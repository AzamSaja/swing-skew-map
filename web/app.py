"""
FastAPI web application backend serving the interactive Options Skew Map Dashboard.
Supports multi-market (US & IDX), interactive calculation sandboxes, and runtime configuration.
"""

from pathlib import Path
import io
from typing import Optional, Dict, Any
import pandas as pd
from pydantic import BaseModel, Field
from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from skew_map.config import DEFAULT_CONFIG, SkewConfig
from skew_map.greeks import calculate_bs_delta
from skew_map.engine import classify_quadrant
from skew_map.narrative import generate_row_sentence
from skew_map.pipeline import run_skew_scan
from skew_map.storage import list_snapshots, load_snapshot

app = FastAPI(title="Options Skew Map Desk", version="2.0.0")

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "web" / "static"
TEMPLATES_DIR = BASE_DIR / "web" / "templates"

try:
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Multi-market cache for instant dashboard responsiveness
CACHE = {
    "US": None,
    "IDX": None,
    "is_scanning": False,
    "scan_progress": "Idle"
}

def get_or_load_data(market: str = "US"):
    m = market.upper()
    if CACHE.get(m):
        return CACHE[m]
    
    snaps = list_snapshots(market=m)
    if snaps:
        data = load_snapshot(snaps[0])
        if data:
            if not data.get("market"):
                data["market"] = m
            if not data.get("benchmark_symbol"):
                data["benchmark_symbol"] = "^JKSE" if m == "IDX" else "SPY"
            CACHE[m] = data
            return data
    return None

@app.get("/", response_class=HTMLResponse)
def index_page():
    index_file = TEMPLATES_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>Dashboard loading...</h1>")
    with open(index_file, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/api/data")
def get_data(market: str = Query("US")):
    m = market.upper()
    data = get_or_load_data(m)
    if not data:
        return JSONResponse({
            "status": "no_data",
            "market": m,
            "message": f"No {m} data available yet. Please trigger a scan."
        })
    return JSONResponse(data)

@app.get("/api/snapshots")
def get_snapshots_list(market: Optional[str] = Query(None)):
    m = market.upper() if market else None
    snaps = list_snapshots(market=m)
    all_snaps = list_snapshots()
    items = []
    for s in all_snaps:
        is_idx = s.endswith("_idx")
        date_part = s.replace("_idx", "")
        items.append({
            "id": s,
            "date": date_part,
            "market": "IDX" if is_idx else "US",
            "label": f"{'🇮🇩 IDX' if is_idx else '🇺🇸 US'} — {date_part}"
        })
    return JSONResponse({"snapshots": snaps, "all_snapshots": all_snaps, "items": items})

@app.get("/api/snapshots/{snap_date}")
def get_snapshot_by_date(snap_date: str):
    s = snap_date.lower().strip()
    if s in ["latest_us", "latest-us"]:
        snaps = list_snapshots(market="US")
        if not snaps:
            raise HTTPException(status_code=404, detail="No US snapshots found")
        data = load_snapshot(snaps[0])
    elif s in ["latest_idx", "latest-idx"]:
        snaps = list_snapshots(market="IDX")
        if not snaps:
            raise HTTPException(status_code=404, detail="No IDX snapshots found")
        data = load_snapshot(idx_snaps[0] if (idx_snaps := list_snapshots(market="IDX")) else snaps[0])
    else:
        data = load_snapshot(snap_date)
    
    if not data:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return JSONResponse(data)

def perform_background_scan(market: str = "US", tickers: str = None):
    m = market.upper()
    CACHE["is_scanning"] = True
    CACHE["scan_progress"] = f"Fetching {m} market chains..."
    try:
        custom_symbols = [s.strip().upper() for s in tickers.split(",")] if tickers else None
        results = run_skew_scan(symbols=custom_symbols, save_to_disk=True, market=m, config=DEFAULT_CONFIG)
        CACHE[m] = results
        CACHE["scan_progress"] = "Complete"
    except Exception as e:
        CACHE["scan_progress"] = f"Error: {e}"
    finally:
        CACHE["is_scanning"] = False

@app.post("/api/scan")
def trigger_scan(background_tasks: BackgroundTasks, market: str = Query("US"), tickers: str = Query(None)):
    if CACHE["is_scanning"]:
        return JSONResponse({"status": "busy", "message": "Scan already in progress."})
    
    background_tasks.add_task(perform_background_scan, market, tickers)
    return JSONResponse({"status": "started", "market": market.upper(), "message": f"{market.upper()} scan initiated."})

@app.get("/api/scan-status")
def scan_status():
    return JSONResponse({
        "is_scanning": CACHE["is_scanning"],
        "progress": CACHE["scan_progress"]
    })

# Interactive Function Sandbox / Greeks Calculator Endpoint
class CalculateRequest(BaseModel):
    spot: float = Field(100.0, description="Underlying Stock Price")
    strike_call: float = Field(105.0, description="OTM Call Strike")
    strike_put: float = Field(95.0, description="OTM Put Strike")
    dte: float = Field(30.0, description="Days to Expiration")
    atm_iv: float = Field(0.25, description="ATM Implied Volatility (decimal)")
    call_iv: float = Field(0.24, description="Call Implied Volatility (decimal)")
    put_iv: float = Field(0.28, description="Put Implied Volatility (decimal)")
    rate: float = Field(0.045, description="Risk-Free Rate (decimal)")
    ret_1m: float = Field(2.5, description="1-Month % Return")
    ret_vs_bench: float = Field(1.2, description="1-Month Return vs Benchmark %")
    rvol: float = Field(1.2, description="Relative Volume")
    symbol: str = Field("CUSTOM", description="Ticker Symbol")
    sector: str = Field("Technology", description="Sector Name")
    sector_rank_pct: int = Field(50, description="Sector Rank Percentile")
    market: Optional[str] = Field("US", description="Market: US or IDX")

@app.post("/api/calculate")
def calculate_sandbox(req: CalculateRequest):
    """
    Live interactive calculation endpoint for testing Black-Scholes Greeks,
    normalized skew, vol points, trap ceilings, and Part 5 readout sentences.
    """
    call_delta = calculate_bs_delta(req.spot, req.strike_call, req.dte, req.call_iv, req.rate, "call")
    put_delta = calculate_bs_delta(req.spot, req.strike_put, req.dte, req.put_iv, req.rate, "put")

    raw_diff = req.put_iv - req.call_iv
    vol_points = round(raw_diff * 100.0, 2)
    skew_normalized = round(raw_diff / req.atm_iv, 4) if req.atm_iv > 0 else 0.0

    # Trap #4 Ceiling check
    sanity_exceeded = (
        abs(skew_normalized) > DEFAULT_CONFIG.max_abs_normalized_skew or
        abs(vol_points) > DEFAULT_CONFIG.max_abs_vol_points
    )

    quadrant = classify_quadrant(req.ret_1m, skew_normalized)
    m = (req.market or "US").upper()
    is_idx = (m == "IDX") or req.symbol.upper().endswith(".JK")

    mock_row = {
        "symbol": req.symbol.upper(),
        "spot": req.spot,
        "skew": skew_normalized,
        "vol_points": vol_points,
        "atm_iv": round(req.atm_iv * 100.0, 2),
        "put_iv": round(req.put_iv * 100.0, 2),
        "put_delta": round(put_delta, 2),
        "call_iv": round(req.call_iv * 100.0, 2),
        "call_delta": round(call_delta, 2),
        "return_1m": req.ret_1m,
        "return_1m_vs_spy": req.ret_vs_bench,
        "rvol": req.rvol,
        "sector": req.sector,
        "sector_rank_pct": req.sector_rank_pct,
        "chain_ok": not sanity_exceeded,
        "rejection_reason": "Exceeded sanity ceiling (Trap #4)" if sanity_exceeded else None,
        "quadrant_1m": quadrant,
        "has_catalyst": False,
        "is_realized_model": is_idx,
        "market": "IDX" if is_idx else "US",
        "benchmark_symbol": "^JKSE" if is_idx else "SPY"
    }

    sentence = generate_row_sentence(mock_row)

    return JSONResponse({
        "call_delta": round(call_delta, 4),
        "put_delta": round(put_delta, 4),
        "raw_diff": round(raw_diff, 4),
        "vol_points": vol_points,
        "skew_normalized": skew_normalized,
        "sanity_exceeded": sanity_exceeded,
        "quadrant": quadrant,
        "readout_sentence": sentence,
        "details": mock_row
    })

# Runtime Configuration Inspection and Tuning Endpoint
@app.get("/api/config")
def get_config():
    return JSONResponse({
        "target_delta": DEFAULT_CONFIG.target_delta,
        "min_dte": DEFAULT_CONFIG.min_dte,
        "max_dte": DEFAULT_CONFIG.max_dte,
        "risk_free_rate": DEFAULT_CONFIG.risk_free_rate,
        "min_open_interest": DEFAULT_CONFIG.min_open_interest,
        "max_abs_normalized_skew": DEFAULT_CONFIG.max_abs_normalized_skew,
        "max_abs_vol_points": DEFAULT_CONFIG.max_abs_vol_points,
        "sector_agreement_threshold": DEFAULT_CONFIG.sector_agreement_threshold
    })

class ConfigUpdateRequest(BaseModel):
    target_delta: Optional[float] = None
    min_dte: Optional[int] = None
    max_dte: Optional[int] = None
    risk_free_rate: Optional[float] = None
    max_abs_normalized_skew: Optional[float] = None
    max_abs_vol_points: Optional[float] = None
    sector_agreement_threshold: Optional[float] = None

@app.post("/api/config")
def update_config(req: ConfigUpdateRequest):
    if req.target_delta is not None:
        DEFAULT_CONFIG.target_delta = req.target_delta
    if req.min_dte is not None:
        DEFAULT_CONFIG.min_dte = req.min_dte
    if req.max_dte is not None:
        DEFAULT_CONFIG.max_dte = req.max_dte
    if req.risk_free_rate is not None:
        DEFAULT_CONFIG.risk_free_rate = req.risk_free_rate
    if req.max_abs_normalized_skew is not None:
        DEFAULT_CONFIG.max_abs_normalized_skew = req.max_abs_normalized_skew
    if req.max_abs_vol_points is not None:
        DEFAULT_CONFIG.max_abs_vol_points = req.max_abs_vol_points
    if req.sector_agreement_threshold is not None:
        DEFAULT_CONFIG.sector_agreement_threshold = req.sector_agreement_threshold

    return JSONResponse({"status": "success", "message": "Configuration updated."})

@app.get("/api/export-csv")
def export_csv(market: str = Query("US")):
    m = market.upper()
    data = get_or_load_data(m)
    if not data or "rows" not in data:
        raise HTTPException(status_code=400, detail="No data to export.")

    export_records = []
    bench_name = data.get("benchmark_symbol", "^JKSE" if m == "IDX" else "SPY")
    for r in data["rows"]:
        export_records.append({
            "Ticker": r.get("symbol"),
            "Sector": r.get("sector"),
            "Market": m,
            "Spot": r.get("spot"),
            "ATM_IV_%": r.get("atm_iv"),
            "Put_25d_IV_%": r.get("put_iv"),
            "Put_Delta": r.get("put_delta"),
            "Call_25d_IV_%": r.get("call_iv"),
            "Call_Delta": r.get("call_delta"),
            "Skew_Normalized": r.get("skew"),
            "Vol_Points": r.get("vol_points"),
            "Return_1M_%": r.get("return_1m"),
            f"Return_1M_vs_{bench_name}_%": r.get("return_1m_vs_spy"),
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
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    scan_date = data.get("scan_date", "skew_map")
    response.headers["Content-Disposition"] = f"attachment; filename=skew_map_{m.lower()}_{scan_date}.csv"
    return response
