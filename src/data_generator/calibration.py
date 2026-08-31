"""
calibration.py — Phase 6: Step 3
Generates config/historical_calibration.json by compiling empirical risk priors
from Step 1 (Dataset Audit) and Step 2 (Historical Analysis).
Provides standard calibration parameters consumed by System 2 Predictor.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any


def build_historical_calibration(
    audit_report_path: str = r"D:\Projects\railway\reports\dataset_audit_report.json",
    analysis_summary_path: str = r"D:\Projects\railway\reports\historical_analysis_summary.json",
    output_config_path: str = r"D:\Projects\railway\config\historical_calibration.json"
) -> Dict[str, Any]:
    """
    Compiles empirical priors into config/historical_calibration.json.
    """
    print(f"[Calibration] Reading audit report from: {audit_report_path}")
    print(f"[Calibration] Reading analysis summary from: {analysis_summary_path}")

    if not os.path.exists(audit_report_path):
        raise FileNotFoundError(f"Audit report not found at: {audit_report_path}")
    if not os.path.exists(analysis_summary_path):
        raise FileNotFoundError(f"Analysis summary not found at: {analysis_summary_path}")

    with open(audit_report_path, "r", encoding="utf-8") as f:
        audit = json.load(f)
    with open(analysis_summary_path, "r", encoding="utf-8") as f:
        analysis = json.load(f)

    # 1. Hourly Congestion Map (24 hours)
    hourly_congestion = analysis.get("hourly_congestion_probability", {})

    # 2. Seasonal Fog Risk Map
    seasonal_fog = analysis.get("seasonal_fog_probability", {})

    # 3. Delay Cause Distribution
    delay_causes = analysis.get("primary_delay_cause_distribution", {})

    # 4. Empirical Corridor Baselines (NR/NCR focus)
    emp_means = analysis.get("empirical_means", {})

    calibration_config = {
        "metadata": {
            "title": "Indian Railways Historical Risk Calibration Matrix",
            "corridor": "New Delhi (NDLS) → Dehradun (DDN)",
            "primary_zones": ["NR", "NCR"],
            "version": "1.0.0"
        },
        "baseline_priors": {
            "mean_delay_minutes": emp_means.get("mean_delay_minutes", 116.38),
            "median_delay_minutes": emp_means.get("median_delay_minutes", 120.0),
            "p90_delay_minutes": emp_means.get("p90_delay_minutes", 180.0),
            "mean_congestion_index": emp_means.get("mean_congestion_index", 0.91),
            "mean_fog_index": emp_means.get("mean_fog_index", 0.85)
        },
        "hourly_congestion_risk": hourly_congestion,
        "seasonal_fog_risk": seasonal_fog,
        "primary_delay_causes": delay_causes,
        "risk_multipliers": {
            "peak_hour_multiplier": 1.20,
            "night_departure_multiplier": 1.05,
            "hdn_route_multiplier": 1.15,
            "late_rake_multiplier": 1.35,
            "special_train_multiplier": 1.10
        },
        "speed_impact_thresholds": {
            "HIGH_CONGESTION": {
                "probability_threshold": 0.70,
                "restriction_speed_kmph": 25.0,
                "level": "HIGH"
            },
            "MEDIUM_CONGESTION": {
                "probability_threshold": 0.45,
                "restriction_speed_kmph": 60.0,
                "level": "MEDIUM"
            },
            "FOG_RESTRICTION": {
                "probability_threshold": 0.40,
                "restriction_speed_kmph": 40.0,
                "level": "MEDIUM"
            }
        }
    }

    out_path = Path(output_config_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(calibration_config, f, indent=2)

    print(f"[Calibration] Calibration configuration successfully written to: {output_config_path}")
    return calibration_config


if __name__ == "__main__":
    config = build_historical_calibration()
    print("\n" + "=" * 80)
    print("STEP 3: HISTORICAL CALIBRATION CONFIGURATION BUILT")
    print("=" * 80)
    print(f"Corridor Focus              : {config['metadata']['corridor']}")
    print(f"Primary Zones               : {config['metadata']['primary_zones']}")
    print(f"Baseline Mean Delay         : {config['baseline_priors']['mean_delay_minutes']} min")
    print(f"HIGH_CONGESTION Speed Cap   : {config['speed_impact_thresholds']['HIGH_CONGESTION']['restriction_speed_kmph']} km/h")
    print(f"FOG_RESTRICTION Speed Cap   : {config['speed_impact_thresholds']['FOG_RESTRICTION']['restriction_speed_kmph']} km/h")
    print("=" * 80)
