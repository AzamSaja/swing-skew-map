"""
Data ingestion layer: options chains, historical stock prices,
volume, benchmarks, and earnings catalysts via yfinance.
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
import logging
import pandas as pd
import yfinance as yf
from .config import SkewConfig, DEFAULT_CONFIG

logger = logging.getLogger(__name__)

def select_target_expiry(
    expiries: List[str],
    config: SkewConfig = DEFAULT_CONFIG,
    ref_date: Optional[date] = None
) -> Tuple[Optional[str], int]:
    """
    Applies Decision #2: Expiry selection rule.
    Selects standard monthly contract (3rd Friday) within [min_dte, max_dte].
    Falls back to closest Friday or closest valid expiry if 3rd Friday not listed.
    """
    if not expiries:
        return None, 0

    today = ref_date or date.today()
    candidates = []

    for exp_str in expiries:
        try:
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
            dte = (exp_date - today).days
            if dte < config.min_dte or dte > config.max_dte:
                continue

            is_friday = (exp_date.weekday() == 4)
            is_third_friday = is_friday and (15 <= exp_date.day <= 21)
            
            candidates.append({
                "expiry": exp_str,
                "dte": dte,
                "is_friday": is_friday,
                "is_third_friday": is_third_friday
            })
        except Exception:
            continue

    if not candidates:
        # If no candidates in strict window, take closest expiry >= min_dte
        future_exps = []
        for exp_str in expiries:
            try:
                exp_d = datetime.strptime(exp_str, "%Y-%m-%d").date()
                dte = (exp_d - today).days
                if dte >= 10:
                    future_exps.append((exp_str, dte))
            except Exception:
                continue
        if future_exps:
            future_exps.sort(key=lambda x: x[1])
            return future_exps[0][0], future_exps[0][1]
        return None, 0

    # 1. First priority: 3rd Friday within target range
    third_fridays = [c for c in candidates if c["is_third_friday"]]
    if third_fridays:
        # Pick one closest to 30-35 DTE
        third_fridays.sort(key=lambda x: abs(x["dte"] - 35))
        return third_fridays[0]["expiry"], third_fridays[0]["dte"]

    # 2. Second priority: Any Friday within target range
    fridays = [c for c in candidates if c["is_friday"]]
    if fridays:
        fridays.sort(key=lambda x: abs(x["dte"] - 35))
        return fridays[0]["expiry"], fridays[0]["dte"]

    # 3. Third priority: Any contract in range
    candidates.sort(key=lambda x: abs(x["dte"] - 35))
    return candidates[0]["expiry"], candidates[0]["dte"]

def fetch_ticker_data(
    ticker_symbol: str,
    config: SkewConfig = DEFAULT_CONFIG
) -> Optional[Dict[str, Any]]:
    """
    Fetches stock history, spot price, returns, volume metrics,
    target option chain, and earnings calendar for a single ticker.
    """
    try:
        t = yf.Ticker(ticker_symbol)
        
        # 1. Price History (need at least ~30 trading days for 1M return and 20D volume avg)
        hist = t.history(period="3mo")
        if hist.empty:
            return None
        hist = hist.dropna(subset=['Close'])
        if len(hist) < 5:
            logger.warning(f"Insufficient history for {ticker_symbol}")
            return None

        spot = float(hist['Close'].iloc[-1])
        
        # Returns
        ret_1d = float((spot / hist['Close'].iloc[-2] - 1.0) * 100) if len(hist) >= 2 else 0.0
        ret_1w = float((spot / hist['Close'].iloc[-6] - 1.0) * 100) if len(hist) >= 6 else ret_1d
        ret_1m = float((spot / hist['Close'].iloc[-22] - 1.0) * 100) if len(hist) >= 22 else ret_1w

        # Volume & RVOL
        today_vol = float(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else 0.0
        avg_vol_20 = float(hist['Volume'].iloc[-21:-1].mean()) if len(hist) >= 21 else float(hist['Volume'].mean())
        rvol = round(today_vol / avg_vol_20, 2) if avg_vol_20 > 0 else 1.0

        # 2. Earnings Calendar (Trap #5 check - skip for index ETFs and IDX)
        earnings_date = None
        has_catalyst = False
        is_idx = (config.market == "IDX") or ticker_symbol.endswith(".JK") or (ticker_symbol.startswith("^"))
        if not is_idx and ticker_symbol.upper() not in ["SPY", "QQQ", "IWM", "DIA", "XLF", "XLK", "XLE", "XLV"]:
            try:
                cal = t.calendar
                if isinstance(cal, dict) and 'Earnings Date' in cal:
                    ed_val = cal['Earnings Date']
                    if isinstance(ed_val, list) and len(ed_val) > 0:
                        earnings_date = str(ed_val[0])
                    elif ed_val:
                        earnings_date = str(ed_val)
                elif isinstance(cal, pd.DataFrame) and not cal.empty and 'Earnings Date' in cal.index:
                    earnings_date = str(cal.loc['Earnings Date'].iloc[0])
            except Exception:
                pass

        # 3. Check Options Availability
        options = list(t.options) if not is_idx else []
        
        # If no options listed (or IDX market), apply Realized Volatility Asymmetry Skew Model
        if not options:
            rets = hist['Close'].pct_change().dropna()
            down_rets = rets[rets < 0]
            up_rets = rets[rets > 0]
            
            import numpy as np
            sigma_down = float(np.sqrt(np.mean(down_rets**2)) * np.sqrt(252)) if len(down_rets) > 0 else 0.20
            sigma_up = float(np.sqrt(np.mean(up_rets**2)) * np.sqrt(252)) if len(up_rets) > 0 else 0.20
            sigma_total = float(np.std(rets) * np.sqrt(252)) if len(rets) > 0 else 0.20
            if sigma_total < 0.01:
                sigma_total = 0.20

            return {
                "symbol": ticker_symbol,
                "spot": spot,
                "return_1d": ret_1d,
                "return_1w": ret_1w,
                "return_1m": ret_1m,
                "rvol": rvol,
                "today_volume": today_vol,
                "avg_volume": avg_vol_20,
                "earnings_date": earnings_date or "N/A",
                "has_options": False,
                "is_realized_model": True,
                "target_expiry": "30D Realized Window",
                "dte": 30,
                "atm_iv": sigma_total,
                "put_iv": sigma_down,
                "call_iv": sigma_up,
                "put_strike": round(spot * 0.95, 2),
                "call_strike": round(spot * 1.05, 2),
                "atm_strike": round(spot, 2),
                "chain_ok": True
            }

        target_exp, dte = select_target_expiry(options, config)
        if not target_exp or dte <= 0:
            return {
                "symbol": ticker_symbol,
                "spot": spot,
                "return_1d": ret_1d,
                "return_1w": ret_1w,
                "return_1m": ret_1m,
                "rvol": rvol,
                "today_volume": today_vol,
                "avg_volume": avg_vol_20,
                "earnings_date": earnings_date,
                "has_options": False,
                "chain_ok": False,
                "error": "No valid expiry in DTE window"
            }

        # Check if earnings catalyst falls inside target expiry (Trap #5)
        if earnings_date:
            try:
                ed_dt = datetime.strptime(earnings_date[:10], "%Y-%m-%d").date()
                exp_dt = datetime.strptime(target_exp, "%Y-%m-%d").date()
                if date.today() <= ed_dt <= exp_dt:
                    has_catalyst = True
            except Exception:
                pass

        # Fetch option chain for target expiry
        chain = t.option_chain(target_exp)
        calls_df = chain.calls.copy()
        puts_df = chain.puts.copy()

        return {
            "symbol": ticker_symbol,
            "spot": spot,
            "return_1d": ret_1d,
            "return_1w": ret_1w,
            "return_1m": ret_1m,
            "today_volume": today_vol,
            "avg_volume": avg_vol_20,
            "rvol": rvol,
            "earnings_date": earnings_date,
            "has_catalyst": has_catalyst,
            "has_options": True,
            "target_expiry": target_exp,
            "dte": dte,
            "calls_df": calls_df,
            "puts_df": puts_df,
            "chain_ok": True
        }

    except Exception as e:
        logger.error(f"Error fetching data for {ticker_symbol}: {e}")
        return None
