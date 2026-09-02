"""
run_pipeline.py — Master End-to-End Execution Pipeline

Automates the complete railway delay prediction lifecycle across all phases:
1. Phase 6: Builds Historical Calibration from 1M+ dataset
2. Phase 6: Runs 30-second Closed-Loop Simulations on the selected route (DDN, AGC, or ALL)
3. Phase 7: Evaluates Baseline 1-3 Benchmarks on generated telemetry
4. Phase 8: Trains Machine Learning (XGBoost/GBR) ETA Regression Models
5. Phase 9: Executes Comparative Evaluation (ML vs All Baselines) & saves reports
6. Phase 10: Exports presentation-ready Excel Workbook & runs live prediction demo

Always saves unique files with ROUTE NAME and TIMESTAMP:
e.g. Data/synthetic_rtis/synthetic_journey_agra_20260902_160530.csv
     reports/Railway_Report_agra_20260902_160530.xlsx

================================================================================
USAGE & EXECUTION COMMANDS:
================================================================================
# 1. Run for Delhi -> Agra corridor (Default / Current Season):
python run_pipeline.py --route agra

# 2. Run for Delhi -> Agra corridor in Monsoon conditions:
python run_pipeline.py --route agra --season monsoon

# 3. Run for Delhi -> Agra corridor in Summer conditions:
python run_pipeline.py --route agra --season summer

# 4. Run for Delhi -> Dehradun corridor (Default / Winter Fog):
python run_pipeline.py --route dehradun

# 5. Run for Delhi -> Dehradun corridor in Monsoon conditions:
python run_pipeline.py --route dehradun --season monsoon

# 6. Run for Both Corridors in one execution:
python run_pipeline.py --route all

# 7. Quick Smoke Test mode (20 steps):
python run_pipeline.py --route agra --quick
================================================================================
"""

import sys
import os
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parent

# Ensure project root is in sys.path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ==============================================================================
# GLOBAL SIMULATION SETTINGS
# Change GLOBAL_DEFAULT_SEASON here to change the default season globally
# Options: "Winter/Fog", "Monsoon", "Summer", "Autumn", "Pre-Monsoon"
# ==============================================================================
GLOBAL_DEFAULT_SEASON = "Winter/Fog"


ROUTE_CONFIGS = {
    "dehradun": {
        "name": "New Delhi to Dehradun [314 km]",
        "route_key": "dehradun",
        "route_file": str(PROJECT_ROOT / "Data" / "routes" / "delhi_dehradun_route.json"),
        "events_file": str(PROJECT_ROOT / "src" / "simulator" / "events" / "simulation_events.json"),
        "train_id": "12017",
        "journey_id": "JRN_NDLS_DDN_01",
        "start_time": "06:45:00",
        "default_season": GLOBAL_DEFAULT_SEASON,
        "supported_seasons": ["Winter/Fog", "Monsoon", "Summer", "Autumn", "Pre-Monsoon"],
        "zone": "NR",
    },
    "agra": {
        "name": "New Delhi to Agra Cantt [195 km]",
        "route_key": "agra",
        "route_file": str(PROJECT_ROOT / "Data" / "routes" / "delhi_agra_route.json"),
        "events_file": str(PROJECT_ROOT / "src" / "simulator" / "events" / "delhi_agra_events.json"),
        "train_id": "12050",
        "journey_id": "JRN_NDLS_AGC_01",
        "start_time": "08:10:00",
        "default_season": GLOBAL_DEFAULT_SEASON,
        "supported_seasons": ["Winter/Fog", "Monsoon", "Summer", "Autumn", "Pre-Monsoon"],
        "zone": "NCR",
    }
}


def print_banner(step_num: int, total_steps: int, title: str):
    print("\n" + "=" * 80)
    print(f"  [{step_num}/{total_steps}] {title.upper()}")
    print("=" * 80)


def run_full_pipeline(
    selected_route: str = "dehradun",
    selected_season: str = "default",
    quick_mode: bool = False
):
    start_time = datetime.now()
    timestamp_str = start_time.strftime("%Y%m%d_%H%M%S")
    total_steps = 6

    # Normalize season name if passed
    season_map = {
        "winter": "Winter/Fog",
        "fog": "Winter/Fog",
        "winter/fog": "Winter/Fog",
        "monsoon": "Monsoon",
        "rain": "Monsoon",
        "summer": "Summer",
        "autumn": "Autumn",
        "pre-monsoon": "Pre-Monsoon"
    }
    season_override = season_map.get(selected_season.lower()) if selected_season.lower() != "default" else None

    # Determine which routes to run
    routes_to_run = []
    if selected_route.lower() in ["all", "both"]:
        routes_to_run = ["dehradun", "agra"]
    elif selected_route.lower() in ["agra", "agc", "ndls_agc"]:
        routes_to_run = ["agra"]
    elif selected_route.lower() in ["dehradun", "ddn", "ndls_ddn"]:
        routes_to_run = ["dehradun"]
    else:
        if os.path.exists(selected_route):
            routes_to_run = ["custom"]
            ROUTE_CONFIGS["custom"] = {
                "name": f"Custom Route ({Path(selected_route).name})",
                "route_key": "custom",
                "route_file": selected_route,
                "events_file": str(PROJECT_ROOT / "src" / "simulator" / "events" / "simulation_events.json"),
                "train_id": "12000",
                "journey_id": "JRN_CUSTOM_01",
                "start_time": "08:00:00",
                "default_season": GLOBAL_DEFAULT_SEASON,
                "zone": "NR",
            }
        else:
            routes_to_run = ["dehradun"]

    effective_season_display = season_override if season_override else f"Global Default ({GLOBAL_DEFAULT_SEASON})"
    print("\n" + "#" * 80)
    print("      INDIAN RAILWAYS AI DELAY & ETA PREDICTION PIPELINE (PHASES 6 - 10)")
    print("#" * 80)
    print(f"Start Timestamp : {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Selected Route  : {selected_route.upper()} ({len(routes_to_run)} corridor(s))")
    print(f"Active Season   : {effective_season_display}")
    print(f"Execution Mode  : {'Quick Test Mode (20 steps)' if quick_mode else 'Full Continuous Simulation'}")

    # -------------------------------------------------------------
    # STEP 1: Phase 6 — Historical Calibration Builder
    # -------------------------------------------------------------
    print_banner(1, total_steps, "Phase 6: Historical Calibration Builder")
    from src.data_generator.calibration_builder import build_historical_calibration
    calib_path = build_historical_calibration()
    print(f"[Done] Calibration matrix built at: {calib_path}")

    # -------------------------------------------------------------
    # STEP 2: Phase 6 — 30-Second Closed-Loop Route Simulation(s)
    # -------------------------------------------------------------
    print_banner(2, total_steps, f"Phase 6: Closed-Loop Simulation ({len(routes_to_run)} corridor(s))")
    from src.data_generator.dataset_builder import build_synthetic_journey

    generated_csvs = []
    last_route_file = None
    last_route_key = None

    for rkey in routes_to_run:
        rinfo = ROUTE_CONFIGS[rkey]
        active_season = season_override if season_override else rinfo.get("default_season", GLOBAL_DEFAULT_SEASON)
        
        # Unique timestamped and route-named output files
        unique_csv_name = f"synthetic_journey_{rinfo['route_key']}_{timestamp_str}.csv"
        unique_json_name = f"synthetic_journey_{rinfo['route_key']}_{timestamp_str}.json"
        
        out_csv = str(PROJECT_ROOT / "Data" / "synthetic_rtis" / unique_csv_name)
        out_json = str(PROJECT_ROOT / "Data" / "synthetic_rtis" / unique_json_name)

        print(f"\n>>> [Simulating Corridor] {rinfo['name']} (Season: {active_season})")
        print(f"    Saving New File: {unique_csv_name}")

        sim_res = build_synthetic_journey(
            route_filepath=rinfo["route_file"],
            events_filepath=rinfo["events_file"],
            train_id=rinfo["train_id"],
            journey_id=f"{rinfo['journey_id']}_{timestamp_str}",
            start_time_str=rinfo["start_time"],
            season=active_season,
            zone=rinfo["zone"],
            output_csv_path=out_csv,
            output_json_path=out_json,
            max_steps=20 if quick_mode else None,
            verbose=True
        )
        generated_csvs.append(out_csv)
        last_route_file = rinfo["route_file"]
        last_route_key = rinfo["route_key"]

    # Target ML dataset to evaluate / train
    target_dataset = generated_csvs[-1]
    
    # Also copy to canonical ml_ready_dataset.csv
    try:
        shutil.copy2(target_dataset, str(PROJECT_ROOT / "Data" / "ml" / "ml_ready_dataset.csv"))
    except Exception:
        pass

    # -------------------------------------------------------------
    # STEP 3: Phase 7 — Baseline Benchmark Evaluations
    # -------------------------------------------------------------
    print_banner(3, total_steps, "Phase 7: Baseline Benchmark Evaluations")
    from src.prediction.evaluator import load_dataset, evaluate_baselines

    rows = load_dataset(target_dataset)
    if rows:
        overall_baselines = evaluate_baselines(rows)
        print(f"[Done] Evaluated {len(rows)} observations from {Path(target_dataset).name} across all 3 baselines:")
        for b_name, m in overall_baselines.items():
            mae = m.get("mae", 0.0)
            rmse = m.get("rmse", 0.0)
            acc5 = m.get("accuracy_within_5_min", 0.0)
            acc10 = m.get("accuracy_within_10_min", 0.0)
            print(f"  • {b_name:25s} -> MAE: {mae:6.2f} min | RMSE: {rmse:6.2f} min | ±5m: {acc5:5.1f}% | ±10m: {acc10:5.1f}%")
    else:
        print(f"[Info] Target dataset '{Path(target_dataset).name}' ready for ML training.")

    # -------------------------------------------------------------
    # STEP 4: Phase 8 — Train Machine Learning ETA Models
    # -------------------------------------------------------------
    print_banner(4, total_steps, "Phase 8: Machine Learning ETA Model Training")
    from src.prediction.ml_model import MLETAEngineModel

    ml_model = MLETAEngineModel()
    ml_metrics = ml_model.train_from_csv(target_dataset)
    saved_model_path = ml_model.save_model(str(PROJECT_ROOT / "models"))
    print(f"[Done] ML Model saved at: {saved_model_path}")
    print(f"  • Destination ETA MAE: {ml_metrics['mae_eta_destination_min']} min | RMSE: {ml_metrics['rmse_eta_destination_min']} min")
    print(f"  • Next Station ETA MAE: {ml_metrics['mae_eta_next_station_min']} min | RMSE: {ml_metrics['rmse_eta_next_station_min']} min")

    # -------------------------------------------------------------
    # STEP 5: Phase 9 — Comparative Benchmark (ML vs All Baselines)
    # -------------------------------------------------------------
    print_banner(5, total_steps, "Phase 9: Comparative Evaluation & Reporting")
    from src.prediction.ml_evaluator import ComparativeMLEvaluator, generate_benchmark_markdown_report

    evaluator = ComparativeMLEvaluator(
        route_filepath=last_route_file or str(PROJECT_ROOT / "Data" / "routes" / "delhi_dehradun_route.json"),
        model_filepath=str(saved_model_path)
    )
    report_data = evaluator.evaluate_dataset(target_dataset)

    # Save unique Markdown & JSON reports
    rep_dir = PROJECT_ROOT / "reports"
    rep_dir.mkdir(parents=True, exist_ok=True)
    
    unique_md_name = f"benchmark_report_{last_route_key}_{timestamp_str}.md"
    unique_json_name = f"benchmark_report_{last_route_key}_{timestamp_str}.json"
    
    md_file = rep_dir / unique_md_name
    json_file = rep_dir / unique_json_name

    with open(md_file, "w", encoding="utf-8") as f:
        f.write(generate_benchmark_markdown_report(report_data))
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    # Maintain latest copy
    try:
        shutil.copy2(str(md_file), str(rep_dir / "ml_vs_baseline_report.md"))
        shutil.copy2(str(json_file), str(rep_dir / "ml_vs_baseline_report.json"))
    except Exception:
        pass

    print(f"[Done] Unique Markdown Report : {md_file.name}")
    print(f"[Done] Unique JSON Metrics    : {json_file.name}")

    # -------------------------------------------------------------
    # STEP 6: Phase 10 — Excel Workbook Export & Live Inference Demo
    # -------------------------------------------------------------
    print_banner(6, total_steps, "Phase 10: Excel Report Export & Live Demo")
    from src.output.export_excel_report import export_railway_excel_report
    
    unique_excel_name = f"Railway_Report_{last_route_key}_{timestamp_str}.xlsx"
    unique_excel_path = str(rep_dir / unique_excel_name)
    
    excel_path = export_railway_excel_report(
        route_name=last_route_key or "delhi_corridor",
        dataset_csv_path=target_dataset,
        output_path=unique_excel_path,
        route_json_path=last_route_file
    )

    from src.prediction.demo_prediction import run_live_prediction_demo
    run_live_prediction_demo()

    # -------------------------------------------------------------
    # PIPELINE COMPLETE SUMMARY
    # -------------------------------------------------------------
    duration = (datetime.now() - start_time).total_seconds()
    print("\n" + "#" * 80)
    print(f"      ALL PIPELINE PHASES EXECUTED SUCCESSFULLY IN {duration:.1f}s")
    print("#" * 80)
    print(f"  • Route Evaluated  : {selected_route.upper()}")
    print(f"  • Season Applied   : {effective_season_display}")
    print(f"  • New Telemetry CSV: {Path(target_dataset).name}")
    print(f"  • ML Model Artifact: {Path(saved_model_path).name}")
    print(f"  • Benchmark Report : {unique_md_name}")
    print(f"  • New Excel File   : {unique_excel_name}")
    print("#" * 80 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run complete railway delay prediction pipeline.")
    parser.add_argument(
        "--route",
        type=str,
        default="dehradun",
        help="Route to simulate and evaluate: 'dehradun' (default), 'agra', 'all', or a custom route JSON path"
    )
    parser.add_argument(
        "--season",
        type=str,
        default="default",
        help="Season environment: 'winter', 'monsoon', 'summer', 'autumn', or 'default'"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run in quick micro-test mode (20 steps)"
    )
    args = parser.parse_args()

    run_full_pipeline(selected_route=args.route, selected_season=args.season, quick_mode=args.quick)
