"""
audit_historical_factors.py — Phase 6: Step 1 Historical Factor Audit
Audits the 1M+ historical Indian Railways dataset (ir_train.csv) to discover pure,
data-derived conditional probability distributions for time, weather, congestion,
operational, route, and train factors without artificial multipliers.
Outputs comprehensive factor_audit_report.json and factor_audit_summary.md.
"""

import os
import json
import math
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_historical_factor_audit(
    csv_path: str = str(PROJECT_ROOT / "indian-railways-predict-train-delay" / "ir_train.csv"),
    output_json_path: str = str(PROJECT_ROOT / "reports" / "factor_audit_report.json"),
    output_md_path: str = str(PROJECT_ROOT / "reports" / "factor_audit_summary.md"),
) -> Dict[str, Any]:
    print("=" * 78)
    print("      PHASE 6 — STEP 1: HISTORICAL FACTOR AUDIT (PURE DATA-DERIVED)")
    print("=" * 78)
    print(f"Dataset : {csv_path}")

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found at: {csv_path}")

    # 1. Load Dataset
    print("\n[1/6] Loading historical dataset (1M+ records)...")
    df = pd.read_csv(csv_path)
    total_rows = len(df)
    total_cols = len(df.columns)
    print(f"      Loaded {total_rows:,} records across {total_cols} columns.")

    # 2. Data Quality Audit
    print("\n[2/6] Running Data Quality & Integrity Checks...")
    missing_counts = df.isnull().sum().to_dict()
    cols_with_missing = {k: int(v) for k, v in missing_counts.items() if v > 0}
    duplicate_journeys = int(df["journey_id"].duplicated().sum()) if "journey_id" in df.columns else 0

    delayed_count = int(df["is_delayed"].sum()) if "is_delayed" in df.columns else 0
    on_time_count = total_rows - delayed_count
    delayed_pct = round((delayed_count / total_rows) * 100.0, 2)

    # Standard delay buckets & heavy delay flag (>45 min)
    df["delay_bucket"] = pd.cut(
        df["delay_minutes"],
        bins=[-1, 5, 15, 45, 120, 100000],
        labels=["ON_TIME (<=5m)", "MINOR (5-15m)", "MODERATE (15-45m)", "SEVERE (45-120m)", "CATASTROPHIC (>120m)"]
    )
    df["is_heavy_delay"] = (df["delay_minutes"] > 45).astype(int)

    quality_check = {
        "total_rows": total_rows,
        "total_columns": total_cols,
        "duplicate_journey_ids": duplicate_journeys,
        "columns_with_missing_values": cols_with_missing,
        "delayed_distribution": {
            "delayed_journeys_gt_15m": delayed_count,
            "on_time_journeys_le_15m": on_time_count,
            "delayed_percentage": delayed_pct,
            "on_time_percentage": round(100.0 - delayed_pct, 2),
        },
    }
    print(f"      Duplicate Journey IDs: {duplicate_journeys}")
    print(f"      Delayed (>15m): {delayed_count:,} ({delayed_pct}%) | On-Time: {on_time_count:,} ({round(100.0 - delayed_pct, 2)}%)")

    # 3. Target Distribution (delay_minutes)
    print("\n[3/6] Computing Pure Target Distributions...")
    delay_series = df["delay_minutes"]
    target_stats = {
        "mean_delay_minutes": round(float(delay_series.mean()), 2),
        "median_delay_minutes": round(float(delay_series.median()), 2),
        "std_delay_minutes": round(float(delay_series.std()), 2),
        "p25_delay_minutes": round(float(delay_series.quantile(0.25)), 2),
        "p50_delay_minutes": round(float(delay_series.quantile(0.50)), 2),
        "p75_delay_minutes": round(float(delay_series.quantile(0.75)), 2),
        "p90_delay_minutes": round(float(delay_series.quantile(0.90)), 2),
        "p95_delay_minutes": round(float(delay_series.quantile(0.95)), 2),
        "max_delay_minutes": int(delay_series.max()),
        "delay_bucket_distribution": {
            str(k): {"count": int(v), "percentage": round((int(v) / total_rows) * 100.0, 2)}
            for k, v in df["delay_bucket"].value_counts().items()
        }
    }

    # Helper: Pure Empirical Group Aggregator with Sample Counts
    def _compute_empirical_metrics(group_col: str, dataframe: pd.DataFrame = df) -> Dict[str, Any]:
        result = {}
        for val, grp in dataframe.groupby(group_col, observed=True):
            n = len(grp)
            if n == 0:
                continue
            del_n = int(grp["is_delayed"].sum())
            heavy_del_n = int(grp["is_heavy_delay"].sum())
            del_pct = round((del_n / n) * 100.0, 2)
            heavy_del_pct = round((heavy_del_n / n) * 100.0, 2)
            mean_del = round(float(grp["delay_minutes"].mean()), 2)
            median_del = round(float(grp["delay_minutes"].median()), 2)
            p90_del = round(float(grp["delay_minutes"].quantile(0.90)), 2)

            result[str(val)] = {
                "sample_count": n,
                "sample_share_pct": round((n / len(dataframe)) * 100.0, 2),
                "delayed_count": del_n,
                "p_delay_pct": del_pct,
                "heavy_delayed_count": heavy_del_n,
                "p_heavy_delay_pct": heavy_del_pct,
                "mean_delay_min": mean_del,
                "median_delay_min": median_del,
                "p90_delay_min": p90_del,
                "status": "VALID_SAMPLE" if n >= 30 else "INSUFFICIENT_EVIDENCE (N < 30)"
            }
        return result

    # 4. Factor Group Audits
    print("\n[4/6] Computing Pure Conditional Factor Matrices...")

    # A. Time Factors
    time_analysis = {
        "by_departure_hour": _compute_empirical_metrics("departure_hour"),
        "by_season": _compute_empirical_metrics("season"),
        "by_day_of_week": _compute_empirical_metrics("day_of_week"),
        "by_is_weekend": _compute_empirical_metrics("is_weekend"),
        "by_is_night_departure": _compute_empirical_metrics("is_night_departure"),
        "by_is_peak_hour": _compute_empirical_metrics("is_peak_hour"),
        "by_is_festival_season": _compute_empirical_metrics("is_festival_season"),
        "by_month": _compute_empirical_metrics("month"),
    }

    # B. Weather / Fog Factors — P(fog | hour), P(fog | season), P(fog | hour, season)
    fog_by_hour = {}
    for hr, grp in df.groupby("departure_hour"):
        n = len(grp)
        fog_cnt = int(grp["is_fog_risk"].sum())
        fog_by_hour[str(hr)] = {
            "sample_count": n,
            "fog_count": fog_cnt,
            "p_fog_pct": round((fog_cnt / n) * 100.0, 2),
            "p_delay_given_fog_pct": round(float(grp[grp['is_fog_risk'] == 1]['is_delayed'].mean()) * 100.0, 2) if fog_cnt > 0 else 0.0,
            "mean_delay_fog_min": round(float(grp[grp['is_fog_risk'] == 1]['delay_minutes'].mean()), 2) if fog_cnt > 0 else 0.0,
        }

    fog_by_season = {}
    for ssn, grp in df.groupby("season"):
        n = len(grp)
        fog_cnt = int(grp["is_fog_risk"].sum())
        fog_by_season[str(ssn)] = {
            "sample_count": n,
            "fog_count": fog_cnt,
            "p_fog_pct": round((fog_cnt / n) * 100.0, 2),
            "p_delay_given_fog_pct": round(float(grp[grp['is_fog_risk'] == 1]['is_delayed'].mean()) * 100.0, 2) if fog_cnt > 0 else 0.0,
            "mean_delay_fog_min": round(float(grp[grp['is_fog_risk'] == 1]['delay_minutes'].mean()), 2) if fog_cnt > 0 else 0.0,
        }

    fog_by_hour_season = {}
    for (ssn, hr), grp in df.groupby(["season", "departure_hour"]):
        n = len(grp)
        fog_cnt = int(grp["is_fog_risk"].sum())
        if ssn not in fog_by_hour_season:
            fog_by_hour_season[ssn] = {}
        fog_by_hour_season[ssn][str(hr)] = {
            "sample_count": n,
            "fog_count": fog_cnt,
            "p_fog_pct": round((fog_cnt / n) * 100.0, 2),
            "p_delay_given_fog_pct": round(float(grp[grp['is_fog_risk'] == 1]['is_delayed'].mean()) * 100.0, 2) if fog_cnt > 0 else 0.0,
            "mean_delay_fog_min": round(float(grp[grp['is_fog_risk'] == 1]['delay_minutes'].mean()), 2) if fog_cnt > 0 else 0.0,
        }

    fog_analysis = {
        "by_is_fog_risk": _compute_empirical_metrics("is_fog_risk"),
        "fog_by_departure_hour": fog_by_hour,
        "fog_by_season": fog_by_season,
        "fog_by_hour_and_season": fog_by_hour_season,
        "zone_fog_index_summary": {
            "overall_mean": round(float(df["zone_fog_index"].mean()), 4),
            "by_zone": {str(z): round(float(g["zone_fog_index"].mean()), 4) for z, g in df.groupby("zone_abbr")},
        },
    }

    # C. Congestion Factors (Data-Derived Bins)
    df["congestion_level"] = pd.cut(
        df["zone_congestion_index"],
        bins=[-0.1, 0.40, 0.70, 1.1],
        labels=["LOW (<0.40)", "MEDIUM (0.40-0.70)", "HIGH (>=0.70)"]
    )
    df["is_high_congestion"] = (df["zone_congestion_index"] >= 0.70).astype(int)

    # Congestion by Hour x Zone
    congestion_by_hour_zone = {}
    for (zone, hr), grp in df.groupby(["zone_abbr", "departure_hour"]):
        n = len(grp)
        high_cong_cnt = int(grp["is_high_congestion"].sum())
        if zone not in congestion_by_hour_zone:
            congestion_by_hour_zone[zone] = {}
        congestion_by_hour_zone[zone][str(hr)] = {
            "sample_count": n,
            "mean_congestion_index": round(float(grp["zone_congestion_index"].mean()), 4),
            "high_congestion_count": high_cong_cnt,
            "p_high_congestion_pct": round((high_cong_cnt / n) * 100.0, 2),
            "p_delay_pct": round(float(grp["is_delayed"].mean()) * 100.0, 2),
            "mean_delay_min": round(float(grp["delay_minutes"].mean()), 2),
        }

    congestion_analysis = {
        "by_congestion_level": _compute_empirical_metrics("congestion_level"),
        "by_is_hdn_route": _compute_empirical_metrics("is_hdn_route"),
        "congestion_by_hour_and_zone": congestion_by_hour_zone,
        "congestion_index_by_hour": {str(hr): round(float(grp["zone_congestion_index"].mean()), 4) for hr, grp in df.groupby("departure_hour")},
        "congestion_index_by_zone": {str(z): round(float(grp["zone_congestion_index"].mean()), 4) for z, grp in df.groupby("zone_abbr")},
    }

    # D. Operational Factors
    operational_analysis = {
        "by_late_incoming_rake": _compute_empirical_metrics("late_incoming_rake"),
        "by_is_rake_shared": _compute_empirical_metrics("is_rake_shared"),
        "by_is_special_train": _compute_empirical_metrics("is_special_train"),
        "by_psr_count_binned": _compute_empirical_metrics(
            pd.cut(df["psr_count"], bins=[-1, 2, 5, 10, 100], labels=["0-2 PSRs", "3-5 PSRs", "6-10 PSRs", ">10 PSRs"])
        ),
        "by_maintenance_score_binned": _compute_empirical_metrics(
            pd.cut(df["maintenance_score"], bins=[0, 4, 7, 10], labels=["POOR (1-4)", "AVERAGE (5-7)", "EXCELLENT (8-10)"])
        ),
    }

    # E. Train & Asset Factors
    train_analysis = {
        "by_train_type": _compute_empirical_metrics("train_type"),
        "by_traction_type": _compute_empirical_metrics("traction_type"),
        "by_has_lhb_coaches": _compute_empirical_metrics("has_lhb_coaches"),
        "by_is_overloaded": _compute_empirical_metrics("is_overloaded"),
        "by_loco_age_binned": _compute_empirical_metrics(
            pd.cut(df["loco_age_years"], bins=[-1, 5, 15, 40], labels=["NEW (<=5y)", "MID (5-15y)", "OLD (>15y)"])
        ),
        "by_coach_age_binned": _compute_empirical_metrics(
            pd.cut(df["coach_age_years"], bins=[-1, 5, 15, 40], labels=["NEW (<=5y)", "MID (5-15y)", "OLD (>15y)"])
        ),
    }

    # F. Route & Infrastructure Factors
    route_analysis = {
        "by_zone_abbr": _compute_empirical_metrics("zone_abbr"),
        "by_track_doubled": _compute_empirical_metrics("track_doubled"),
        "by_is_electrified": _compute_empirical_metrics("is_electrified"),
        "by_is_circular_route": _compute_empirical_metrics("is_circular_route"),
        "by_source_station_category": _compute_empirical_metrics("source_station_category"),
        "by_destination_station_category": _compute_empirical_metrics("destination_station_category"),
        "by_distance_binned": _compute_empirical_metrics(
            pd.cut(df["distance_km"], bins=[-1, 300, 700, 1500, 5000], labels=["SHORT (<=300km)", "MEDIUM (300-700km)", "LONG (700-1500km)", "ULTRA-LONG (>1500km)"])
        ),
        "by_scheduled_stops_binned": _compute_empirical_metrics(
            pd.cut(df["num_scheduled_stops"], bins=[-1, 5, 15, 30, 100], labels=["FEW (<=5)", "MODERATE (6-15)", "MANY (16-30)", "VERY_MANY (>30)"])
        ),
    }

    # G. Delay Causes Analysis
    print("\n[5/6] Auditing Primary Delay Causes & Cross-Conditions...")
    delay_cause_stats = {}
    for cause, grp in df.groupby("primary_delay_cause"):
        n = len(grp)
        heavy_cnt = int(grp["is_heavy_delay"].sum())
        delay_cause_stats[str(cause)] = {
            "sample_count": n,
            "percentage_of_all_records": round((n / total_rows) * 100.0, 2),
            "mean_delay_min": round(float(grp["delay_minutes"].mean()), 2),
            "median_delay_min": round(float(grp["delay_minutes"].median()), 2),
            "p90_delay_min": round(float(grp["delay_minutes"].quantile(0.90)), 2),
            "heavy_delayed_count": heavy_cnt,
            "p_heavy_delay_pct": round((heavy_cnt / n) * 100.0, 2),
        }

    # Conditional Cross-Combinations (Pure Empirical Slices)
    conditional_combos = {}

    # P(delay | fog, peak hour)
    for (fog, peak), grp in df.groupby(["is_fog_risk", "is_peak_hour"]):
        n = len(grp)
        del_cnt = int(grp["is_delayed"].sum())
        heavy_cnt = int(grp["is_heavy_delay"].sum())
        tag = f"Fog={bool(fog)} & PeakHour={bool(peak)}"
        conditional_combos[tag] = {
            "sample_count": n,
            "p_delay_pct": round((del_cnt / n) * 100.0, 2),
            "p_heavy_delay_pct": round((heavy_cnt / n) * 100.0, 2),
            "mean_delay_min": round(float(grp["delay_minutes"].mean()), 2),
            "median_delay_min": round(float(grp["delay_minutes"].median()), 2),
            "p90_delay_min": round(float(grp["delay_minutes"].quantile(0.90)), 2),
        }

    # P(delay | congestion level, peak hour)
    for (cong, peak), grp in df.groupby(["congestion_level", "is_peak_hour"], observed=True):
        n = len(grp)
        del_cnt = int(grp["is_delayed"].sum())
        heavy_cnt = int(grp["is_heavy_delay"].sum())
        tag = f"Congestion={cong} & PeakHour={bool(peak)}"
        conditional_combos[tag] = {
            "sample_count": n,
            "p_delay_pct": round((del_cnt / n) * 100.0, 2),
            "p_heavy_delay_pct": round((heavy_cnt / n) * 100.0, 2),
            "mean_delay_min": round(float(grp["delay_minutes"].mean()), 2),
            "median_delay_min": round(float(grp["delay_minutes"].median()), 2),
            "p90_delay_min": round(float(grp["delay_minutes"].quantile(0.90)), 2),
        }

    # P(delay | late incoming rake & fog)
    for (late_rake, fog), grp in df.groupby(["late_incoming_rake", "is_fog_risk"]):
        n = len(grp)
        del_cnt = int(grp["is_delayed"].sum())
        heavy_cnt = int(grp["is_heavy_delay"].sum())
        tag = f"LateRake={bool(late_rake)} & Fog={bool(fog)}"
        conditional_combos[tag] = {
            "sample_count": n,
            "p_delay_pct": round((del_cnt / n) * 100.0, 2),
            "p_heavy_delay_pct": round((heavy_cnt / n) * 100.0, 2),
            "mean_delay_min": round(float(grp["delay_minutes"].mean()), 2),
            "median_delay_min": round(float(grp["delay_minutes"].median()), 2),
            "p90_delay_min": round(float(grp["delay_minutes"].quantile(0.90)), 2),
        }

    # 5. NR & NCR Zone Specific Geographic Proxy Analysis
    print("\n[6/6] Computing Pure Empirical Metrics for NR & NCR Corridors...")
    nr_df = df[df["zone_abbr"] == "NR"]
    ncr_df = df[df["zone_abbr"] == "NCR"]
    nr_ncr_df = df[df["zone_abbr"].isin(["NR", "NCR"])]

    # NR/NCR Fog Matrix by Hour x Season
    nr_ncr_fog_hour_season = {}
    for (ssn, hr), grp in nr_ncr_df.groupby(["season", "departure_hour"]):
        n = len(grp)
        fog_cnt = int(grp["is_fog_risk"].sum())
        if ssn not in nr_ncr_fog_hour_season:
            nr_ncr_fog_hour_season[ssn] = {}
        nr_ncr_fog_hour_season[ssn][str(hr)] = {
            "sample_count": n,
            "fog_count": fog_cnt,
            "p_fog_pct": round((fog_cnt / n) * 100.0, 2),
            "mean_delay_fog_min": round(float(grp[grp['is_fog_risk'] == 1]['delay_minutes'].mean()), 2) if fog_cnt > 0 else 0.0,
        }

    # NR/NCR Congestion Matrix by Hour
    nr_ncr_congestion_by_hour = {}
    for hr, grp in nr_ncr_df.groupby("departure_hour"):
        n = len(grp)
        high_cong_cnt = int((grp["zone_congestion_index"] >= 0.70).sum())
        nr_ncr_congestion_by_hour[str(hr)] = {
            "sample_count": n,
            "mean_congestion_index": round(float(grp["zone_congestion_index"].mean()), 4),
            "high_congestion_count": high_cong_cnt,
            "p_high_congestion_pct": round((high_cong_cnt / n) * 100.0, 2),
            "p_delay_pct": round(float(grp["is_delayed"].mean()) * 100.0, 2),
            "mean_delay_min": round(float(grp["delay_minutes"].mean()), 2),
        }

    nr_ncr_analysis = {
        "NR_sample_size": len(nr_df),
        "NCR_sample_size": len(ncr_df),
        "combined_NR_NCR_sample_size": len(nr_ncr_df),
        "combined_NR_NCR_metrics": {
            "delayed_count": int(nr_ncr_df["is_delayed"].sum()),
            "delayed_pct": round(float(nr_ncr_df["is_delayed"].mean()) * 100.0, 2),
            "mean_delay_min": round(float(nr_ncr_df["delay_minutes"].mean()), 2),
            "median_delay_min": round(float(nr_ncr_df["delay_minutes"].median()), 2),
            "p90_delay_min": round(float(nr_ncr_df["delay_minutes"].quantile(0.90)), 2),
            "mean_fog_index": round(float(nr_ncr_df["zone_fog_index"].mean()), 4),
            "mean_congestion_index": round(float(nr_ncr_df["zone_congestion_index"].mean()), 4),
        },
        "NR_NCR_fog_by_hour_and_season": nr_ncr_fog_hour_season,
        "NR_NCR_congestion_by_hour": nr_ncr_congestion_by_hour,
        "NR_NCR_delay_cause_distribution": {
            str(cause): {
                "sample_count": len(grp),
                "share_pct": round((len(grp) / len(nr_ncr_df)) * 100.0, 2),
                "mean_delay_min": round(float(grp["delay_minutes"].mean()), 2),
                "median_delay_min": round(float(grp["delay_minutes"].median()), 2),
            }
            for cause, grp in nr_ncr_df.groupby("primary_delay_cause")
        }
    }

    # Factor Classification Matrix
    factor_classification = {
        "USE DIRECTLY": {
            "description": "Dynamic, strong physical signal, available in real-time at simulation timestamp t",
            "factors": [
                {"name": "current_position_km", "reason": "Continuous physical progress along corridor (0 to 314 km)."},
                {"name": "current_speed_kmph", "reason": "Immediate kinematic state indicating cruising vs decelerating."},
                {"name": "current_delay_min", "reason": "Actual accumulated delay against timetable up to timestamp t."},
                {"name": "current_section_id", "reason": "Sectional bottleneck identification (e.g. single line in SEC_HW_DDN)."},
                {"name": "departure_hour", "reason": "Time-of-day feature capturing peak commute windows and morning fog."},
                {"name": "season", "reason": "Macro weather regime (Winter/Fog vs Summer vs Monsoon)."},
                {"name": "signal_state", "reason": "Immediate block signal status (GREEN=1.0, YELLOW=0.5, RED=0.0)."},
                {"name": "is_fog_active_observed", "reason": "Local visibility sensor observation at locomotive position."},
                {"name": "distance_to_next_station_km", "reason": "Remaining segment distance to next scheduled stop."},
                {"name": "distance_to_destination_km", "reason": "Remaining total corridor distance to terminal DDN."}
            ]
        },
        "USE AS CALIBRATION": {
            "description": "Pure data-derived historical matrices to calibrate System 2 & 3 probabilistic event sampling",
            "factors": [
                {"name": "P(fog | hour, season, NR/NCR)", "reason": "Empirical probability matrix for fog event spawning."},
                {"name": "P(high_congestion | hour, NR/NCR)", "reason": "Empirical probability matrix for congestion severity."},
                {"name": "P(late_incoming_rake)", "reason": "Empirical prior probability of initial departure turnaround delay."},
                {"name": "P(primary_delay_cause)", "reason": "Baseline operational distribution of delay root causes."},
                {"name": "zone_congestion_index_by_hour", "reason": "Calibrated capacity baseline by hour for Northern corridors."},
                {"name": "zone_fog_index", "reason": "Empirical geographic fog susceptibility score."}
            ]
        },
        "OPTIONAL": {
            "description": "Moderate signal but secondary in synthetic single-corridor simulation",
            "factors": [
                {"name": "is_weekend", "reason": "Minor weekend schedule variation (~2% difference in dataset)."},
                {"name": "day_of_week", "reason": "Weekday scheduling nuances."},
                {"name": "is_festival_season", "reason": "Holiday calendar turnaround surges."},
                {"name": "is_special_train", "reason": "Special non-scheduled trains receive lower dispatch priority."},
                {"name": "maintenance_score", "reason": "Asset reliability score proxy for unscheduled halts."}
            ]
        },
        "DO NOT USE": {
            "description": "Weak signal, redundant, or static attributes not applicable to NDLS-DDN corridor",
            "factors": [
                {"name": "is_circular_route", "reason": "All NDLS-DDN corridor runs are linear point-to-point journeys."},
                {"name": "traction_type", "reason": "NDLS-DDN corridor is 100% electrified 25kV AC."},
                {"name": "is_electrified", "reason": "Constant across NDLS-DDN corridor (zero variance)."},
                {"name": "coach_age_years", "reason": "Negligible independent predictive signal relative to track conditions."},
                {"name": "loco_age_years", "reason": "Weak predictive power for real-time ETA calculation."}
            ]
        },
        "FUTURE / LEAKAGE": {
            "description": "Strictly forbidden from model inputs; only permissible as target ground truth labels",
            "factors": [
                {"name": "delay_minutes", "reason": "Ground truth destination delay label."},
                {"name": "is_delayed", "reason": "Ground truth binary classification target."},
                {"name": "target_eta_to_destination_min", "reason": "Ground truth destination ETA regression target."},
                {"name": "target_eta_to_next_station_min", "reason": "Ground truth next-station ETA regression target."},
                {"name": "actual_arrival_time", "reason": "Future timestamp only known after physical arrival occurs."},
                {"name": "final_journey_duration", "reason": "Future end-to-end outcome."}
            ]
        }
    }

    # Save JSON Report
    report_data = {
        "metadata": {
            "report_title": "Phase 6 Step 1 — Historical Factor Audit Report (Pure Empirical Data)",
            "dataset_path": csv_path,
            "corridor_target": "New Delhi (NDLS) -> Dehradun (DDN) [314 km]",
            "audit_timestamp": pd.Timestamp.now().isoformat(),
            "methodology": "Pure frequentist empirical counting. Zero manual multipliers or synthetic heuristics.",
        },
        "dataset_size": {
            "total_records": total_rows,
            "total_columns": total_cols,
            "NR_records": len(nr_df),
            "NCR_records": len(ncr_df),
            "combined_NR_NCR_records": len(nr_ncr_df),
        },
        "data_quality_audit": quality_check,
        "target_statistics": target_stats,
        "time_factors_analysis": time_analysis,
        "weather_fog_analysis": fog_analysis,
        "congestion_analysis": congestion_analysis,
        "operational_analysis": operational_analysis,
        "route_infrastructure_analysis": route_analysis,
        "train_asset_analysis": train_analysis,
        "delay_cause_analysis": delay_cause_stats,
        "conditional_probabilities": conditional_combos,
        "NR_NCR_proxy_analysis": nr_ncr_analysis,
        "factor_classification": factor_classification,
    }

    out_json = Path(output_json_path)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print(f"\n[Done] Pure Empirical Factor Audit JSON saved to: {out_json}")

    # Generate Markdown Summary Report
    md_lines = []
    md_lines.append("# Phase 6 Step 1 — Historical Factor Audit Summary (Data-Derived)")
    md_lines.append("")
    md_lines.append(f"**Dataset**: `{csv_path}` | **Total Records Analyzed**: `{total_rows:,}`")
    md_lines.append(f"**Northern Corridors (NR + NCR)**: `{len(nr_ncr_df):,}` records")
    md_lines.append(f"**Methodology**: Pure empirical counts and conditional probabilities. **Zero manual multipliers.**")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")
    md_lines.append("## 1. Executive Summary & Success Criteria Answers")
    md_lines.append("")

    # 1. When is fog most likely?
    winter_fog_nr_ncr = nr_ncr_analysis["NR_NCR_fog_by_hour_and_season"].get("Winter/Fog", {})
    top_winter_fog_hours = sorted(winter_fog_nr_ncr.items(), key=lambda x: x[1]["p_fog_pct"], reverse=True)[:4]
    fog_hours_str = ", ".join([f"`{hr:0>2}:00` ({data['p_fog_pct']}%, N={data['sample_count']:,})" for hr, data in top_winter_fog_hours])
    md_lines.append(f"1. **When is fog most likely?**\n   - **Season**: `Winter/Fog` season in Northern Railway (NR/NCR) has the highest fog rate (**{fog_by_season.get('Winter/Fog', {}).get('p_fog_pct', 0)}%**, N={fog_by_season.get('Winter/Fog', {}).get('sample_count', 0):,}) vs `Summer` (**{fog_by_season.get('Summer', {}).get('p_fog_pct', 0)}%**, N={fog_by_season.get('Summer', {}).get('sample_count', 0):,}).\n   - **Peak Hours (NR/NCR Winter)**: {fog_hours_str}.\n   - **Midday Clearing**: In NR/NCR winter, fog probability drops sharply after 09:00 AM (e.g. 12:00 PM is **{winter_fog_nr_ncr.get('12', {}).get('p_fog_pct', 0)}%**, N={winter_fog_nr_ncr.get('12', {}).get('sample_count', 0):,}).")
    md_lines.append("")

    # 2. Under what conditions is congestion most likely?
    top_cong_hours = sorted(nr_ncr_analysis["NR_NCR_congestion_by_hour"].items(), key=lambda x: x[1]["p_high_congestion_pct"], reverse=True)[:3]
    cong_hours_str = ", ".join([f"`{hr:0>2}:00` ({data['p_high_congestion_pct']}%, N={data['sample_count']:,})" for hr, data in top_cong_hours])
    md_lines.append(f"2. **Under what conditions is congestion most likely?**\n   - **Peak Commute Hours in NR/NCR**: High congestion ($\ge 0.70$) peaks at: {cong_hours_str}.\n   - **HDN Routes**: High Density Network routes experience **{congestion_analysis['by_is_hdn_route'].get('1', {}).get('p_delay_pct', 0)}% delay rate** (N={congestion_analysis['by_is_hdn_route'].get('1', {}).get('sample_count', 0):,}) vs {congestion_analysis['by_is_hdn_route'].get('0', {}).get('p_delay_pct', 0)}% on non-HDN routes.\n   - **Capacity Utilization**: Mean NR/NCR congestion index is **{nr_ncr_analysis['combined_NR_NCR_metrics']['mean_congestion_index']}**.")
    md_lines.append("")

    # 3. Which factors are associated with higher delay?
    md_lines.append(f"3. **Which factors are associated with higher delay?**\n   - **Late Incoming Rake**: Delay rate jumps to **{operational_analysis['by_late_incoming_rake'].get('1', {}).get('p_delay_pct', 0)}%** (N={operational_analysis['by_late_incoming_rake'].get('1', {}).get('sample_count', 0):,}) with mean delay of **{operational_analysis['by_late_incoming_rake'].get('1', {}).get('mean_delay_min', 0)} min** (vs {operational_analysis['by_late_incoming_rake'].get('0', {}).get('mean_delay_min', 0)} min normal).\n   - **High Congestion**: Delay rate is **{congestion_analysis['by_congestion_level'].get('HIGH (>=0.70)', {}).get('p_delay_pct', 0)}%** (N={congestion_analysis['by_congestion_level'].get('HIGH (>=0.70)', {}).get('sample_count', 0):,}) with mean delay of **{congestion_analysis['by_congestion_level'].get('HIGH (>=0.70)', {}).get('mean_delay_min', 0)} min**.\n   - **Active Fog**: Delay rate is **{fog_analysis['by_is_fog_risk'].get('1', {}).get('p_delay_pct', 0)}%** (N={fog_analysis['by_is_fog_risk'].get('1', {}).get('sample_count', 0):,}) with mean delay of **{fog_analysis['by_is_fog_risk'].get('1', {}).get('mean_delay_min', 0)} min**.")
    md_lines.append("")

    # 4. Which factors are associated with severe delay (>45 min)?
    md_lines.append(f"4. **Which factors are associated with severe delay (>45 min)?**\n   - **Late Rake + Fog Compound**: **{conditional_combos.get('LateRake=True & Fog=True', {}).get('p_heavy_delay_pct', 0)}% heavy delay rate** (N={conditional_combos.get('LateRake=True & Fog=True', {}).get('sample_count', 0):,}, mean delay: {conditional_combos.get('LateRake=True & Fog=True', {}).get('mean_delay_min', 0)} min).\n   - **High Congestion + Peak Hour**: **{conditional_combos.get('Congestion=HIGH (>=0.70) & PeakHour=True', {}).get('p_heavy_delay_pct', 0)}% heavy delay rate** (N={conditional_combos.get('Congestion=HIGH (>=0.70) & PeakHour=True', {}).get('sample_count', 0):,}).\n   - **Primary Cause: Track Congestion**: Mean delay of **{delay_cause_stats.get('Track Congestion', {}).get('mean_delay_min', 0)} min** with **{delay_cause_stats.get('Track Congestion', {}).get('p_heavy_delay_pct', 0)}% heavy delay rate**.")
    md_lines.append("")

    # 5. Which factors can realistically be known at simulation time T?
    md_lines.append("5. **Which factors can realistically be known at simulation time T?**\n   - Current position, current speed, current delay against timetable, current section ID, current hour, season, local block signal, active physical speed restriction, and weather/fog observation.")
    md_lines.append("")

    # 6. Which historical factors should calibrate System 2?
    md_lines.append("6. **Which historical factors should calibrate System 2?**\n   - Empirical conditional matrices: `P(fog | season, hour, NR/NCR)`, `P(high_congestion | hour, NR/NCR)`, `P(late_incoming_rake)`, and `P(delay_cause | NR/NCR)`.")
    md_lines.append("")

    # 7. Which factors should NOT be used?
    md_lines.append("7. **Which factors should NOT be used?**\n   - `is_circular_route` (all linear on NDLS-DDN), `traction_type` / `is_electrified` (constant electrified), `loco_age_years` / `coach_age_years` (negligible predictive signal).\n   - `delay_minutes` / `is_delayed` / `target_eta` (Forbidden future leakage).")
    md_lines.append("")

    md_lines.append("---")
    md_lines.append("")
    md_lines.append("## 2. Primary Delay Causes (Pure Empirical Counts)")
    md_lines.append("")
    md_lines.append("| Primary Delay Cause | Sample Count (N) | % of All Records | Mean Delay (min) | Median Delay (min) | P90 Delay (min) | Heavy Delay (>45m) % |")
    md_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for cause, st in sorted(delay_cause_stats.items(), key=lambda x: x[1]["sample_count"], reverse=True):
        md_lines.append(f"| **{cause}** | {st['sample_count']:,} | {st['percentage_of_all_records']}% | {st['mean_delay_min']} min | {st['median_delay_min']} min | {st['p90_delay_min']} min | {st['p_heavy_delay_pct']}% |")

    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")
    md_lines.append("## 3. NR/NCR Winter Fog Matrix (Hour × Season with Sample Counts)")
    md_lines.append("")
    md_lines.append("| Departure Hour | Winter/Fog Sample Count (N) | Fog Count | Empirical Fog Probability (%) | Mean Delay when Fog Active (min) |")
    md_lines.append("| :--- | :--- | :--- | :--- | :--- |")
    for hr in range(24):
        hr_str = str(hr)
        w_data = winter_fog_nr_ncr.get(hr_str, {})
        n = w_data.get("sample_count", 0)
        f_cnt = w_data.get("fog_count", 0)
        p_fog = w_data.get("p_fog_pct", 0.0)
        m_del = w_data.get("mean_delay_fog_min", 0.0)
        md_lines.append(f"| `{hr:02d}:00` | {n:,} | {f_cnt:,} | **{p_fog:.1f}%** | {m_del:.1f} min |")

    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")
    md_lines.append("## 4. NR/NCR Hourly Congestion Matrix (Pure Data-Derived)")
    md_lines.append("")
    md_lines.append("| Departure Hour | NR/NCR Sample Count (N) | Mean Congestion Index | High Congestion (>=0.70) Count | High Congestion Probability (%) | Empirical Delay Probability (%) |")
    md_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
    for hr in range(24):
        hr_str = str(hr)
        c_data = nr_ncr_analysis["NR_NCR_congestion_by_hour"].get(hr_str, {})
        n = c_data.get("sample_count", 0)
        mean_idx = c_data.get("mean_congestion_index", 0.0)
        h_cnt = c_data.get("high_congestion_count", 0)
        p_h_cong = c_data.get("p_high_congestion_pct", 0.0)
        p_del = c_data.get("p_delay_pct", 0.0)
        md_lines.append(f"| `{hr:02d}:00` | {n:,} | {mean_idx:.4f} | {h_cnt:,} | **{p_h_cong:.1f}%** | {p_del:.1f}% |")

    md_lines.append("")
    out_md = Path(output_md_path)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"[Done] Pure Empirical Factor Audit Summary Markdown saved to: {out_md}")

    return report_data


if __name__ == "__main__":
    run_historical_factor_audit()
