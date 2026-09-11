"""
Narrative generation engine.
Implements the standardized sentence template from Part 5 ("Reading a row out loud")
and generates the Executive Daily Read ("Today's Read") and KPI strip summaries.
"""

from typing import Dict, Any, List

def generate_row_sentence(row: Dict[str, Any]) -> str:
    """
    Generates the standardized sentence template from Part 5:
    [Ticker] — traders are paying [slightly / clearly / heavily] more for [puts / calls],
    which is more [fear / upside] than [X%] of its sector.
    The stock is [up/down X%] on the month [vs SPY], on [heavy / normal / light] volume.
    That puts it in [quadrant] — [action].
    """
    symbol = row["symbol"]
    skew = row.get("skew")
    chain_ok = row.get("chain_ok", False)
    quadrant_info = row.get("quadrant_1m")

    if not chain_ok or skew is None or not quadrant_info:
        reason = row.get("rejection_reason", "insufficient chain quality")
        return f"{symbol} — option chain does not meet quality bar ({reason}). Left unclassified."

    # 1. Degree: slightly / clearly / heavily
    abs_skew = abs(skew)
    if abs_skew < 0.05:
        degree = "slightly"
    elif abs_skew < 0.15:
        degree = "clearly"
    else:
        degree = "heavily"

    # 2. Side & Sentiment: puts (fear) vs calls (upside)
    is_realized = row.get("is_realized_model", False)
    if skew >= 0:
        side = "puts" if not is_realized else "downside tail vol"
        sentiment_word = "fear"
    else:
        side = "calls" if not is_realized else "upside volatility"
        sentiment_word = "upside"

    # 3. Sector Rank
    sector_pct = row.get("sector_rank_pct", 50)

    # 4. Price Return
    ret_1m = row.get("return_1m", 0.0)
    ret_vs_spy = row.get("return_1m_vs_spy", 0.0)
    is_idx = symbol.endswith(".JK") or row.get("sector") in ["Consumer Non-Cyclicals", "Financials (IDX)"] or is_realized
    bench_label = "IHSG" if is_idx else "SPY"
    
    if ret_1m >= 0:
        price_str = f"up {ret_1m:.1f}% on the month"
    else:
        price_str = f"down {abs(ret_1m):.1f}% on the month"

    vs_spy_str = f" ({'+' if ret_vs_spy >= 0 else ''}{ret_vs_spy:.1f}% vs {bench_label})"

    # 5. Volume Context (RVOL)
    rvol = row.get("rvol", 1.0)
    if rvol >= 1.5:
        vol_str = f"heavy volume ({rvol}x RVOL)"
    elif rvol >= 0.8:
        vol_str = f"normal volume ({rvol}x RVOL)"
    else:
        vol_str = f"light volume ({rvol}x RVOL)"

    # 6. Quadrant & Action
    quad_name = quadrant_info["quadrant"]
    action = quadrant_info["action"]

    sentence = (
        f"{symbol} — traders are paying {degree} more for {side}, which is more {sentiment_word} "
        f"than {sector_pct}% of its sector. The stock is {price_str}{vs_spy_str}, on {vol_str}. "
        f"That puts it in {quad_name} — {action}."
    )

    # Trap #5 Catalyst check
    if row.get("has_catalyst"):
        sentence += (
            f" [CAVEAT: Confirmed earnings on {row.get('earnings_date')} inside expiry window — "
            f"elevated IV is dated event premium, not structural sentiment.]"
        )

    return sentence

def generate_todays_read(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synthesizes the executive daily read and caution flags from the scan results.
    """
    rows = analysis_results.get("rows", [])
    valid_count = analysis_results.get("valid_count", 0)
    total_count = analysis_results.get("total_count", 0)
    sector_summaries = analysis_results.get("sector_summaries", {})
    action_board = analysis_results.get("action_board", {})
    caution_flags = analysis_results.get("caution_flags", [])

    contrarians = action_board.get("contrarian_bids", [])
    chase = action_board.get("chase", [])
    hedged = action_board.get("hedged_rally", [])
    fear = action_board.get("fear", [])

    most_hedged = analysis_results.get("most_hedged_sector")
    most_call_bid = analysis_results.get("most_call_bid_sector")

    paragraphs = []

    # 1. Market Positioning Overview
    market_overview = (
        f"Board active across {valid_count} qualified names ({total_count - valid_count} filtered for thin chains). "
        f"The options market is most hedged in {most_hedged['sector'] if most_hedged else 'N/A'} "
        f"({most_hedged['avg_vol_points'] if most_hedged else 0.0:+.1f} vol pts), "
        f"while upside is most aggressively bid in {most_call_bid['sector'] if most_call_bid else 'N/A'} "
        f"({most_call_bid['avg_vol_points'] if most_call_bid else 0.0:+.1f} vol pts)."
    )
    paragraphs.append(market_overview)

    # 2. Caution Flags (Rallying while puts are bid)
    if caution_flags:
        cf_tickers = [c["symbol"] for c in caution_flags[:4]]
        cf_str = ", ".join(cf_tickers)
        caution_para = (
            f"⚠️ Caution Flag: {cf_str} continue rallying on the month while traders underneath "
            f"are paying heavily for crash protection. A stock extending upward while insurance is bid "
            f"isn't bullish enthusiasm — it is institutional hedging. Recommended action: tighten trailing stops rather than exit."
        )
        paragraphs.append(caution_para)
    else:
        paragraphs.append("No prominent divergence caution flags detected today; rallies are largely unhedged.")

    # 3. Contrarian Bids (Down on the month, but calls bid)
    if contrarians:
        top_cb = contrarians[:3]
        cb_tickers = [c["symbol"] for c in top_cb]
        cb_str = ", ".join(cb_tickers)
        cb_para = (
            f"🔵 Contrarian Bids: {cb_str} have sold off on the month, but call options are actively bid. "
            f"Tape and options positioning disagree here. These enter the swing watchlist for chart level confirmation."
        )
        paragraphs.append(cb_para)
    else:
        paragraphs.append("No clean contrarian bids on the board today; selling pressure is accompanied by put demand.")

    # 4. Sector Caveats (Trap #3)
    low_agreement_sectors = [s for s in sector_summaries.values() if s.get("has_caveat")]
    if low_agreement_sectors:
        sec_names = [f"{s['sector']} ({s['agreement_pct']}% agreement)" for s in low_agreement_sectors]
        caveat_para = (
            f"⚡ Breadth Caveat: Low internal agreement detected in {', '.join(sec_names)}. "
            f"Do not treat these sector averages as unified moves; individual constituent names are sharply split."
        )
        paragraphs.append(caveat_para)

    return {
        "title": "Today's Read",
        "paragraphs": paragraphs,
        "contrarian_count": len(contrarians),
        "chase_count": len(chase),
        "hedged_count": len(hedged),
        "fear_count": len(fear),
        "caution_count": len(caution_flags)
    }

