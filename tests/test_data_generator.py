"""
Unit tests for the Historical/Synthetic Dataset Generator (Phase 6).
"""

import csv
import json
import unittest
from pathlib import Path

from src.data_generator.dataset_builder import build_synthetic_journey
from src.data_generator.validator import validate_ml_dataset


class TestDatasetGenerator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parent.parent
        route_path = cls.root / "Data" / "routes" / "delhi_dehradun_route.json"
        with open(route_path, "r", encoding="utf-8") as f:
            cls.route = json.load(f)

    def test_closed_loop_dataset_building(self):
        """Test generating synthetic journey via 30-second closed loop."""
        out_csv = self.root / "Data" / "synthetic_rtis" / "test_closed_loop.csv"
        observations = build_synthetic_journey(
            start_time_str="06:45:00",
            season="Winter/Fog",
            output_csv_path=str(out_csv)
        )
        self.assertGreater(len(observations), 100)
        self.assertTrue(out_csv.exists())

    def test_ml_dataset_validation(self):
        """Test running 20-rule dataset and anti-leakage validator."""
        val_summary = validate_ml_dataset()
        self.assertTrue(val_summary["validation_passed"])
        self.assertEqual(val_summary["errors_count"], 0)


if __name__ == "__main__":
    unittest.main()
