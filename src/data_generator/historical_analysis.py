"""
historical_analysis.py — Phase 6: Step 2
Extracts empirical conditional probability distributions from ir_train.csv for NR & NCR zones.
Computes risk priors for:
- Hourly congestion risk (0-23 hours)
- Seasonal fog probability
- Delay severity distribution by zone and season
- Operational disruption priors
"""

import os
import json
from pathlib import Path
from typing import Dict, Any
import pandas as pd
import numpy as np


def analyze_historical_priors(
    csv_path: str = r"D:\Projects\railway\indian-railways-predict-train-delay\ir_train.csv",
    output_analysis_path: str = r"D:\Projects\railway\reports\historical_analysis_summary.json"
) -> Dict[str, Any]:
    """
    Reads ir_train.csv, filters for Northern corridors (NR & NCR), and computes conditional risk distributions.
    """
    print(f"[HistoricalAnalysis] Reading dataset from: {csv_path}")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found at: {csv_path}")

    use_cols = [
        "journey_id", "zone_abbr", "season", "departure_hour", "is_peak_hour",
        "is_fog_risk", "fog_risk_score", "zone_fog_index", "zone_congestion_index",
        "season_severity_score", "delay_minutes", "is_delayed", "primary_delay_cause"
    ]

    df = pd.read_csv(csv_path, usecols=use_cols)
    print(f"[HistoricalAnalysis] Successfully loaded {len(df):,} records.")

    # 1. Filter for Northern Zone (NR) & North Central Zone (NCR)
    nr_df = df[df["zone_abbr"].isin(["NR", "NCR"])]
    if len(nr_df) == 0:
        nr_df = df  # fallback if zone filter is empty
    print(f"[HistoricalAnalysis] Filtered {len(nr_df):,} records for NR & NCR zones.")

    # 2. Hourly Congestion Probabilities (Normalized 0.0 to 1.0)
    hourly_congestion = {}
    for hr in range(24):
        hr_df = nr_df[nr_df["departure_hour"] == hr]
        if len(hr_df) > 0:
            avg_cong = float(hr_df["zone_congestion_index"].mean())
            is_peak = int(hr_df["is_peak_hour"].mode()[0]) if not hr_df["is_peak_hour"].empty else 0
            prob = min(1.0, max(0.0, avg_cong * (1.2 if is_peak else 0.85)))
            hourly_congestion[str(hr)] = round(prob, 4)
        else:
            hourly_congestion[str(hr)] = 0.50

    # 3. Seasonal Fog Probabilities
    seasonal_fog = {}
    for season_name, grp in nr_df.groupby("season"):
        fog_prob = float(grp["is_fog_risk"].mean())
        mean_fog_idx = float(grp["zone_fog_index"].mean())
        combined_fog_risk = min(1.0, max(0.0, fog_prob * 0.6 + mean_fog_idx * 0.4))
        seasonal_fog[str(season_name)] = round(combined_fog_risk, 4)

    if "Winter/Fog" in seasonal_fog:
        seasonal_fog["Winter/Fog"] = max(0.45, seasonal_fog["Winter/Fog"])

    # 4. Primary Delay Cause Frequencies in NR/NCR corridor
    delay_cause_freq = (
        nr_df["primary_delay_cause"].value_counts(normalize=True).round(4).to_dict()
    )

    # 5. Delay Severity Distribution (Categories: ON_TIME <=5m, MINOR <=15m, MODERATE <=45m, HEAVY >45m)
    def categorize_delay(d_min: float) -> str:
        if d_min <= 5:
            return "ON_TIME"
        elif d_min <= 15:
            return "MINOR_DELAY"
        elif d_min <= 45:
            return "MODERATE_DELAY"
        else:
            return "HEAVY_DELAY"

    nr_df_copy = nr_df.copy()
    nr_df_copy["delay_category"] = nr_df_copy["delay_minutes"].apply(categorize_delay)
    delay_severity_dist = (
        nr_df_copy["delay_category"].value_counts(normalize=True).round(4).to_dict()
    )

    analysis_result = {
        "corridor_focus": "NR & NCR (Northern / North Central Railway)",
        "sample_size": len(nr_df),
        "hourly_congestion_probability": hourly_congestion,
        "seasonal_fog_probability": seasonal_fog,
        "primary_delay_cause_distribution": delay_cause_freq,
        "delay_severity_distribution": delay_severity_dist,
        "empirical_means": {
            "mean_delay_minutes": round(float(nr_df["delay_minutes"].mean()), 2),
            "median_delay_minutes": round(float(nr_df["delay_minutes"].median()), 2),
            "p90_delay_minutes": round(float(nr_df["delay_minutes"].quantile(0.90)), 2),
            "mean_congestion_index": round(float(nr_df["zone_congestion_index"].mean()), 3),
            "mean_fog_index": round(float(nr_df["zone_fog_index"].mean()), 3)
        }
    }

    out_path = Path(output_analysis_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(analysis_result, f, indent=2)

    print(f"[HistoricalAnalysis] Summary saved to: {output_analysis_path}")
    return analysis_result


if __name__ == "__main__":
    summary = analyze_historical_priors()
    emp = summary["empirical_means"]

    print("\n" + "=" * 85)
    print("STEP 2: HISTORICAL ANALYSIS SUMMARY (NR & NCR CORRIDORS)")
    print("=" * 85)
    print(f"Sample Size (NR/NCR records) : {summary['sample_size']:,}")
    print(f"Empirical Mean Delay          : {emp['mean_delay_minutes']} min (Median: {emp['median_delay_minutes']} min)")
    print(f"90th Percentile Delay (P90)   : {emp['p90_delay_minutes']} min")
    print("-" * 85)
    print("TOP DELAY CAUSES (NR/NCR):")
    for cause, pct in summary["primary_delay_cause_distribution"].items():
        print(f"  - {cause:<30}: {pct * 100:.1f}%")
    print("-" * 85)
    print("SEASONAL FOG RISK PROBABILITIES:")
    for season, prob in summary["seasonal_fog_probability"].items():
        print(f"  - {season:<30}: {prob * 100:.1f}%")
    print("=" * 85)
