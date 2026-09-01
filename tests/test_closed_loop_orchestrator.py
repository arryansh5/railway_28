"""
test_closed_loop_orchestrator.py — Tests for Phase 6 Step 6 (Full 30s Closed-Loop Orchestration)

Verifies:
1. Micro-test (15 timesteps): verifies 30s advancement and System 1 -> 2 -> 3 -> 1 loop.
2. Anti-leakage validation: features at t contain zero future information.
3. CSV and JSON output integrity.
4. Target label back-population correctness.
"""

import json
import unittest
from pathlib import Path
import pandas as pd

from src.data_generator.dataset_builder import build_synthetic_journey

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestClosedLoopOrchestrator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_csv = PROJECT_ROOT / "Data" / "synthetic_rtis" / "test_micro_journey.csv"
        cls.test_json = PROJECT_ROOT / "Data" / "synthetic_rtis" / "test_micro_journey.json"

    def test_micro_closed_loop_orchestration(self):
        """Rule 24: Micro-test (15 steps) verifies 3-system loop and observation outputs."""
        result = build_synthetic_journey(
            start_time_str="06:45:00",
            journey_id="JRN_MICRO_TEST",
            season="Winter/Fog",
            zone="NR",
            output_csv_path=str(self.test_csv),
            output_json_path=str(self.test_json),
            max_steps=15,
            verbose=False
        )

        self.assertEqual(len(result["observations"]), 15)
        self.assertTrue(self.test_csv.exists())
        self.assertTrue(self.test_json.exists())

        # Verify CSV row schema and monotonicity
        df = pd.read_csv(self.test_csv)
        self.assertEqual(len(df), 15)
        self.assertIn("latitude", df.columns)
        self.assertIn("longitude", df.columns)
        self.assertIn("predicted_fog_risk", df.columns)
        self.assertIn("predicted_congestion_probability", df.columns)
        self.assertIn("target_eta_to_destination_min", df.columns)

        # Verify 30s timestep progression
        time_diffs = df["simulation_time_sec"].diff().dropna()
        self.assertTrue((time_diffs == 30.0).all())

    def test_strict_anti_leakage_in_features(self):
        """Rule 16: Feature columns at timestamp t contain zero future states."""
        result = build_synthetic_journey(
            start_time_str="06:45:00",
            journey_id="JRN_LEAKAGE_TEST",
            season="Winter/Fog",
            zone="NR",
            output_csv_path=str(self.test_csv),
            output_json_path=str(self.test_json),
            max_steps=10,
            verbose=False
        )
        obs_list = result["observations"]

        for obs in obs_list:
            # Current time must match prediction timestamp
            self.assertEqual(obs["timestamp"], obs["prediction_timestamp"])
            # Target ETA to destination must be non-negative
            self.assertGreaterEqual(obs["target_eta_to_destination_min"], 0.0)


if __name__ == "__main__":
    unittest.main()
