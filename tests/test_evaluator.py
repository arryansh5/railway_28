"""
Unit tests for the Baseline Evaluator (Phase 7).
"""

import unittest
from src.prediction.evaluator import (
    load_dataset,
    evaluate_baselines,
    evaluate_sliced,
    evaluate_by_section,
    _parse_row,
    _is_truthy,
    _float_or_zero,
)
from src.prediction.baseline_engine import BaselineETAEngine


class TestDatasetLoading(unittest.TestCase):
    """Test CSV parsing and loading."""

    def test_load_val_dataset(self):
        """Verify val.csv loads successfully with expected shape."""
        rows = load_dataset("Data/historical/val.csv")
        self.assertGreater(len(rows), 0)
        # Each row should have the required columns
        for r in rows[:5]:
            self.assertIn("section_id", r)
            self.assertIn("scheduled_running_time_min", r)
            self.assertIn("actual_section_running_time_min", r)

    def test_load_train_dataset(self):
        """Verify train.csv loads successfully."""
        rows = load_dataset("Data/historical/train.csv")
        self.assertGreater(len(rows), 0)

    def test_load_nonexistent_raises(self):
        """Loading a missing file should raise FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_dataset("Data/historical/nonexistent.csv")

    def test_numeric_parsing(self):
        """Verify numeric fields are parsed as floats."""
        row = _parse_row({
            "section_id": "SEC_NDLS_GZB",
            "scheduled_running_time_min": "28.0",
            "actual_section_running_time_min": "30.5",
            "entry_delay_min": "-2.5",
            "congestion_level": "HIGH",
            "speed_restriction_active": "1",
        })
        self.assertIsNotNone(row)
        self.assertIsInstance(row["scheduled_running_time_min"], float)
        self.assertIsInstance(row["actual_section_running_time_min"], float)
        self.assertIsInstance(row["entry_delay_min"], float)
        self.assertEqual(row["congestion_level"], "HIGH")

    def test_empty_field_parsed_as_none(self):
        """Empty string fields should be parsed as None."""
        row = _parse_row({
            "section_id": "SEC_A_B",
            "scheduled_running_time_min": "28.0",
            "actual_section_running_time_min": "30.0",
            "restriction_speed_kmph": "",
        })
        self.assertIsNone(row["restriction_speed_kmph"])


class TestHelpers(unittest.TestCase):
    """Test helper utility functions."""

    def test_is_truthy(self):
        self.assertTrue(_is_truthy(1))
        self.assertTrue(_is_truthy(1.0))
        self.assertTrue(_is_truthy("1"))
        self.assertTrue(_is_truthy(True))
        self.assertFalse(_is_truthy(0))
        self.assertFalse(_is_truthy("0"))
        self.assertFalse(_is_truthy(None))
        self.assertFalse(_is_truthy(""))

    def test_float_or_zero(self):
        self.assertEqual(_float_or_zero("3.5"), 3.5)
        self.assertEqual(_float_or_zero(None), 0.0)
        self.assertEqual(_float_or_zero("abc"), 0.0)
        self.assertEqual(_float_or_zero(-2.0), -2.0)


class TestBaselineEvaluation(unittest.TestCase):
    """Test baseline evaluation logic on controlled data."""

    def _make_rows(self):
        """Create a small controlled dataset for testing."""
        return [
            {
                "section_id": "SEC_A_B",
                "scheduled_running_time_min": 30.0,
                "actual_section_running_time_min": 32.0,
                "historical_section_median_min": 31.0,
                "historical_section_p90_min": 38.0,
                "previous_section_delay_min": 2.0,
                "entry_delay_min": 3.0,
                "congestion_level": "LOW",
                "weather_condition": "CLEAR",
                "speed_restriction_active": 0,
                "unscheduled_halt_active": 0,
            },
            {
                "section_id": "SEC_B_C",
                "scheduled_running_time_min": 45.0,
                "actual_section_running_time_min": 55.0,
                "historical_section_median_min": 48.0,
                "historical_section_p90_min": 58.0,
                "previous_section_delay_min": 5.0,
                "entry_delay_min": 8.0,
                "congestion_level": "HIGH",
                "weather_condition": "RAIN",
                "speed_restriction_active": 1,
                "unscheduled_halt_active": 0,
            },
            {
                "section_id": "SEC_A_B",
                "scheduled_running_time_min": 30.0,
                "actual_section_running_time_min": 29.0,
                "historical_section_median_min": 31.0,
                "historical_section_p90_min": 38.0,
                "previous_section_delay_min": -1.0,
                "entry_delay_min": -2.0,
                "congestion_level": "LOW",
                "weather_condition": "CLEAR",
                "speed_restriction_active": 0,
                "unscheduled_halt_active": 0,
            },
        ]

    def test_overall_evaluation_returns_all_methods(self):
        """All three baseline methods should be present in results."""
        rows = self._make_rows()
        results = evaluate_baselines(rows)
        self.assertIn("SCHEDULED", results)
        self.assertIn("SCHEDULE_PLUS_DELAY", results)
        self.assertIn("HISTORICAL_MEDIAN", results)

    def test_scheduled_baseline_accuracy(self):
        """Verify SCHEDULED baseline produces correct predictions."""
        rows = self._make_rows()
        # Actuals: [32, 55, 29], Scheduled: [30, 45, 30]
        # Errors:  [2, 10, 1], MAE = 13/3 ≈ 4.33
        results = evaluate_baselines(rows, methods=["SCHEDULED"])
        mae = results["SCHEDULED"]["mae"]
        self.assertAlmostEqual(mae, 4.33, places=1)

    def test_historical_median_baseline(self):
        """Verify HISTORICAL_MEDIAN baseline uses median values."""
        rows = self._make_rows()
        # Actuals: [32, 55, 29], Medians: [31, 48, 31]
        # Errors:  [1, 7, 2], MAE = 10/3 ≈ 3.33
        results = evaluate_baselines(rows, methods=["HISTORICAL_MEDIAN"])
        mae = results["HISTORICAL_MEDIAN"]["mae"]
        self.assertAlmostEqual(mae, 3.33, places=1)

    def test_historical_median_beats_scheduled(self):
        """Historical median should have lower MAE than pure schedule on this data."""
        rows = self._make_rows()
        results = evaluate_baselines(rows)
        self.assertLess(
            results["HISTORICAL_MEDIAN"]["mae"],
            results["SCHEDULED"]["mae"]
        )

    def test_metrics_contain_extended_fields(self):
        """Check that extended metrics (P50, P95, bias) are present."""
        rows = self._make_rows()
        results = evaluate_baselines(rows, methods=["SCHEDULED"])
        m = results["SCHEDULED"]
        self.assertIn("bias", m)
        self.assertIn("p50_error", m)
        self.assertIn("p95_error", m)
        self.assertIn("max_error", m)


class TestSlicedEvaluation(unittest.TestCase):
    """Test operational condition slicing."""

    def _make_rows(self):
        return [
            {
                "section_id": "SEC_A_B",
                "scheduled_running_time_min": 30.0,
                "actual_section_running_time_min": 32.0,
                "historical_section_median_min": 31.0,
                "historical_section_p90_min": 38.0,
                "previous_section_delay_min": 0.0,
                "entry_delay_min": 2.0,
                "congestion_level": "LOW",
                "weather_condition": "CLEAR",
                "speed_restriction_active": 0,
                "unscheduled_halt_active": 0,
            },
            {
                "section_id": "SEC_B_C",
                "scheduled_running_time_min": 45.0,
                "actual_section_running_time_min": 60.0,
                "historical_section_median_min": 48.0,
                "historical_section_p90_min": 58.0,
                "previous_section_delay_min": 5.0,
                "entry_delay_min": 8.0,
                "congestion_level": "HIGH",
                "weather_condition": "RAIN",
                "speed_restriction_active": 1,
                "unscheduled_halt_active": 1,
            },
            {
                "section_id": "SEC_A_B",
                "scheduled_running_time_min": 30.0,
                "actual_section_running_time_min": 28.0,
                "historical_section_median_min": 31.0,
                "historical_section_p90_min": 38.0,
                "previous_section_delay_min": -1.0,
                "entry_delay_min": 1.0,
                "congestion_level": "LOW",
                "weather_condition": "CLEAR",
                "speed_restriction_active": 0,
                "unscheduled_halt_active": 0,
            },
        ]

    def test_sliced_returns_congestion_slices(self):
        """Should produce separate results for LOW and HIGH congestion."""
        rows = self._make_rows()
        sliced = evaluate_sliced(rows)
        self.assertIn("congestion_LOW", sliced)
        # HIGH only has 1 row so may be skipped (< 2), check gracefully
        if "congestion_HIGH" in sliced:
            self.assertIn("SCHEDULED", sliced["congestion_HIGH"])

    def test_sliced_low_congestion_better_than_high(self):
        """LOW congestion should have lower error than HIGH (schedule more reliable)."""
        rows = self._make_rows()
        sliced = evaluate_sliced(rows)
        if "congestion_LOW" in sliced and "congestion_HIGH" in sliced:
            low_mae = sliced["congestion_LOW"]["SCHEDULED"]["mae"]
            high_mae = sliced["congestion_HIGH"]["SCHEDULED"]["mae"]
            self.assertLessEqual(low_mae, high_mae)


class TestSectionBreakdown(unittest.TestCase):
    """Test per-section evaluation."""

    def test_by_section_groups_correctly(self):
        rows = [
            {"section_id": "SEC_A_B", "scheduled_running_time_min": 30.0,
             "actual_section_running_time_min": 32.0, "historical_section_median_min": 31.0,
             "previous_section_delay_min": 0.0},
            {"section_id": "SEC_A_B", "scheduled_running_time_min": 30.0,
             "actual_section_running_time_min": 28.0, "historical_section_median_min": 31.0,
             "previous_section_delay_min": 0.0},
            {"section_id": "SEC_B_C", "scheduled_running_time_min": 45.0,
             "actual_section_running_time_min": 50.0, "historical_section_median_min": 48.0,
             "previous_section_delay_min": 0.0},
            {"section_id": "SEC_B_C", "scheduled_running_time_min": 45.0,
             "actual_section_running_time_min": 43.0, "historical_section_median_min": 48.0,
             "previous_section_delay_min": 0.0},
        ]
        by_section = evaluate_by_section(rows)
        self.assertIn("SEC_A_B", by_section)
        self.assertIn("SEC_B_C", by_section)
        self.assertEqual(by_section["SEC_A_B"]["SCHEDULED"]["count"], 2)
        self.assertEqual(by_section["SEC_B_C"]["SCHEDULED"]["count"], 2)


class TestSectionTimePrediction(unittest.TestCase):
    """Test the static predict_section_time method."""

    def test_scheduled_baseline(self):
        row = {"scheduled_running_time_min": 40.0}
        result = BaselineETAEngine.predict_section_time(row, method="SCHEDULED")
        self.assertEqual(result, 40.0)

    def test_historical_median_baseline(self):
        row = {"scheduled_running_time_min": 40.0, "historical_section_median_min": 42.5}
        result = BaselineETAEngine.predict_section_time(row, method="HISTORICAL_MEDIAN")
        self.assertEqual(result, 42.5)

    def test_historical_median_falls_back_to_schedule(self):
        row = {"scheduled_running_time_min": 40.0, "historical_section_median_min": None}
        result = BaselineETAEngine.predict_section_time(row, method="HISTORICAL_MEDIAN")
        self.assertEqual(result, 40.0)

    def test_schedule_plus_delay(self):
        row = {"scheduled_running_time_min": 40.0, "previous_section_delay_min": 6.0}
        result = BaselineETAEngine.predict_section_time(row, method="SCHEDULE_PLUS_DELAY")
        self.assertEqual(result, 43.0)  # 40 + 6*0.5

    def test_schedule_plus_delay_negative_clamp(self):
        row = {"scheduled_running_time_min": 5.0, "previous_section_delay_min": -20.0}
        result = BaselineETAEngine.predict_section_time(row, method="SCHEDULE_PLUS_DELAY")
        self.assertEqual(result, 0.0)  # clamped at 0


if __name__ == "__main__":
    unittest.main()
