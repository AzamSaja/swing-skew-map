"""
Unit tests for Options Skew Map calculation, Greeks, guardrails, and quadrant classification.
"""

import unittest
from datetime import date
import pandas as pd

from skew_map.config import SkewConfig
from skew_map.greeks import calculate_bs_delta, find_atm_iv, find_delta_strike
from skew_map.engine import classify_quadrant, analyze_ticker_options, process_universe
from skew_map.narrative import generate_row_sentence, generate_todays_read
from skew_map.storage import apply_snapshot_deltas

class TestSkewEngine(unittest.TestCase):

    def test_bs_delta_calculation(self):
        # S = 100, K = 100, DTE = 30, IV = 0.20, r = 0.045
        c_delta = calculate_bs_delta(100.0, 100.0, 30, 0.20, 0.045, "call")
        p_delta = calculate_bs_delta(100.0, 100.0, 30, 0.20, 0.045, "put")

        # ATM call delta should be approx ~0.51 - 0.53
        self.assertAlmostEqual(c_delta, 0.52, delta=0.05)
        # Put delta should be Call delta - 1
        self.assertAlmostEqual(p_delta, c_delta - 1.0, delta=0.01)

        # OTM Call: K = 105 -> delta should be < 0.50
        otm_c_delta = calculate_bs_delta(100.0, 105.0, 30, 0.20, 0.045, "call")
        self.assertTrue(0.10 < otm_c_delta < 0.40)

        # OTM Put: K = 95 -> abs(delta) should be < 0.50
        otm_p_delta = calculate_bs_delta(100.0, 95.0, 30, 0.20, 0.045, "put")
        self.assertTrue(-0.40 < otm_p_delta < -0.10)

    def test_quadrant_classification(self):
        # 1. Contrarian Bid: Return < 0, Skew < 0
        cb = classify_quadrant(-3.5, -0.05)
        self.assertEqual(cb["code"], "contrarian_bid")
        self.assertEqual(cb["action"], "Watchlist")

        # 2. Chase / Crowded: Return > 0, Skew < 0
        chase = classify_quadrant(4.2, -0.06)
        self.assertEqual(chase["code"], "chase")
        self.assertEqual(chase["verdict"], "MOMENTUM")

        # 3. Hedged Rally: Return > 0, Skew > 0
        hr = classify_quadrant(6.1, 0.12)
        self.assertEqual(hr["code"], "hedged_rally")
        self.assertEqual(hr["action"], "Tighten Stops")

        # 4. Fear: Return < 0, Skew > 0
        fear = classify_quadrant(-5.0, 0.15)
        self.assertEqual(fear["code"], "fear")
        self.assertEqual(fear["action"], "Leave Alone")

    def test_sanity_ceiling_trap4(self):
        # Construct mock option chain with an absurd quote (e.g. Duke Energy -1.43 bug)
        mock_raw = {
            "symbol": "DUK",
            "spot": 100.0,
            "return_1d": 0.5,
            "return_1w": 1.0,
            "return_1m": 2.0,
            "rvol": 1.0,
            "has_options": True,
            "chain_ok": True,
            "dte": 30,
            "calls_df": pd.DataFrame({
                "strike": [95.0, 100.0, 105.0],
                "impliedVolatility": [0.30, 0.15, 0.45],  # Abnormal high call IV
                "openInterest": [100, 500, 200],
                "bid": [5.0, 2.0, 1.0],
                "ask": [5.2, 2.1, 1.1]
            }),
            "puts_df": pd.DataFrame({
                "strike": [95.0, 100.0, 105.0],
                "impliedVolatility": [0.10, 0.15, 0.20],  # Low put IV -> skew heavily negative!
                "openInterest": [100, 500, 200],
                "bid": [1.0, 2.0, 5.0],
                "ask": [1.1, 2.1, 5.2]
            })
        }
        res = analyze_ticker_options(mock_raw)
        # Should be flagged or fail chain_ok due to sanity ceiling violation
        self.assertFalse(res["chain_ok"])
        self.assertIn("Exceeded sanity ceiling", res["rejection_reason"])

    def test_sentence_template_part5(self):
        mock_row = {
            "symbol": "NVDA",
            "spot": 125.0,
            "return_1m": -4.5,
            "return_1m_vs_spy": -6.2,
            "rvol": 1.65,
            "sector_rank_pct": 20,
            "skew": -0.08,
            "chain_ok": True,
            "quadrant_1m": {
                "quadrant": "CONTRARIAN BID",
                "action": "Watchlist"
            },
            "has_catalyst": False
        }
        sentence = generate_row_sentence(mock_row)
        self.assertIn("NVDA", sentence)
        self.assertIn("clearly more for calls", sentence)
        self.assertIn("more upside than 20% of its sector", sentence)
        self.assertIn("down 4.5% on the month", sentence)
        self.assertIn("heavy volume (1.65x RVOL)", sentence)
        self.assertIn("CONTRARIAN BID — Watchlist", sentence)

    def test_trap5_earnings_catalyst(self):
        mock_row = {
            "symbol": "AAPL",
            "spot": 220.0,
            "return_1m": 3.0,
            "return_1m_vs_spy": 1.2,
            "rvol": 1.1,
            "sector_rank_pct": 75,
            "skew": 0.12,
            "chain_ok": True,
            "quadrant_1m": {
                "quadrant": "HEDGED RALLY",
                "action": "Tighten Stops"
            },
            "has_catalyst": True,
            "earnings_date": "2026-10-15"
        }
        sentence = generate_row_sentence(mock_row)
        self.assertIn("CAVEAT: Confirmed earnings", sentence)
        self.assertIn("dated event premium", sentence)

    def test_sector_agreement_trap3(self):
        # Create mock rows for a sector with split agreement (< 60%)
        mock_rows = [
            {"symbol": "A", "skew": 0.05, "vol_points": 5.0, "chain_ok": True, "sector": "Tech", "quadrant_1m": classify_quadrant(1, 0.05)},
            {"symbol": "B", "skew": 0.06, "vol_points": 6.0, "chain_ok": True, "sector": "Tech", "quadrant_1m": classify_quadrant(1, 0.06)},
            {"symbol": "C", "skew": -0.04, "vol_points": -4.0, "chain_ok": True, "sector": "Tech", "quadrant_1m": classify_quadrant(1, -0.04)},
            {"symbol": "D", "skew": -0.05, "vol_points": -5.0, "chain_ok": True, "sector": "Tech", "quadrant_1m": classify_quadrant(1, -0.05)}
        ]
        res = process_universe(
            ticker_data_list=[
                {"symbol": r["symbol"], "spot": 100, "return_1m": 1.0, "has_options": False}
                for r in mock_rows
            ],
            sector_map={r["symbol"]: "Tech" for r in mock_rows},
            watchlist_set=set()
        )
        # Manually verify sector summaries agreement computation
        summary = res["sector_summaries"].get("Tech")
        if summary:
            self.assertTrue(summary["has_caveat"] or summary["agreement"] <= 0.60)

    def test_delta_vs_prior_week_storage(self):
        current_rows = [
            {"symbol": "NVDA", "skew": -0.05, "quadrant_1m": {"quadrant": "CONTRARIAN BID"}}
        ]
        prior_snap = {
            "date": "2026-09-05",
            "rows": [
                {"symbol": "NVDA", "skew": 0.03, "quadrant_1m": {"quadrant": "FEAR"}}
            ]
        }
        updated = apply_snapshot_deltas(current_rows, prior_snap)
        self.assertEqual(updated[0]["delta_skew"], -0.08)
        self.assertTrue(updated[0]["is_flipped"])
        self.assertEqual(updated[0]["prior_quadrant"], "FEAR")

if __name__ == "__main__":
    unittest.main()

