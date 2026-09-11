"""
Snapshot storage and historical change tracking (Decision #7).
Enables computing Delta vs Last Week (Δ Skew) and detecting quadrant flips.
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from .config import SNAPSHOT_DIR

def get_snapshot_path(date_str: Optional[str] = None, market: str = "US") -> Path:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    d_str = date_str or date.today().isoformat()
    suffix = "_idx" if market.upper() == "IDX" and not d_str.endswith("_idx") else ""
    return SNAPSHOT_DIR / f"{d_str}{suffix}.json"

def save_snapshot(results: Dict[str, Any], date_str: Optional[str] = None, market: str = "US") -> Path:
    """
    Saves a completed scan to data/snapshots/YYYY-MM-DD[_idx].json.
    """
    m = results.get("market") or market.upper()
    p = get_snapshot_path(date_str, market=m)
    clean_data = {
        "timestamp": datetime.now().isoformat(),
        "date": date_str or date.today().isoformat(),
        "scan_date": results.get("scan_date") or date_str or date.today().isoformat(),
        "market": m,
        "benchmark_symbol": results.get("benchmark_symbol", "^JKSE" if m == "IDX" else "SPY"),
        "valid_count": results.get("valid_count", 0),
        "total_count": results.get("total_count", 0),
        "market_median_vol_points": results.get("market_median_vol_points", 0.0),
        "most_hedged_sector": results.get("most_hedged_sector"),
        "most_call_bid_sector": results.get("most_call_bid_sector"),
        "caution_flags": results.get("caution_flags", []),
        "sector_summaries": results.get("sector_summaries", {}),
        "index_references": results.get("index_references", {}),
        "action_board": results.get("action_board", {}),
        "todays_read": results.get("todays_read", {}),
        "rows": results.get("rows", [])
    }
    with open(p, "w", encoding="utf-8") as f:
        json.dump(clean_data, f, indent=2)
    return p

def list_snapshots(market: Optional[str] = None) -> List[str]:
    """
    Returns sorted list of available snapshot dates (newest first).
    """
    if not SNAPSHOT_DIR.exists():
        return []
    files = sorted(SNAPSHOT_DIR.glob("*.json"), reverse=True)
    stems = [f.stem for f in files]
    if market:
        if market.upper() == "IDX":
            return [s for s in stems if s.endswith("_idx")]
        else:
            return [s for s in stems if not s.endswith("_idx")]
    return stems

def load_snapshot(date_str: str) -> Optional[Dict[str, Any]]:
    """
    Loads snapshot for given date string (YYYY-MM-DD or YYYY-MM-DD_idx).
    Reconstructs action_board and todays_read if missing from older format.
    """
    p = SNAPSHOT_DIR / f"{date_str}.json"
    if not p.exists():
        # Try with or without _idx
        if date_str.endswith("_idx"):
            p = SNAPSHOT_DIR / f"{date_str[:-4]}.json"
        else:
            p = SNAPSHOT_DIR / f"{date_str}_idx.json"
        if not p.exists():
            return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not data.get("market"):
            data["market"] = "IDX" if "_idx" in p.stem else "US"
        if not data.get("benchmark_symbol"):
            data["benchmark_symbol"] = "^JKSE" if data["market"] == "IDX" else "SPY"
            
        rows = data.get("rows", [])
        if "action_board" not in data or not data["action_board"]:
            valid_rows = [r for r in rows if r.get("chain_ok") and r.get("skew") is not None]
            data["action_board"] = {
                "contrarian_bids": [r for r in valid_rows if r.get("quadrant_1m", {}).get("code") == "contrarian_bid"],
                "chase": [r for r in valid_rows if r.get("quadrant_1m", {}).get("code") == "chase"],
                "hedged_rally": [r for r in valid_rows if r.get("quadrant_1m", {}).get("code") == "hedged_rally"],
                "fear": [r for r in valid_rows if r.get("quadrant_1m", {}).get("code") == "fear"],
            }
        if "todays_read" not in data or not data["todays_read"]:
            from .narrative import generate_todays_read
            data["todays_read"] = generate_todays_read(data)
            
        return data
    except Exception:
        return None

def get_latest_prior_snapshot(current_date_str: Optional[str] = None, market: str = "US") -> Optional[Dict[str, Any]]:
    """
    Finds the most recent snapshot older than current_date_str for the market.
    """
    snaps = list_snapshots(market=market)
    c_date = current_date_str or date.today().isoformat()
    for s_date in snaps:
        clean_s = s_date.replace("_idx", "")
        clean_c = c_date.replace("_idx", "")
        if clean_s < clean_c:
            return load_snapshot(s_date)
    return None

def apply_snapshot_deltas(
    current_rows: List[Dict[str, Any]],
    prior_snapshot: Optional[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Compares current rows with prior snapshot to compute Delta vs Last Week.
    Adds 'delta_skew', 'delta_skew_str', 'prior_quadrant', and 'is_flipped'.
    """
    if not prior_snapshot or "rows" not in prior_snapshot:
        for r in current_rows:
            r["delta_skew"] = None
            r["delta_skew_str"] = "—"
            r["prior_quadrant"] = None
            r["is_flipped"] = False
        return current_rows

    prior_map = {p["symbol"]: p for p in prior_snapshot["rows"]}

    for r in current_rows:
        sym = r["symbol"]
        prior = prior_map.get(sym)
        
        if prior and prior.get("skew") is not None and r.get("skew") is not None:
            c_skew = float(r["skew"])
            p_skew = float(prior["skew"])
            diff = round(c_skew - p_skew, 4)
            r["delta_skew"] = diff
            r["delta_skew_str"] = f"{diff:+.4f}" if diff != 0 else "0.0000"
            
            p_quad = prior.get("quadrant_1m", {}).get("quadrant")
            c_quad = r.get("quadrant_1m", {}).get("quadrant")
            r["prior_quadrant"] = p_quad
            r["is_flipped"] = (p_quad and c_quad and p_quad != c_quad)
        else:
            r["delta_skew"] = None
            r["delta_skew_str"] = "—"
            r["prior_quadrant"] = None
            r["is_flipped"] = False

    return current_rows
