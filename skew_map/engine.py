"""
Core calculation engine: Skew formulas, sanity ceilings,
4-quadrant assignment, sector agreement metrics, and intra-sector ranking.
"""

from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd

from .config import SkewConfig, DEFAULT_CONFIG
from .greeks import find_atm_iv, find_delta_strike

def classify_quadrant(return_val: float, skew_val: float) -> Dict[str, str]:
    """
    Classifies a stock into one of the 4 quadrants based on price return and skew.
    """
    if return_val < 0 and skew_val < 0:
        return {
            "quadrant": "CONTRARIAN BID",
            "code": "contrarian_bid",
            "badge": "🔵 CONTRARIAN BID",
            "color": "#3b82f6",  # Blue
            "action": "Watchlist",
            "verdict": "FRESH LOOK",
            "meaning": "Price is falling while calls are bid. Tape and options disagree."
        }
    elif return_val >= 0 and skew_val < 0:
        return {
            "quadrant": "CHASE",
            "code": "chase",
            "badge": "🟠 CHASE",
            "color": "#f97316",  # Orange
            "action": "Crowded / Late",
            "verdict": "MOMENTUM",
            "meaning": "Price is up and calls are bid. Everyone agrees, late entry."
        }
    elif return_val >= 0 and skew_val >= 0:
        return {
            "quadrant": "HEDGED RALLY",
            "code": "hedged_rally",
            "badge": "🟡 HEDGED RALLY",
            "color": "#eab308",  # Yellow
            "action": "Tighten Stops",
            "verdict": "TIGHTEN",
            "meaning": "Price is rising but protection is being bought underneath. Rally unconfirmed."
        }
    else:  # return_val < 0 and skew_val >= 0
        return {
            "quadrant": "FEAR",
            "code": "fear",
            "badge": "🔴 FEAR",
            "color": "#ef4444",  # Red
            "action": "Leave Alone",
            "verdict": "LEAVE IT",
            "meaning": "Falling and protection is getting more expensive. Not a bargain yet."
        }

def analyze_ticker_options(
    raw_data: Dict[str, Any],
    spy_1m_return: float = 0.0,
    config: SkewConfig = DEFAULT_CONFIG
) -> Dict[str, Any]:
    """
    Computes ATM IV, 25-delta strikes, normalized Skew, raw Vol Points,
    and applies sanity ceiling checks (Trap #4) and quality checks (Decision #5).
    """
    symbol = raw_data["symbol"]
    spot = raw_data["spot"]
    ret_1d = raw_data.get("return_1d", 0.0)
    ret_1w = raw_data.get("return_1w", 0.0)
    ret_1m = raw_data.get("return_1m", 0.0)
    ret_1m_vs_spy = round(ret_1m - spy_1m_return, 2)
    rvol = raw_data.get("rvol", 1.0)
    earnings_date = raw_data.get("earnings_date")
    has_catalyst = raw_data.get("has_catalyst", False)

    base_result = {
        "symbol": symbol,
        "spot": round(spot, 2),
        "return_1d": round(ret_1d, 2),
        "return_1w": round(ret_1w, 2),
        "return_1m": round(ret_1m, 2),
        "return_1m_vs_spy": ret_1m_vs_spy,
        "rvol": rvol,
        "earnings_date": earnings_date or "N/A",
        "has_catalyst": has_catalyst,
        "target_expiry": raw_data.get("target_expiry", "N/A"),
        "dte": raw_data.get("dte", 0),
        "atm_strike": None,
        "atm_iv": None,
        "put_strike": None,
        "put_iv": None,
        "put_delta": None,
        "call_strike": None,
        "call_iv": None,
        "call_delta": None,
        "skew": None,             # normalized
        "vol_points": None,       # raw vol points
        "chain_ok": False,
        "rejection_reason": None,
        "quadrant_1m": None,
        "quadrant_1w": None,
        "quadrant_1d": None,
    }

    if raw_data.get("is_realized_model"):
        atm_iv = raw_data.get("atm_iv", 0.20)
        put_iv = raw_data.get("put_iv", 0.20)
        call_iv = raw_data.get("call_iv", 0.20)
        raw_vol_diff = put_iv - call_iv
        vol_points = round(raw_vol_diff * 100.0, 2)
        skew_normalized = round(raw_vol_diff / atm_iv, 4) if atm_iv > 0 else 0.0

        q_1m = classify_quadrant(ret_1m, skew_normalized)
        q_1w = classify_quadrant(ret_1w, skew_normalized)
        q_1d = classify_quadrant(ret_1d, skew_normalized)

        base_result.update({
            "is_realized_model": True,
            "atm_strike": raw_data.get("atm_strike"),
            "atm_iv": round(atm_iv * 100.0, 2),
            "put_strike": raw_data.get("put_strike"),
            "put_iv": round(put_iv * 100.0, 2),
            "put_delta": -0.25,
            "call_strike": raw_data.get("call_strike"),
            "call_iv": round(call_iv * 100.0, 2),
            "call_delta": 0.25,
            "skew": skew_normalized,
            "vol_points": vol_points,
            "chain_ok": True,
            "rejection_reason": None,
            "quadrant_1m": q_1m,
            "quadrant_1w": q_1w,
            "quadrant_1d": q_1d,
        })
        return base_result

    if not raw_data.get("has_options") or not raw_data.get("chain_ok"):
        base_result["rejection_reason"] = raw_data.get("error", "No valid options chain")
        return base_result

    calls_df = raw_data.get("calls_df")
    puts_df = raw_data.get("puts_df")
    dte = raw_data.get("dte", 30)

    # 1. ATM IV
    atm_strike, atm_iv = find_atm_iv(spot, calls_df, puts_df)
    if atm_iv is None or atm_iv < config.min_atm_iv or atm_iv > config.max_atm_iv:
        base_result["rejection_reason"] = f"Unrealistic ATM IV: {atm_iv}"
        return base_result

    # 2. 25-Delta strikes
    call_info = find_delta_strike(spot, calls_df, dte, target_delta=config.target_delta, option_type="call", rate=config.risk_free_rate)
    put_info = find_delta_strike(spot, puts_df, dte, target_delta=config.target_delta, option_type="put", rate=config.risk_free_rate)

    if not call_info or not put_info:
        base_result["rejection_reason"] = "Could not identify 25-delta strikes"
        return base_result

    # 3. Quality checks (Decision #5)
    # Check open interest
    oi_ok = (call_info["open_interest"] >= config.min_open_interest and put_info["open_interest"] >= config.min_open_interest)

    put_iv = put_info["iv"]
    call_iv = call_info["iv"]

    # 4. Skew calculations (Decision #3)
    raw_vol_diff = put_iv - call_iv
    vol_points = round(raw_vol_diff * 100.0, 2)
    skew_normalized = round(raw_vol_diff / atm_iv, 4)

    # 5. Sanity ceiling (Trap #4 / Decision #6)
    is_sanity_exceeded = (
        abs(skew_normalized) > config.max_abs_normalized_skew or
        abs(vol_points) > config.max_abs_vol_points or
        put_iv <= 0.01 or call_iv <= 0.01
    )

    if is_sanity_exceeded:
        base_result["chain_ok"] = False
        base_result["rejection_reason"] = f"Exceeded sanity ceiling: Skew={skew_normalized}, VolPts={vol_points}"
        base_result["skew"] = skew_normalized
        base_result["vol_points"] = vol_points
        base_result["atm_iv"] = round(atm_iv * 100.0, 2)
        base_result["atm_strike"] = atm_strike
        base_result["put_strike"] = put_info["strike"]
        base_result["put_iv"] = round(put_iv * 100.0, 2)
        base_result["put_delta"] = round(put_info["delta"], 2)
        base_result["call_strike"] = call_info["strike"]
        base_result["call_iv"] = round(call_iv * 100.0, 2)
        base_result["call_delta"] = round(call_info["delta"], 2)
        return base_result

    chain_ok = oi_ok and (not is_sanity_exceeded)

    # 6. Quadrant classification
    q_1m = classify_quadrant(ret_1m, skew_normalized)
    q_1w = classify_quadrant(ret_1w, skew_normalized)
    q_1d = classify_quadrant(ret_1d, skew_normalized)

    base_result.update({
        "atm_strike": atm_strike,
        "atm_iv": round(atm_iv * 100.0, 2),
        "put_strike": put_info["strike"],
        "put_iv": round(put_iv * 100.0, 2),
        "put_delta": round(put_info["delta"], 2),
        "call_strike": call_info["strike"],
        "call_iv": round(call_iv * 100.0, 2),
        "call_delta": round(call_info["delta"], 2),
        "skew": skew_normalized,
        "vol_points": vol_points,
        "chain_ok": chain_ok,
        "rejection_reason": "Low Open Interest" if not oi_ok else None,
        "quadrant_1m": q_1m,
        "quadrant_1w": q_1w,
        "quadrant_1d": q_1d,
    })

    return base_result

def process_universe(
    ticker_data_list: List[Dict[str, Any]],
    sector_map: Dict[str, str],
    watchlist_set: set,
    spy_1m_return: float = 0.0,
    config: SkewConfig = DEFAULT_CONFIG
) -> Dict[str, Any]:
    """
    Processes full universe, runs intra-sector ranking, computes Trap #2 cross-sector
    vol points, evaluates Trap #3 sector agreement, and builds Action Board buckets.
    """
    analyzed_rows = []
    
    for raw in ticker_data_list:
        sym = raw["symbol"]
        analysis = analyze_ticker_options(raw, spy_1m_return=spy_1m_return, config=config)
        analysis["sector"] = sector_map.get(sym, "Other")
        analysis["is_watchlist"] = sym in watchlist_set
        analyzed_rows.append(analysis)

    # Group by Sector for Intra-Sector Ranking & Trap #3 Sector Agreement
    valid_rows = [r for r in analyzed_rows if r["chain_ok"] and r["skew"] is not None]
    
    # Intra-sector ranking (percentile rank within sector)
    sector_groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in valid_rows:
        sec = r["sector"]
        sector_groups.setdefault(sec, []).append(r)

    for sec, rows in sector_groups.items():
        # Sort by skew ascending
        sorted_rows = sorted(rows, key=lambda x: x["skew"])
        n = len(sorted_rows)
        for rank_idx, r in enumerate(sorted_rows):
            # Percentile: 0% = most call-bid, 100% = most put-bid
            pct = round((rank_idx / max(1, n - 1)) * 100) if n > 1 else 50
            r["sector_rank_pct"] = pct
            r["sector_rank_str"] = f"{pct}%"

    # Default for rows not ranked
    for r in analyzed_rows:
        if "sector_rank_pct" not in r:
            r["sector_rank_pct"] = 50
            r["sector_rank_str"] = "N/A"

    # Compute Sector Metrics (Trap #2: Vol points, Trap #3: Agreement)
    sector_summaries = {}
    for sec, rows in sector_groups.items():
        if not rows:
            continue
        v_pts = [r["vol_points"] for r in rows]
        skews = [r["skew"] for r in rows]
        
        avg_vol_pts = round(float(np.mean(v_pts)), 2)
        med_vol_pts = round(float(np.median(v_pts)), 2)
        avg_skew = round(float(np.mean(skews)), 4)

        # Agreement: share of names leaning the same direction (puts bid > 0 vs calls bid < 0)
        puts_bid_count = sum(1 for s in skews if s > 0)
        calls_bid_count = sum(1 for s in skews if s < 0)
        total_sec = len(skews)

        if puts_bid_count >= calls_bid_count:
            lean = "Puts Bid (Fear/Hedging)"
            agreement = round(puts_bid_count / total_sec, 2)
        else:
            lean = "Calls Bid (Upside Bid)"
            agreement = round(calls_bid_count / total_sec, 2)

        has_caveat = (agreement < config.sector_agreement_threshold) and (total_sec >= 2)
        caveat_msg = f"Low consensus ({int(agreement*100)}%): Sector average dragged by split sentiment." if has_caveat else None

        sector_summaries[sec] = {
            "sector": sec,
            "count": total_sec,
            "avg_vol_points": avg_vol_pts,
            "median_vol_points": med_vol_pts,
            "avg_skew": avg_skew,
            "lean": lean,
            "agreement": agreement,
            "agreement_pct": int(agreement * 100),
            "has_caveat": has_caveat,
            "caveat_message": caveat_msg
        }

    # Action Board buckets
    action_board = {
        "contrarian_bids": [r for r in valid_rows if r["quadrant_1m"]["code"] == "contrarian_bid"],
        "chase": [r for r in valid_rows if r["quadrant_1m"]["code"] == "chase"],
        "hedged_rally": [r for r in valid_rows if r["quadrant_1m"]["code"] == "hedged_rally"],
        "fear": [r for r in valid_rows if r["quadrant_1m"]["code"] == "fear"],
    }

    # Sort each action bucket
    # Contrarian Bids: sort by most call-bid (skew ascending)
    action_board["contrarian_bids"].sort(key=lambda x: x["skew"])
    # Chase: sort by 1M return descending
    action_board["chase"].sort(key=lambda x: x["return_1m"], reverse=True)
    # Hedged Rally: sort by most put-bid (skew descending)
    action_board["hedged_rally"].sort(key=lambda x: x["skew"], reverse=True)
    # Fear: sort by 1M return ascending (worst performers)
    action_board["fear"].sort(key=lambda x: x["return_1m"])

    # High-level Market Metrics
    all_valid_vol_pts = [r["vol_points"] for r in valid_rows]
    market_median_vol_pts = round(float(np.median(all_valid_vol_pts)), 2) if all_valid_vol_pts else 0.0

    sorted_sectors = sorted(sector_summaries.values(), key=lambda x: x["avg_vol_points"], reverse=True)
    most_hedged_sector = sorted_sectors[0] if sorted_sectors else None
    most_call_bid_sector = sorted_sectors[-1] if sorted_sectors else None

    # Caution flags: rallying stocks with heavy put skew
    caution_flags = [
        r for r in valid_rows
        if r["return_1m"] > 3.0 and r["skew"] > 0.08
    ]

    return {
        "rows": analyzed_rows,
        "valid_count": len(valid_rows),
        "total_count": len(analyzed_rows),
        "sector_summaries": sector_summaries,
        "action_board": action_board,
        "market_median_vol_points": market_median_vol_pts,
        "most_hedged_sector": most_hedged_sector,
        "most_call_bid_sector": most_call_bid_sector,
        "caution_flags": caution_flags
    }

