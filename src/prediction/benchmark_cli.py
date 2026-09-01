"""
benchmark_cli.py — Phase 9: Benchmark CLI Runner
Executes comprehensive comparative benchmarking between the Phase 8 ML ETA Model
and the 3 Baseline Engines on a target CSV dataset, saving Markdown and JSON reports.

Usage:
    python -m src.prediction.benchmark_cli --dataset Data/ml/ml_ready_dataset.csv --output-dir reports
"""

import os
import sys
import json
import argparse
from pathlib import Path

from src.prediction.ml_evaluator import ComparativeMLEvaluator, generate_benchmark_markdown_report

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase 9 — ML ETA vs Baselines Comparative Benchmark Runner"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=str(PROJECT_ROOT / "Data" / "ml" / "ml_ready_dataset.csv"),
        help="Path to the ML-ready dataset CSV (default: Data/ml/ml_ready_dataset.csv)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(PROJECT_ROOT / "reports"),
        help="Directory to write reports to (default: reports/)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=str(PROJECT_ROOT / "models" / "xgboost_eta_model.pkl"),
        help="Path to the trained ML model binary (default: models/xgboost_eta_model.pkl)",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    output_dir = Path(args.output_dir)
    model_path = Path(args.model)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("      PHASE 9: ML ETA MODEL VS BASELINES COMPARATIVE BENCHMARK")
    print("=" * 72)
    print(f"Dataset   : {dataset_path}")
    print(f"Model     : {model_path}")
    print(f"Output Dir: {output_dir}")
    print()

    # 1. Initialize Evaluator
    print("[1/3] Loading route topology, baselines, and ML model...")
    evaluator = ComparativeMLEvaluator(
        route_filepath=str(PROJECT_ROOT / "Data" / "routes" / "delhi_dehradun_route.json"),
        model_filepath=str(model_path)
    )

    # 2. Run Evaluation
    print(f"[2/3] Ingesting and evaluating {dataset_path.name} across all 4 models...")
    report_data = evaluator.evaluate_dataset(str(dataset_path))
    total_obs = report_data["total_observations"]
    print(f"      Evaluated {total_obs} 30-second observations successfully.")

    # 3. Save Markdown and JSON Reports
    print("[3/3] Generating benchmark reports...")
    
    # Markdown
    md_content = generate_benchmark_markdown_report(report_data)
    md_file = output_dir / "ml_vs_baseline_report.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"      Markdown Report : {md_file}")

    # JSON
    json_file = output_dir / "ml_vs_baseline_report.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print(f"      JSON Metrics    : {json_file}")

    print()
    print("=" * 72)
    print("Benchmark complete! Key summary:")
    dest_overall = report_data["overall"]["destination_eta"]
    for m_key, m_name in [
        ("scheduled", "Baseline 1 (Scheduled)"),
        ("schedule_plus_delay", "Baseline 2 (Schedule+Delay)"),
        ("historical_median", "Baseline 3 (Section Medians)"),
        ("ml_model", "Model 4 (Phase 8 ML)"),
    ]:
        m = dest_overall.get(m_key, {})
        print(f"  • {m_name:30s} -> MAE: {m.get('mae', 0.0):6.2f} min | RMSE: {m.get('rmse', 0.0):6.2f} min | +/-15m: {m.get('accuracy_within_15_min', 0.0):5.1f}%")
    print("=" * 72)


if __name__ == "__main__":
    main()
