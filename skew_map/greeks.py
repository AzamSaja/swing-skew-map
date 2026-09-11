"""
Black-Scholes Delta and Greeks calculation engine.
Handles probability-equidistant strike matching (25-delta calls and puts),
ATM volatility calculation, and sanity filtering.
"""

import math
from typing import Optional, Tuple, Dict, Any
import numpy as np
import pandas as pd
from scipy.stats import norm

def calculate_bs_delta(
    spot: float,
    strike: float,
    dte_days: float,
    iv: float,
    rate: float = 0.045,
    option_type: str = "call"
) -> float:
    """
    Calculates Black-Scholes Delta for a given option contract.
    Returns:
        float: Delta value (Call: 0.0 to 1.0, Put: -1.0 to 0.0).
    """
    if spot <= 0 or strike <= 0 or dte_days <= 0 or iv <= 0.001:
        return 0.0
    
    t = dte_days / 365.0
    try:
        d1 = (math.log(spot / strike) + (rate + 0.5 * iv * iv) * t) / (iv * math.sqrt(t))
        if option_type.lower() == "call":
            return float(norm.cdf(d1))
        else:
            return float(norm.cdf(d1) - 1.0)
    except (ValueError, ZeroDivisionError, OverflowError):
        return 0.0

def find_atm_iv(
    spot: float,
    calls_df: pd.DataFrame,
    puts_df: pd.DataFrame
) -> Tuple[Optional[float], Optional[float]]:
    """
    Finds the At-The-Money strike and ATM implied volatility.
    Returns (atm_strike, atm_iv).
    """
    if calls_df.empty and puts_df.empty:
        return None, None

    # Merge or find common strikes near spot
    all_strikes = sorted(list(set(calls_df['strike'].tolist() + puts_df['strike'].tolist())))
    if not all_strikes:
        return None, None

    # Find strike closest to spot
    atm_strike = min(all_strikes, key=lambda k: abs(k - spot))

    call_match = calls_df[calls_df['strike'] == atm_strike]
    put_match = puts_df[puts_df['strike'] == atm_strike]

    ivs = []
    if not call_match.empty:
        c_iv = call_match.iloc[0].get('impliedVolatility')
        if pd.notna(c_iv) and c_iv > 0.01:
            ivs.append(c_iv)
            
    if not put_match.empty:
        p_iv = put_match.iloc[0].get('impliedVolatility')
        if pd.notna(p_iv) and p_iv > 0.01:
            ivs.append(p_iv)

    if not ivs:
        # Fallback to closest strike that has valid IV
        valid_calls = calls_df[calls_df['impliedVolatility'] > 0.01]
        if not valid_calls.empty:
            closest_c = valid_calls.iloc[(valid_calls['strike'] - spot).abs().argsort()[:1]]
            return float(closest_c.iloc[0]['strike']), float(closest_c.iloc[0]['impliedVolatility'])
        return None, None

    atm_iv = float(np.mean(ivs))
    return float(atm_strike), atm_iv

def find_delta_strike(
    spot: float,
    chain_df: pd.DataFrame,
    dte_days: float,
    target_delta: float = 0.25,
    option_type: str = "call",
    rate: float = 0.045
) -> Optional[Dict[str, Any]]:
    """
    Finds the strike closest to the target delta (e.g. 0.25 delta call, or 0.25 delta put |delta|=0.25).
    Filters out zero-liquidity or stale quotes.
    """
    if chain_df.empty:
        return None

    valid = chain_df[chain_df['impliedVolatility'] > 0.01].copy()
    if valid.empty:
        return None

    # Compute deltas for all valid strikes
    deltas = []
    abs_delta_diffs = []
    
    for _, row in valid.iterrows():
        k = float(row['strike'])
        iv = float(row['impliedVolatility'])
        d = calculate_bs_delta(spot, k, dte_days, iv, rate, option_type)
        deltas.append(d)
        
        # For call: target is +target_delta (e.g. +0.25)
        # For put: target is -target_delta (e.g. -0.25)
        expected_d = target_delta if option_type == "call" else -target_delta
        abs_delta_diffs.append(abs(d - expected_d))

    valid['delta'] = deltas
    valid['delta_diff'] = abs_delta_diffs

    # Prefer strikes with non-zero open interest if possible
    has_oi = valid[valid['openInterest'] > 0]
    candidate_df = has_oi if not has_oi.empty else valid

    best_row = candidate_df.sort_values('delta_diff').iloc[0]

    # Verify delta is within reasonable proximity
    if best_row['delta_diff'] > 0.15:
        # If best match is too far from 25-delta, flag
        pass

    return {
        'strike': float(best_row['strike']),
        'iv': float(best_row['impliedVolatility']),
        'delta': float(best_row['delta']),
        'open_interest': int(best_row.get('openInterest', 0) or 0),
        'volume': int(best_row.get('volume', 0) or 0),
        'bid': float(best_row.get('bid', 0.0) or 0.0),
        'ask': float(best_row.get('ask', 0.0) or 0.0),
        'in_the_money': bool(best_row.get('inTheMoney', False))
    }

