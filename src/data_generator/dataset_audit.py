"""
dataset_audit.py — Phase 6: Step 1
Audits the 1.5M historical Indian Railways dataset (ir_train.csv).
Extracts national and zone-specific empirical priors for delay, congestion, fog, and seasonal severity.
Specialized focus on Northern Railway (NR) and North Central Railway (NCR).
"""

import os
import json
from pathlib import Path
from typing import Dict, Any
import pandas as pd
import numpy as np


def run_dataset_audit(
    csv_path: str = r"D:\Projects\railway\indian-railways-predict-train-delay\ir_train.csv",
    output_report_path: str = r"D:\Projects\railway\reports\dataset_audit_report.json"
) -> Dict[str, Any]:
    """
    Analyzes the 1.5M dataset across all zones, highlighting NR & NCR, and saves a calibration summary.
    """
    print(f"[DatasetAudit] Loading historical dataset from: {csv_path}")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found at: {csv_path}")

    use_cols = [
        # Target / Identifiers
        "journey_id", "train_type", "zone_abbr", "delay_minutes", "is_delayed", "primary_delay_cause",
        
        # 1. Time Factors
        "departure_hour", "is_peak_hour", "season", "is_festival_season", "is_night_departure",
        
        # 2. Network Factors
        "distance_km", "num_scheduled_stops", "track_doubled", "psr_count", "is_hdn_route",
        
        # 3. Weather Factors
        "is_fog_risk", "fog_risk_score", "zone_fog_index", "season_severity_score",
        
        # 4. Congestion Factors
        "zone_congestion_index",
        
        # 5. Operational Factors
        "late_incoming_rake", "maintenance_score", "is_rake_shared", "is_special_train", "route_historical_ontime_pct"
    ]


    df = pd.read_csv(csv_path, usecols=use_cols)
    total_records = len(df)
    print(f"[DatasetAudit] Successfully loaded {total_records:,} historical records.")

    # 1. National Overview (All-India Baseline)
    national_stats = {
        "total_records": total_records,
        "overall_on_time_pct": round(float((df["is_delayed"] == 0).mean() * 100), 2),
        "median_delay_min": round(float(df["delay_minutes"].median()), 2),
        "mean_delay_min": round(float(df["delay_minutes"].mean()), 2),
        "p90_delay_min": round(float(df["delay_minutes"].quantile(0.90)), 2),
        "fog_risk_probability": round(float(df["is_fog_risk"].mean()), 4),
        "peak_hour_delay_ratio": round(
            float(df[df["is_peak_hour"] == 1]["delay_minutes"].mean() /
                  max(1.0, df[df["is_peak_hour"] == 0]["delay_minutes"].mean())), 2
        )
    }

    # 2. Zone-by-Zone Profiling
    zone_profiles: Dict[str, Any] = {}
    unique_zones = sorted(df["zone_abbr"].dropna().unique().tolist())

    for zone in unique_zones:
        z_df = df[df["zone_abbr"] == zone]
        if len(z_df) < 500:
            continue

        late_rake_df = z_df[z_df["late_incoming_rake"] == 1]
        hdn_df = z_df[z_df["is_hdn_route"] == 1]
        fest_df = z_df[z_df["is_festival_season"] == 1]

        zone_profiles[zone] = {
            "record_count": len(z_df),
            "on_time_pct": round(float((z_df["is_delayed"] == 0).mean() * 100), 2),
            "median_delay_min": round(float(z_df["delay_minutes"].median()), 2),
            "mean_delay_min": round(float(z_df["delay_minutes"].mean()), 2),
            "p90_delay_min": round(float(z_df["delay_minutes"].quantile(0.90)), 2),
            "fog_risk_probability": round(float(z_df["is_fog_risk"].mean()), 4),
            "mean_zone_fog_index": round(float(z_df["zone_fog_index"].mean()), 3),
            "mean_zone_congestion_index": round(float(z_df["zone_congestion_index"].mean()), 3),
            "late_rake_mean_delay": round(float(late_rake_df["delay_minutes"].mean()), 2) if len(late_rake_df) > 0 else 0.0,
            "hdn_route_mean_delay": round(float(hdn_df["delay_minutes"].mean()), 2) if len(hdn_df) > 0 else 0.0,
            "festival_season_mean_delay": round(float(fest_df["delay_minutes"].mean()), 2) if len(fest_df) > 0 else 0.0,
            "top_delay_causes": z_df["primary_delay_cause"].value_counts().head(3).to_dict()
        }
            # 3. Time Factors Analysis
    time_factors = {
        "peak_hour_mean_delay": round(float(df[df["is_peak_hour"] == 1]["delay_minutes"].mean()), 2),
        "non_peak_hour_mean_delay": round(float(df[df["is_peak_hour"] == 0]["delay_minutes"].mean()), 2),
        "festival_season_mean_delay": round(float(df[df["is_festival_season"] == 1]["delay_minutes"].mean()), 2),
        "night_departure_mean_delay": round(float(df[df["is_night_departure"] == 1]["delay_minutes"].mean()), 2),
        "hourly_delay_multipliers": (df.groupby("departure_hour")["delay_minutes"].mean() / df["delay_minutes"].mean()).round(3).to_dict(),
        "seasonal_delay_multipliers": (df.groupby("season")["delay_minutes"].mean() / df["delay_minutes"].mean()).round(3).to_dict()
    }

    # 4. Network Factors Analysis
    network_factors = {
        "hdn_route_mean_delay": round(float(df[df["is_hdn_route"] == 1]["delay_minutes"].mean()), 2),
        "non_hdn_route_mean_delay": round(float(df[df["is_hdn_route"] == 0]["delay_minutes"].mean()), 2),
        "double_track_mean_delay": round(float(df[df["track_doubled"] == 1]["delay_minutes"].mean()), 2),
        "single_track_mean_delay": round(float(df[df["track_doubled"] == 0]["delay_minutes"].mean()), 2),
        "avg_psr_count": round(float(df["psr_count"].mean()), 2)
    }

    # 5. Weather Factors Analysis
    weather_factors = {
        "fog_risk_probability": round(float(df["is_fog_risk"].mean()), 4),
        "mean_fog_risk_score": round(float(df["fog_risk_score"].mean()), 3),
        "mean_zone_fog_index": round(float(df["zone_fog_index"].mean()), 3),
        "mean_season_severity_score": round(float(df["season_severity_score"].mean()), 3)
    }

    # 6. Congestion Factors Analysis
    congestion_factors = {
        "mean_zone_congestion_index": round(float(df["zone_congestion_index"].mean()), 3),
        "high_congestion_mean_delay": round(float(df[df["zone_congestion_index"] > 0.8]["delay_minutes"].mean()), 2)
    }

    # 7. Operational Factors Analysis
    operations_factors = {
        "late_incoming_rake_mean_delay": round(float(df[df["late_incoming_rake"] == 1]["delay_minutes"].mean()), 2),
        "on_time_incoming_rake_mean_delay": round(float(df[df["late_incoming_rake"] == 0]["delay_minutes"].mean()), 2),
        "special_train_mean_delay": round(float(df[df["is_special_train"] == 1]["delay_minutes"].mean()), 2),
        "regular_train_mean_delay": round(float(df[df["is_special_train"] == 0]["delay_minutes"].mean()), 2),
        "train_type_delay_profile": df.groupby("train_type")["delay_minutes"].mean().round(2).to_dict()
    }

    # 3. Time-of-Day Congestion Profile (Hourly multipliers 0-23)
    hourly_congestion = (
        df.groupby("departure_hour")["delay_minutes"].mean() / df["delay_minutes"].mean()
    ).round(3).to_dict()

    # 4. Seasonal Severity Factors
    season_multipliers = (
        df.groupby("season")["delay_minutes"].mean() / df["delay_minutes"].mean()
    ).round(3).to_dict()

    # Compile comprehensive report
    report = {
        "dataset_name": "Indian Railways Historical Delay Dataset (1.5M)",
        "national_baseline": national_stats,
        "primary_focus_zones": ["NR", "NCR"],
        "time_factors": time_factors,
        "network_factors": network_factors,
        "weather_factors": weather_factors,
        "congestion_factors": congestion_factors,
        "operational_factors": operations_factors,
        "total_zones_analyzed": len(zone_profiles),
        "zone_profiles": zone_profiles
    }


    report_path = Path(output_report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[DatasetAudit] Audit report saved to: {output_report_path}")
    return report


if __name__ == "__main__":
    report = run_dataset_audit()
    nat = report["national_baseline"]
    zp = report["zone_profiles"]
    tf = report["time_factors"]
    nf = report["network_factors"]
    of = report["operational_factors"]

    nr = zp.get("NR", {})
    ncr = zp.get("NCR", {})

    print("\n" + "=" * 90)
    print("COMPREHENSIVE DATASET AUDIT: NATIONAL BASELINE vs NR & NCR ZONES")
    print("=" * 90)
    print(f"{'Metric / Operational Factor':<35} | {'ALL_INDIA':<15} | {'NR (Northern)':<16} | {'NCR (North Central)'}")
    print("-" * 90)
    print(f"{'Record Count':<35} | {nat['total_records']:>15,} | {nr.get('record_count', 0):>16,} | {ncr.get('record_count', 0):>16,}")
    print(f"{'On-Time Rate (%)':<35} | {nat['overall_on_time_pct']:>14.1f}% | {nr.get('on_time_pct', 0):>15.1f}% | {ncr.get('on_time_pct', 0):>15.1f}%")
    print(f"{'Mean Delay (min)':<35} | {nat['mean_delay_min']:>15.1f} | {nr.get('mean_delay_min', 0):>16.1f} | {ncr.get('mean_delay_min', 0):>16.1f}")
    print(f"{'Median Delay (min)':<35} | {nat['median_delay_min']:>15.1f} | {nr.get('median_delay_min', 0):>16.1f} | {ncr.get('median_delay_min', 0):>16.1f}")
    print(f"{'P90 Delay (min)':<35} | {nat['p90_delay_min']:>15.1f} | {nr.get('p90_delay_min', 0):>16.1f} | {ncr.get('p90_delay_min', 0):>16.1f}")
    print("-" * 90)
    print("OPERATIONAL & WEATHER COMPARISONS:")
    print(f"{'Fog Risk Probability (%)':<35} | {nat['fog_risk_probability']*100:>14.2f}% | {nr.get('fog_risk_probability', 0)*100:>15.2f}% | {ncr.get('fog_risk_probability', 0)*100:>15.2f}%")
    print(f"{'Mean Congestion Index':<35} | {'-':>15} | {nr.get('mean_zone_congestion_index', 0):>16.3f} | {ncr.get('mean_zone_congestion_index', 0):>16.3f}")
    print(f"{'Late Incoming Rake Delay (min)':<35} | {of['late_incoming_rake_mean_delay']:>15.1f} | {nr.get('late_rake_mean_delay', 0):>16.1f} | {ncr.get('late_rake_mean_delay', 0):>16.1f}")
    print(f"{'HDN Route Delay (min)':<35} | {nf['hdn_route_mean_delay']:>15.1f} | {nr.get('hdn_route_mean_delay', 0):>16.1f} | {ncr.get('hdn_route_mean_delay', 0):>16.1f}")
    print(f"{'Festival Season Delay (min)':<35} | {tf['festival_season_mean_delay']:>15.1f} | {nr.get('festival_season_mean_delay', 0):>16.1f} | {ncr.get('festival_season_mean_delay', 0):>16.1f}")
    print("=" * 90)
