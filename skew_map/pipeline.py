"""
Pipeline orchestrator: Parallel data fetching, calculation,
delta comparison, narrative building, and snapshot persistence.
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from typing import Dict, List, Any, Optional
import logging

from .config import SkewConfig, DEFAULT_CONFIG, DEFAULT_UNIVERSE_PATH, DEFAULT_IDX_UNIVERSE_PATH
from .data_fetcher import fetch_ticker_data
from .engine import process_universe
from .narrative import generate_row_sentence, generate_todays_read
from .storage import save_snapshot, get_latest_prior_snapshot, apply_snapshot_deltas

logger = logging.getLogger(__name__)

def load_universe_config(market: str = "US", path=None) -> Dict[str, Any]:
    target_path = path or (DEFAULT_IDX_UNIVERSE_PATH if market.upper() == "IDX" else DEFAULT_UNIVERSE_PATH)
    with open(target_path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_skew_scan(
    symbols: Optional[List[str]] = None,
    sector_mapping: Optional[Dict[str, str]] = None,
    watchlist: Optional[List[str]] = None,
    save_to_disk: bool = True,
    max_workers: int = 10,
    market: str = "US",
    config: Optional[SkewConfig] = None
) -> Dict[str, Any]:
    """
    Executes a complete Options / Volatility Skew Map scan across US or IDX universe.
    """
    if config is None:
        config = SkewConfig(market=market.upper())
    else:
        config.market = market.upper()

    is_idx = (config.market == "IDX")

    # 1. Load universe if not provided
    if symbols is None or sector_mapping is None:
        u_cfg = load_universe_config(market=config.market)
        sector_mapping = {}
        all_syms = []
        for sec, t_list in u_cfg["sectors"].items():
            for t in t_list:
                sector_mapping[t] = sec
                all_syms.append(t)
        symbols = symbols or list(set(all_syms))
        watchlist = watchlist or u_cfg.get("watchlist", [])

    watchlist_set = set(watchlist or [])

    # 2. Benchmarks (SPY, QQQ, IWM for US; ^JKSE for IDX)
    bench_syms = ["^JKSE"] if is_idx else config.index_symbols
    logger.info(f"Fetching benchmarks for {config.market}: {bench_syms}...")
    benchmarks_data = {}
    with ThreadPoolExecutor(max_workers=max(1, len(bench_syms))) as executor:
        f_map = {executor.submit(fetch_ticker_data, sym, config): sym for sym in bench_syms}
        for fut in as_completed(f_map):
            sym = f_map[fut]
            try:
                res = fut.result()
                if res:
                    benchmarks_data[sym] = res
            except Exception as e:
                logger.error(f"Failed benchmark fetch {sym}: {e}")

    primary_bench = "^JKSE" if is_idx else "SPY"
    bench_1m_return = 0.0
    if primary_bench in benchmarks_data:
        bench_1m_return = benchmarks_data[primary_bench].get("return_1m", 0.0)

    # 3. Fetch Universe in parallel
    logger.info(f"Fetching {len(symbols)} tickers with {max_workers} threads...")
    raw_results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        f_map = {executor.submit(fetch_ticker_data, sym, config): sym for sym in symbols}
        for fut in as_completed(f_map):
            try:
                res = fut.result()
                if res:
                    raw_results.append(res)
            except Exception as e:
                logger.error(f"Error fetching ticker: {e}")

    # 4. Engine Processing
    results = process_universe(
        ticker_data_list=raw_results,
        sector_map=sector_mapping,
        watchlist_set=watchlist_set,
        spy_1m_return=bench_1m_return,
        config=config
    )

    # 5. Add Index Benchmark Vol Points for the Sector Comparison Chart (Trap #2 reference lines)
    index_references = {}
    for idx_sym, idx_data in benchmarks_data.items():
        from .engine import analyze_ticker_options
        idx_analyzed = analyze_ticker_options(idx_data, spy_1m_return=bench_1m_return, config=config)
        index_references[idx_sym] = {
            "symbol": idx_sym,
            "vol_points": idx_analyzed.get("vol_points"),
            "skew": idx_analyzed.get("skew"),
            "return_1m": idx_analyzed.get("return_1m")
        }
    results["index_references"] = index_references
    results["market"] = config.market
    results["benchmark_symbol"] = primary_bench

    # 6. Apply Historical Deltas vs Prior Week / Prior Snapshot (Decision #7)
    prior_snap = get_latest_prior_snapshot(market=config.market)
    results["rows"] = apply_snapshot_deltas(results["rows"], prior_snap)
    results["has_prior_snapshot"] = prior_snap is not None
    results["prior_snapshot_date"] = prior_snap.get("date") if prior_snap else None

    # 7. Generate Row Sentences and Today's Read
    for r in results["rows"]:
        r["sentence_readout"] = generate_row_sentence(r)

    todays_read = generate_todays_read(results)
    results["todays_read"] = todays_read
    results["scan_date"] = date.today().isoformat()

    # 8. Save Snapshot
    if save_to_disk:
        snap_path = save_snapshot(results, market=config.market)
        results["snapshot_file"] = str(snap_path)

    return results

