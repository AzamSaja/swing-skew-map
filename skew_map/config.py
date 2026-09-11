"""
Configuration parameters embodying the 7 decisions and trap guardrails
from the Notion Skew Map framework.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SNAPSHOT_DIR = DATA_DIR / "snapshots"
DEFAULT_UNIVERSE_PATH = DATA_DIR / "default_universe.json"
DEFAULT_IDX_UNIVERSE_PATH = DATA_DIR / "idx_universe.json"

@dataclass
class SkewConfig:
    market: str = "US"  # "US" or "IDX"
    
    # Decision #1: Delta level for probability-equidistant strikes
    target_delta: float = 0.25  # 25-delta option (~1-in-4 probability)
    delta_tolerance: float = 0.08  # allowable search window [0.17, 0.33]

    # Decision #2: Expiry rule (standard monthly contract, ~30-45 DTE)
    min_dte: int = 18          # avoid front-week noise / gamma expiration traps
    max_dte: int = 55          # keep within active swing trading horizon
    prefer_third_friday: bool = True

    # Decision #3: Normalization settings
    # Normalized skew = (Put_IV - Call_IV) / ATM_IV (used for intra-sector ranking)
    # Vol points = (Put_IV - Call_IV) * 100 (used for cross-sector comparisons)
    
    # Decision #4: Benchmarking
    benchmark_symbol: str = "SPY"
    index_symbols: List[str] = field(default_factory=lambda: ["SPY", "QQQ", "IWM"])

    # Decision #5: Quality bar & Chain OK threshold
    min_open_interest: int = 20
    min_atm_iv: float = 0.05
    max_atm_iv: float = 3.50

    # Decision #6: Sanity ceiling (Trap #4 - Reject absurd quotes)
    max_abs_normalized_skew: float = 1.25
    max_abs_vol_points: float = 45.0

    # Trap #3: Sector Agreement threshold
    sector_agreement_threshold: float = 0.60  # Require >= 60% agreement for valid sector verdict

    # Risk-free rate for Black-Scholes delta calculations (approx current SOFR / US 3M T-bill)
    risk_free_rate: float = 0.045

DEFAULT_CONFIG = SkewConfig()

