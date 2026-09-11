"""
Integration tests for the Web API and frontend endpoints.
"""

import unittest
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from starlette.testclient import TestClient
from web.app import app

class TestWebApp(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_index_page(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Options Skew Map", resp.text)
        self.assertIn("The Name Radar", resp.text)
        self.assertIn("The Action Board", resp.text)
        self.assertIn("quadrantBackgroundPlugin", resp.text)
        self.assertIn("sectorBenchmarkPlugin", resp.text)
        self.assertIn("renderSectorHeatGrid", resp.text)
        self.assertIn("toggleCrosshairCenter", resp.text)
        self.assertIn("toast-container", resp.text)

    def test_api_calculate(self):
        payload = {
            "spot": 100.0,
            "strike_call": 105.0,
            "strike_put": 95.0,
            "dte": 30.0,
            "atm_iv": 0.25,
            "call_iv": 0.24,
            "put_iv": 0.28,
            "rate": 0.045,
            "ret_1m": -2.0,
            "ret_vs_bench": -1.0,
            "rvol": 1.2,
            "symbol": "AAPL",
            "sector": "Technology",
            "sector_rank_pct": 60
        }
        resp = self.client.post("/api/calculate", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("quadrant", data)
        self.assertIn("vol_points", data)
        self.assertIn("readout_sentence", data)
        self.assertFalse(data["sanity_exceeded"])

    def test_api_config(self):
        resp = self.client.get("/api/config")
        self.assertEqual(resp.status_code, 200)
        cfg = resp.json()
        self.assertIn("target_delta", cfg)
        self.assertIn("sector_agreement_threshold", cfg)

        update_resp = self.client.post("/api/config", json={"target_delta": 0.25})
        self.assertEqual(update_resp.status_code, 200)
        self.assertEqual(update_resp.json()["status"], "success")

    def test_api_data(self):
        resp = self.client.get("/api/data")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("rows", data)
        self.assertIn("sector_summaries", data)
        self.assertIn("action_board", data)
        self.assertIn("market_median_vol_points", data)

    def test_api_snapshots(self):
        resp = self.client.get("/api/snapshots")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("snapshots", data)
        self.assertTrue(len(data["snapshots"]) >= 1)

    def test_api_export_csv(self):
        resp = self.client.get("/api/export-csv")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["content-type"], "text/csv; charset=utf-8")
        self.assertIn("attachment; filename=", resp.headers["content-disposition"])
        self.assertIn("Ticker,Sector", resp.text)

if __name__ == "__main__":
    unittest.main()
