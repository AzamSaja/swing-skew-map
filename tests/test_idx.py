"""
Unit and integration tests for IDX market integration and interactive web endpoints.
"""

import unittest
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from starlette.testclient import TestClient
from web.app import app
from skew_map.pipeline import load_universe_config

class TestIDXAndInteractiveWeb(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_idx_universe_config(self):
        cfg = load_universe_config(market="IDX")
        self.assertEqual(cfg.get("market"), "IDX")
        self.assertEqual(cfg.get("benchmark"), "^JKSE")
        self.assertIn("Financials", cfg.get("sectors", {}))
        self.assertIn("BBCA.JK", cfg["sectors"]["Financials"])

    def test_api_calculate_sandbox(self):
        payload = {
            "spot": 100.0,
            "strike_call": 105.0,
            "strike_put": 95.0,
            "dte": 30.0,
            "atm_iv": 0.25,
            "call_iv": 0.24,
            "put_iv": 0.28,
            "rate": 0.045,
            "ret_1m": -3.5,
            "ret_vs_bench": -2.0,
            "rvol": 1.2,
            "symbol": "TEST",
            "sector": "Technology",
            "sector_rank_pct": 25
        }
        resp = self.client.post("/api/calculate", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        
        self.assertIn("call_delta", data)
        self.assertIn("put_delta", data)
        self.assertIn("skew_normalized", data)
        self.assertIn("vol_points", data)
        self.assertIn("readout_sentence", data)
        self.assertIn("TEST", data["readout_sentence"])
        self.assertEqual(data["vol_points"], 4.0)  # (0.28 - 0.24) * 100 = 4.0
        self.assertEqual(data["skew_normalized"], 0.16) # 0.04 / 0.25 = 0.16

    def test_api_calculate_sanity_ceiling_trap4(self):
        # Trigger Trap #4 quote artifact test: absurd call IV vs put IV
        payload = {
            "spot": 100.0,
            "strike_call": 105.0,
            "strike_put": 95.0,
            "dte": 30.0,
            "atm_iv": 0.15,
            "call_iv": 0.45,  # absurdly high
            "put_iv": 0.10,
            "rate": 0.045,
            "ret_1m": 2.0,
            "ret_vs_bench": 1.0,
            "rvol": 1.0,
            "symbol": "BAD_QUOTE",
            "sector": "Utilities",
            "sector_rank_pct": 0
        }
        resp = self.client.post("/api/calculate", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["sanity_exceeded"])

    def test_api_config_get_and_post(self):
        # GET config
        resp = self.client.get("/api/config")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("target_delta", data)
        self.assertIn("sector_agreement_threshold", data)

        # POST config
        update_payload = {"target_delta": 0.26, "sector_agreement_threshold": 0.65}
        post_resp = self.client.post("/api/config", json=update_payload)
        self.assertEqual(post_resp.status_code, 200)

        # Re-check updated
        get_again = self.client.get("/api/config").json()
        self.assertEqual(get_again["target_delta"], 0.26)
        self.assertEqual(get_again["sector_agreement_threshold"], 0.65)

    def test_api_data_idx(self):
        resp = self.client.get("/api/data?market=idx")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        if data.get("status") != "no_data":
            self.assertEqual(data.get("market"), "IDX")
            self.assertEqual(data.get("benchmark_symbol"), "^JKSE")

    def test_api_export_csv_idx(self):
        resp = self.client.get("/api/export-csv?market=idx")
        if resp.status_code == 200:
            self.assertEqual(resp.headers["content-type"], "text/csv; charset=utf-8")
            self.assertIn("BBCA.JK", resp.text)

if __name__ == "__main__":
    unittest.main()

