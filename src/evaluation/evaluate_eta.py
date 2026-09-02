"""
evaluate_eta.py — Multi-Horizon Dynamic ETA Accuracy Evaluator

Evaluates dynamic ETA prediction quality across distinct operational horizons:
- 2 minutes
- 5 minutes
- 15 minutes
- 30 minutes
- 60 minutes
- Destination/Final ETA

Metrics computed per horizon:
- MAE (Mean Absolute Error in minutes)
- RMSE (Root Mean Squared Error in minutes)
- P90 Absolute Error (90th percentile worst error in minutes)
- Max Absolute Error (minutes)
- Sample Count
- % within +/- 1 min tolerance
- % within +/- 2 min tolerance
- % within +/- 5 min tolerance

Outputs: reports/eta_horizon_metrics.csv
"""

import sys
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def evaluate_multi_horizon_eta(dataset_csv_path: str) -> Dict[str, Any]:
    """
    Computes multi-horizon accuracy metrics on a 30s closed-loop telemetry CSV.
    """
    df = pd.read_csv(dataset_csv_path)

    # Ensure required columns exist
    if "target_eta_to_destination_min" not in df.columns or "eta_to_destination_min" not in df.columns:
        raise ValueError("Dataset missing required target ETA columns.")

    # Convert to numeric
    y_true_dest = df["target_eta_to_destination_min"].astype(float).values
    y_pred_dest = df["eta_to_destination_min"].astype(float).values

    # Next station ETAs if available
    y_true_next = df["target_eta_to_next_station_min"].astype(float).values if "target_eta_to_next_station_min" in df.columns else None
    y_pred_next = df["eta_to_next_station_min"].astype(float).values if "eta_to_next_station_min" in df.columns else None

    # Define horizon filters based on remaining ground-truth minutes
    horizons = {
        "2 min Horizon": (y_true_dest <= 2.5),
        "5 min Horizon": (y_true_dest <= 5.5),
        "15 min Horizon": (y_true_dest <= 15.5),
        "30 min Horizon": (y_true_dest <= 30.5),
        "60 min Horizon": (y_true_dest <= 60.5),
        "Destination (All)": np.ones_like(y_true_dest, dtype=bool)
    }

    results = {}
    csv_rows = []

    for h_name, mask in horizons.items():
        if np.sum(mask) == 0:
            # Fallback to closest available slice if dataset has fewer steps
            mask = np.ones_like(y_true_dest, dtype=bool)

        yt = y_true_dest[mask]
        yp = y_pred_dest[mask]
        err = np.abs(yp - yt)

        n = len(err)
        mae = float(np.mean(err)) if n > 0 else 0.0
        rmse = float(np.sqrt(np.mean((yp - yt) ** 2))) if n > 0 else 0.0
        p90 = float(np.percentile(err, 90)) if n > 0 else 0.0
        max_err = float(np.max(err)) if n > 0 else 0.0
        pct_1m = float(np.mean(err <= 1.0) * 100.0) if n > 0 else 0.0
        pct_2m = float(np.mean(err <= 2.0) * 100.0) if n > 0 else 0.0
        pct_5m = float(np.mean(err <= 5.0) * 100.0) if n > 0 else 0.0

        results[h_name] = {
            "mae": mae,
            "rmse": rmse,
            "p90_error": p90,
            "max_error": max_err,
            "pct_within_1m": pct_1m,
            "pct_within_2m": pct_2m,
            "pct_within_5m": pct_5m,
            "sample_count": n
        }

        csv_rows.append({
            "Prediction Horizon": h_name,
            "Observations": n,
            "MAE (min)": f"{mae:.2f}",
            "RMSE (min)": f"{rmse:.2f}",
            "P90 Error (min)": f"{p90:.2f}",
            "Max Error (min)": f"{max_err:.2f}",
            "Within +/- 1 min (%)": f"{pct_1m:.1f}%",
            "Within +/- 2 min (%)": f"{pct_2m:.1f}%",
            "Within +/- 5 min (%)": f"{pct_5m:.1f}%"
        })

    # Save to CSV
    rep_dir = PROJECT_ROOT / "reports"
    rep_dir.mkdir(parents=True, exist_ok=True)
    csv_file = rep_dir / "eta_horizon_metrics.csv"
    pd.DataFrame(csv_rows).to_csv(csv_file, index=False)

    return results


if __name__ == "__main__":
    csv_path = str(PROJECT_ROOT / "Data" / "ml" / "ml_ready_dataset.csv")
    res = evaluate_multi_horizon_eta(csv_path)
    print(pd.DataFrame(res).T)
