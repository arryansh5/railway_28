"""
Unit tests for the Historical/Synthetic Dataset Generator (Phase 6).
"""

import csv
import json
import unittest
from pathlib import Path

from src.data_generator.generator import DatasetGenerator


class TestDatasetGenerator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parent.parent
        route_path = cls.root / "Data" / "routes" / "delhi_dehradun_route.json"
        with open(route_path, "r", encoding="utf-8") as f:
            cls.route = json.load(f)

    def test_determinism_with_fixed_seed(self):
        """Test that same seed produces identical outputs."""
        gen1 = DatasetGenerator(self.route, seed=42)
        gen2 = DatasetGenerator(self.route, seed=42)

        data1 = gen1.generate_journey_data(num_days=3)
        data2 = gen2.generate_journey_data(num_days=3)

        self.assertEqual(len(data1), len(data2))
        self.assertEqual(data1[0]["actual_section_running_time_min"], data2[0]["actual_section_running_time_min"])
        self.assertEqual(data1[5]["journey_id"], data2[5]["journey_id"])

    def test_schema_and_synthetic_labeling(self):
        """Test that all required columns and synthetic labels exist."""
        gen = DatasetGenerator(self.route, seed=100)
        data = gen.generate_journey_data(num_days=2)

        required_cols = [
            "journey_id", "train_id", "train_type", "timestamp", "hour", "day_of_week",
            "section_id", "from_station_id", "to_station_id", "section_distance_km",
            "scheduled_running_time_min", "entry_speed_kmph", "entry_delay_min",
            "congestion_level", "weather_condition", "actual_section_running_time_min",
            "data_source"
        ]

        self.assertGreater(len(data), 0)
        for row in data:
            for col in required_cols:
                self.assertIn(col, row)
            self.assertEqual(row["data_source"], "SYNTHETIC_DATASET")

    def test_temporal_split_integrity(self):
        """Test that train/val/test splits have no date leakage and preserve chronological order."""
        train_path = self.root / "Data" / "historical" / "train.csv"
        val_path = self.root / "Data" / "historical" / "val.csv"
        test_path = self.root / "Data" / "historical" / "test.csv"

        self.assertTrue(train_path.exists())
        self.assertTrue(val_path.exists())
        self.assertTrue(test_path.exists())

        def get_dates(p):
            with open(p, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                return sorted(list(set(row["date"] for row in reader)))

        train_dates = get_dates(train_path)
        val_dates = get_dates(val_path)
        test_dates = get_dates(test_path)

        # No overlapping dates
        self.assertEqual(len(set(train_dates).intersection(set(val_dates))), 0)
        self.assertEqual(len(set(val_dates).intersection(set(test_dates))), 0)
        self.assertEqual(len(set(train_dates).intersection(set(test_dates))), 0)

        # Chronological progression: max(train) < min(val) and max(val) < min(test)
        self.assertLess(max(train_dates), min(val_dates))
        self.assertLess(max(val_dates), min(test_dates))

    def test_causal_congestion_impact(self):
        """Test that high congestion causes longer section transit times on average than low congestion."""
        gen = DatasetGenerator(self.route, seed=42)
        data = gen.generate_journey_data(num_days=30)

        # Test on SEC_GZB_MTC
        gzb_mtc = [r for r in data if r["section_id"] == "SEC_GZB_MTC"]
        low_cong = [r["actual_section_running_time_min"] for r in gzb_mtc if r["congestion_level"] == "LOW"]
        high_cong = [r["actual_section_running_time_min"] for r in gzb_mtc if r["congestion_level"] == "HIGH"]

        if low_cong and high_cong:
            mean_low = sum(low_cong) / len(low_cong)
            mean_high = sum(high_cong) / len(high_cong)
            self.assertGreater(mean_high, mean_low)


if __name__ == "__main__":
    unittest.main()
