"""
Evaluation Metrics Module.
Computes standard benchmarks (MAE, RMSE, P90, threshold accuracies)
comparing ETA predictions against ground truth observations.
"""

import math
from typing import List, Dict, Any


class EvaluationMetrics:
    """
    Computes statistical evaluation metrics for train delay and ETA predictions.
    """

    @staticmethod
    def compute(actual_values: List[float], predicted_values: List[float]) -> Dict[str, Any]:
        """
        Compute evaluation metrics comparing actual vs predicted values (in minutes).

        Args:
            actual_values: Ground truth actual values (e.g. delays or offsets in minutes).
            predicted_values: Model predictions corresponding to actual values.

        Returns:
            Dictionary containing MAE, RMSE, P90 error, Accuracy within 5 min, and Accuracy within 10 min.
        """
        if not actual_values or not predicted_values:
            return {
                "count": 0,
                "mae": 0.0,
                "rmse": 0.0,
                "p90_error": 0.0,
                "accuracy_within_5_min": 0.0,
                "accuracy_within_10_min": 0.0,
            }

        n = min(len(actual_values), len(predicted_values))
        if n == 0:
            return {
                "count": 0,
                "mae": 0.0,
                "rmse": 0.0,
                "p90_error": 0.0,
                "accuracy_within_5_min": 0.0,
                "accuracy_within_10_min": 0.0,
            }

        errors = [abs(actual_values[i] - predicted_values[i]) for i in range(n)]
        raw_errors = [predicted_values[i] - actual_values[i] for i in range(n)]
        squared_errors = [(actual_values[i] - predicted_values[i]) ** 2 for i in range(n)]

        mae = sum(errors) / n
        rmse = math.sqrt(sum(squared_errors) / n)
        mean_bias = sum(raw_errors) / n

        sorted_errors = sorted(errors)
        p50_idx = int(math.ceil(0.50 * n)) - 1
        p90_idx = int(math.ceil(0.90 * n)) - 1
        p95_idx = int(math.ceil(0.95 * n)) - 1

        p50_error = sorted_errors[max(0, min(p50_idx, n - 1))]
        p90_error = sorted_errors[max(0, min(p90_idx, n - 1))]
        p95_error = sorted_errors[max(0, min(p95_idx, n - 1))]
        max_error = sorted_errors[-1]

        within_5 = sum(1 for e in errors if e <= 5.0)
        within_10 = sum(1 for e in errors if e <= 10.0)

        acc_5 = round((within_5 / n) * 100.0, 2)
        acc_10 = round((within_10 / n) * 100.0, 2)

        return {
            "count": n,
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "bias": round(mean_bias, 2),
            "p50_error": round(p50_error, 2),
            "p90_error": round(p90_error, 2),
            "p95_error": round(p95_error, 2),
            "max_error": round(max_error, 2),
            "accuracy_within_5_min": acc_5,
            "accuracy_within_10_min": acc_10,
        }

