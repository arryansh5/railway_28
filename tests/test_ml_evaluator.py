"""
test_ml_evaluator.py — Unit Tests for Phase 9 Comparative Model Evaluation Suite.
"""

import os
import unittest
from pathlib import Path

from src.prediction.ml_evaluator import (
    compute_error_metrics,
    ComparativeMLEvaluator,
    generate_benchmark_markdown_report,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestMLEvaluator(unittest.TestCase):

    def test_compute_error_metrics(self):
        """Tests math accuracy of MAE, RMSE, P50, and percentage windows."""
        preds = [10.0, 20.0, 30.0, 40.0]
        actuals = [12.0, 20.0, 25.0, 50.0]  # Errors: 2, 0, 5, 10
        metrics = compute_error_metrics(preds, actuals)

        self.assertEqual(metrics["samples"], 4)
        self.assertEqual(metrics["mae"], 4.25)
        self.assertEqual(metrics["max_error"], 10.0)
        self.assertEqual(metrics["accuracy_within_2_min"], 50.0)   # 2/4
        self.assertEqual(metrics["accuracy_within_5_min"], 75.0)   # 3/4
        self.assertEqual(metrics["accuracy_within_15_min"], 100.0) # 4/4

    def test_empty_metrics(self):
        """Tests safe handling of empty inputs."""
        metrics = compute_error_metrics([], [])
        self.assertEqual(metrics["samples"], 0)
        self.assertEqual(metrics["mae"], 0.0)

    def test_evaluator_on_dataset(self):
        """Tests end-to-end evaluation across all 4 models on ml_ready_dataset.csv."""
        dataset_path = str(PROJECT_ROOT / "Data" / "ml" / "ml_ready_dataset.csv")
        if not os.path.exists(dataset_path):
            self.skipTest("ML dataset not generated yet.")

        evaluator = ComparativeMLEvaluator()
        report = evaluator.evaluate_dataset(dataset_path)

        self.assertIn("total_observations", report)
        self.assertGreater(report["total_observations"], 0)

        # Check all 4 models evaluated
        overall_dest = report["overall"]["destination_eta"]
        for key in ["scheduled", "schedule_plus_delay", "historical_median", "ml_model"]:
            self.assertIn(key, overall_dest)
            self.assertIn("mae", overall_dest[key])
            self.assertIn("rmse", overall_dest[key])

        # Check slices computed
        self.assertIn("sliced", report)
        self.assertIn("section_breakdown", report)

        # Generate and check Markdown
        md_text = generate_benchmark_markdown_report(report)
        self.assertIn("Phase 9: Comprehensive ETA Model Evaluation", md_text)
        self.assertIn("Model 4: Phase 8 ML Regressor", md_text)


if __name__ == "__main__":
    unittest.main()
