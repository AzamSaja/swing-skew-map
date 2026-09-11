"""
Command-line interface for the Options Skew Map.
Supports running live scans, generating terminal reports, exporting CSVs,
and launching the interactive Web Dashboard.
"""

import argparse
import sys
import json
from pathlib import Path
import pandas as pd

# Fix Windows console utf-8 printing
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from skew_map.pipeline import run_skew_scan, load_universe_config
from skew_map.storage import list_snapshots, load_snapshot, get_latest_prior_snapshot

def format_terminal_report(results: dict):
    print("=" * 80)
    print(f"       OPTIONS SKEW MAP — DAILY BRIEFING ({results.get('scan_date', 'TODAY')})")
    print("=" * 80)
    
    # KPI Strip
    mh = results.get("most_hedged_sector")
    mcb = results.get("most_call_bid_sector")
    print(f"\n[KPI STRIP]")
    print(f"* Total Scanned: {results.get('total_count')} names | Valid Chains: {results.get('valid_count')} names")
    if mh:
        print(f"* Most-Hedged Sector: {mh['sector']} ({mh['avg_vol_points']:+.2f} vol pts, {mh['agreement_pct']}% agreement)")
    if mcb:
        print(f"* Most Upside-Bid Sector: {mcb['sector']} ({mcb['avg_vol_points']:+.2f} vol pts, {mcb['agreement_pct']}% agreement)")
    print(f"* Market Median Vol Points: {results.get('market_median_vol_points', 0.0):+.2f} pts")

    # Benchmarks
    idx_ref = results.get("index_references", {})
    if idx_ref:
        idx_strs = [f"{s}: {d.get('vol_points', 0.0):+.1f} pts" for s, d in idx_ref.items()]
        print(f"* Benchmark Vol Points: {' | '.join(idx_strs)}")

    # Today's Read
    tr = results.get("todays_read", {})
    print(f"\n[TODAY'S READ]")
    for p in tr.get("paragraphs", []):
        print(f"  > {p}\n")

    # Action Board
    ab = results.get("action_board", {})
    print("-" * 80)
    print("ACTION BOARD SUMMARY")
    print("-" * 80)

    for bucket_key, bucket_title in [
        ("contrarian_bids", "🔵 CONTRARIAN BIDS (FRESH LOOK / WATCHLIST)"),
        ("chase", "🟠 CHASE / CROWDED (MOMENTUM / LATE)"),
        ("hedged_rally", "🟡 HEDGED RALLY (TIGHTEN STOPS)"),
        ("fear", "🔴 FEAR (LEAVE ALONE)")
    ]:
        items = ab.get(bucket_key, [])
        print(f"\n{bucket_title} [{len(items)} names]:")
        if not items:
            print("  (None)")
            continue
        for it in items[:6]:
            d_str = it.get("delta_skew_str", "—")
            cat_flag = " [EARNINGS!]" if it.get("has_catalyst") else ""
            print(f"  * {it['symbol']:<5} | 1M: {it['return_1m']:+6.1f}% (vs SPY: {it['return_1m_vs_spy']:+5.1f}%) | "
                  f"Skew: {it['skew']:+6.3f} (Δ: {d_str}) | VolPts: {it['vol_points']:+5.1f} | RVOL: {it['rvol']:4.2f}x{cat_flag}")

    print("\n" + "=" * 80)

def export_to_csv(results: dict, output_path: str):
    rows = results.get("rows", [])
    if not rows:
        print("No rows to export.")
        return

    export_records = []
    for r in rows:
        export_records.append({
            "Ticker": r.get("symbol"),
            "Sector": r.get("sector"),
            "Spot": r.get("spot"),
            "ATM_IV_%": r.get("atm_iv"),
            "Put_25d_IV_%": r.get("put_iv"),
            "Put_Delta": r.get("put_delta"),
            "Call_25d_IV_%": r.get("call_iv"),
            "Call_Delta": r.get("call_delta"),
            "Skew_Normalized": r.get("skew"),
            "Vol_Points": r.get("vol_points"),
            "Return_1M_%": r.get("return_1m"),
            "Return_1M_vs_SPY_%": r.get("return_1m_vs_spy"),
            "RVOL": r.get("rvol"),
            "Earnings_Date": r.get("earnings_date"),
            "Event_Premium_Catalyst": r.get("has_catalyst"),
            "Chain_OK": r.get("chain_ok"),
            "Sector_Rank": r.get("sector_rank_str"),
            "Delta_vs_Prior_Week": r.get("delta_skew_str"),
            "Quadrant_1M": r.get("quadrant_1m", {}).get("quadrant") if r.get("quadrant_1m") else "UNCLASSIFIED",
            "Action": r.get("quadrant_1m", {}).get("action") if r.get("quadrant_1m") else "IGNORE",
            "Readout_Sentence": r.get("sentence_readout")
        })

    df = pd.DataFrame(export_records)
    df.to_csv(output_path, index=False)
    print(f"Successfully exported {len(df)} records to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Options Skew Map CLI")
    subparsers = parser.add_subparsers(dest="command")

    # scan
    scan_parser = subparsers.add_parser("scan", help="Run a skew map scan")
    scan_parser.add_argument("--market", type=str, default="US", choices=["US", "IDX", "us", "idx"], help="Market universe: US or IDX")
    scan_parser.add_argument("--tickers", type=str, help="Comma-separated list of tickers (optional)")
    scan_parser.add_argument("--no-save", action="store_true", help="Do not save snapshot to disk")
    scan_parser.add_argument("--threads", type=int, default=8, help="Number of concurrent download threads")

    # report
    report_parser = subparsers.add_parser("report", help="Print terminal report from latest snapshot or live scan")
    report_parser.add_argument("--market", type=str, default="US", choices=["US", "IDX", "us", "idx"], help="Market universe")
    report_parser.add_argument("--date", type=str, help="Snapshot date (YYYY-MM-DD), defaults to latest")

    # export-csv
    export_parser = subparsers.add_parser("export-csv", help="Export latest scan to CSV")
    export_parser.add_argument("output", type=str, help="Destination CSV file path")
    export_parser.add_argument("--market", type=str, default="US", choices=["US", "IDX", "us", "idx"], help="Market universe")

    # serve
    serve_parser = subparsers.add_parser("serve", help="Launch interactive Web Dashboard")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to run web server on")
    serve_parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address")

    args = parser.parse_args()

    if args.command == "scan":
        m = args.market.upper()
        custom_symbols = [s.strip().upper() for s in args.tickers.split(",")] if args.tickers else None
        print(f"Starting {m} scan for {len(custom_symbols) if custom_symbols else m + ' universe'} tickers...")
        res = run_skew_scan(symbols=custom_symbols, save_to_disk=not args.no_save, max_workers=args.threads, market=m)
        format_terminal_report(res)

    elif args.command == "report":
        m = args.market.upper()
        snaps = list_snapshots(market=m)
        target_date = args.date or (snaps[0] if snaps else None)
        if not target_date:
            print(f"No {m} snapshots found. Running live scan...")
            res = run_skew_scan(market=m)
        else:
            print(f"Loading {m} snapshot: {target_date}")
            res = load_snapshot(target_date)
            if not res:
                print(f"Snapshot not found for date {target_date}")
                sys.exit(1)
        format_terminal_report(res)

    elif args.command == "export-csv":
        m = args.market.upper()
        snaps = list_snapshots(market=m)
        if not snaps:
            print(f"No {m} snapshot found to export. Run 'python cli.py scan --market {m}' first.")
            sys.exit(1)
        res = load_snapshot(snaps[0])
        export_to_csv(res, args.output)

    elif args.command == "serve":
        import uvicorn
        print(f"Starting Skew Map Web Dashboard at http://{args.host}:{args.port}")
        uvicorn.run("web.app:app", host=args.host, port=args.port, reload=True)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
