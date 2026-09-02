"""
compare_rtis_vs_full.py — System 1 Baseline vs Complete System Comparison

Runs identical test journeys across corridors comparing:
A. System 1 Only: RTIS / Pure Kinematics (No System 2 risk caps, no System 3 feedback)
B. Complete System: System 1 + System 2 (MLETAEngine) + System 3 (RestrictionEngine) closed-loop

Outputs: reports/rtis_vs_full_comparison.csv
"""

import sys
import os
import json
import math
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_generator.dataset_builder import build_synthetic_journey
from src.prediction.ml_predictor import MLETAEngine, BasePredictor, ConditionPrediction


class NoOpPredictor(BasePredictor):
    """Predictor for System 1 Only: Returns zero risk so System 3 never intervenes."""
    def predict(self, *args, current_state: Dict[str, Any] = None, train_state_dict: Dict[str, Any] = None, context: Dict[str, Any] = None, **kwargs) -> ConditionPrediction:
        st = current_state or train_state_dict or {}
        timestamp = st.get("timestamp", "06:45:00")
        return ConditionPrediction(
            prediction_timestamp=timestamp,
            prediction_horizon_min=30.0,
            fog_risk=0.0,
            congestion_risk=0.0,
            delay_risk=0.0,
            operational_risk=0.0,
            confidence=1.0,
            expected_speed_impact="NONE",
            predicted_condition_summary="SYSTEM_1_KINEMATICS_ONLY",
            prediction_source="SYSTEM_1_BASELINE",
            evidence={"mode": "SYSTEM_1_NOOP"}
        )


def run_rtis_vs_full_experiment(
    route_file: str,
    events_file: str,
    train_id: str = "12017",
    start_time_str: str = "06:45:00",
    season: str = "Winter/Fog",
    zone: str = "NR",
    max_steps: int = None
) -> Dict[str, Any]:
    """
    Executes identical journey seeds under System 1 Only vs Complete System.
    """
    temp_dir = PROJECT_ROOT / "reports" / "temp_eval"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 1. Run Complete System
    full_csv = str(temp_dir / "journey_complete_system.csv")
    full_json = str(temp_dir / "journey_complete_system.json")
    
    res_full = build_synthetic_journey(
        route_filepath=route_file,
        events_filepath=events_file,
        train_id=train_id,
        journey_id="EVAL_FULL_01",
        start_time_str=start_time_str,
        season=season,
        zone=zone,
        output_csv_path=full_csv,
        output_json_path=full_json,
        max_steps=max_steps,
        verbose=False
    )

    # 2. Run System 1 Only (Identical inputs, No System 2/3 intervention)
    rtis_csv = str(temp_dir / "journey_rtis_only.csv")
    rtis_json = str(temp_dir / "journey_rtis_only.json")

    res_rtis = build_synthetic_journey(
        route_filepath=route_file,
        events_filepath=events_file,
        train_id=train_id,
        journey_id="EVAL_RTIS_01",
        start_time_str=start_time_str,
        season=season,
        zone=zone,
        output_csv_path=rtis_csv,
        output_json_path=rtis_json,
        predictor=NoOpPredictor(),
        max_steps=max_steps,
        verbose=False
    )

    # Load and evaluate observations
    df_full = pd.read_csv(full_csv)
    df_rtis = pd.read_csv(rtis_csv)

    # Ground truth actual remaining minutes to destination
    y_true_full = df_full["target_eta_to_destination_min"].values
    y_true_rtis = df_rtis["target_eta_to_destination_min"].values

    # Predicted destination ETAs using Phase 8 Machine Learning Engine
    ml_engine = MLETAEngine()
    y_pred_full_list = []
    for row in df_full.to_dict(orient="records"):
        pred = ml_engine.predict(row, context={"season": season, "zone": zone})
        y_pred_full_list.append(pred.eta_destination_min)
    y_pred_full = np.array(y_pred_full_list)
    
    # RTIS baseline ETA calculation: Instantaneous speed kinematics (dist / speed)
    # where speed > 5 km/h, else fallback to distance / scheduled average
    speeds = df_rtis["current_speed_kmph"].values
    dists = df_rtis["distance_to_destination_km"].values
    y_pred_rtis = np.zeros_like(dists)
    for i, (d, s) in enumerate(zip(dists, speeds)):
        if s > 15.0:
            y_pred_rtis[i] = (d / s) * 60.0
        else:
            y_pred_rtis[i] = (d / 65.0) * 60.0  # nominal line speed fallback

    # Compute errors
    err_full = np.abs(y_pred_full - y_true_full)
    err_rtis = np.abs(y_pred_rtis - y_true_rtis)

    metrics_full = {
        "mae": float(np.mean(err_full)),
        "rmse": float(np.sqrt(np.mean((y_pred_full - y_true_full) ** 2))),
        "p90_error": float(np.percentile(err_full, 90)),
        "max_error": float(np.max(err_full)),
        "final_arrival_error": float(abs(res_full["actual_duration_min"] - df_full["target_eta_to_destination_min"].iloc[0])),
        "sample_count": len(df_full)
    }

    metrics_rtis = {
        "mae": float(np.mean(err_rtis)),
        "rmse": float(np.sqrt(np.mean((y_pred_rtis - y_true_rtis) ** 2))),
        "p90_error": float(np.percentile(err_rtis, 90)),
        "max_error": float(np.max(err_rtis)),
        "final_arrival_error": float(abs(res_rtis["actual_duration_min"] - df_rtis["target_eta_to_destination_min"].iloc[0])),
        "sample_count": len(df_rtis)
    }

    mae_improvement_pct = ((metrics_rtis["mae"] - metrics_full["mae"]) / max(0.001, metrics_rtis["mae"])) * 100.0
    rmse_improvement_pct = ((metrics_rtis["rmse"] - metrics_full["rmse"]) / max(0.001, metrics_rtis["rmse"])) * 100.0

    comparison_results = {
        "rtis_baseline": metrics_rtis,
        "complete_system": metrics_full,
        "mae_improvement_pct": float(mae_improvement_pct),
        "rmse_improvement_pct": float(rmse_improvement_pct),
        "total_test_observations": len(df_full)
    }

    # Save CSV Report
    csv_rows = [
        {
            "System Architecture": "System 1 (RTIS/Physics Simulator Alone)",
            "ETA MAE (min)": f"{metrics_rtis['mae']:.2f}",
            "ETA RMSE (min)": f"{metrics_rtis['rmse']:.2f}",
            "P90 Error (min)": f"{metrics_rtis['p90_error']:.2f}",
            "Max Error (min)": f"{metrics_rtis['max_error']:.2f}",
            "Final Arrival Error (min)": f"{metrics_rtis['final_arrival_error']:.2f}",
            "Observations": metrics_rtis["sample_count"],
            "Status": "Baseline Reference"
        },
        {
            "System Architecture": "Complete System (System 1 + 2 + 3 Closed Loop)",
            "ETA MAE (min)": f"{metrics_full['mae']:.2f}",
            "ETA RMSE (min)": f"{metrics_full['rmse']:.2f}",
            "P90 Error (min)": f"{metrics_full['p90_error']:.2f}",
            "Max Error (min)": f"{metrics_full['max_error']:.2f}",
            "Final Arrival Error (min)": f"{metrics_full['final_arrival_error']:.2f}",
            "Observations": metrics_full["sample_count"],
            "Status": f"+{mae_improvement_pct:.1f}% MAE Improvement"
        }
    ]

    rep_dir = PROJECT_ROOT / "reports"
    rep_dir.mkdir(parents=True, exist_ok=True)
    csv_file = rep_dir / "rtis_vs_full_comparison.csv"
    pd.DataFrame(csv_rows).to_csv(csv_file, index=False)

    return comparison_results


if __name__ == "__main__":
    route = str(PROJECT_ROOT / "Data" / "routes" / "delhi_dehradun_route.json")
    evts = str(PROJECT_ROOT / "src" / "simulator" / "events" / "simulation_events.json")
    res = run_rtis_vs_full_experiment(route, evts)
    print(json.dumps(res, indent=2))
