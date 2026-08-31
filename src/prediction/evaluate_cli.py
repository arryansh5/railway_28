"""
Baseline Evaluation CLI — Phase 7.
Runs baseline section-level travel time benchmarks on historical/synthetic CSV datasets.
Outputs markdown report and JSON metrics.

Usage:
    python -m src.prediction.evaluate_cli --dataset Data/historical/val.csv
    python -m src.prediction.evaluate_cli --dataset Data/historical/test.csv --output-dir reports
"""

import argparse
import sys
from pathlib import Path

from src.prediction.evaluator import (
    load_dataset,
    evaluate_baselines,
    evaluate_sliced,
    evaluate_by_section,
    generate_report,
    save_report_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Phase 7 baseline ETA evaluation on a section-level CSV dataset."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="Path to the CSV dataset (e.g. Data/historical/val.csv)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports",
        help="Directory to save reports (default: reports/)",
    )
    args = parser.parse_args()

    dataset_path = args.dataset
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Derive a label from the filename (e.g. "val" or "test")
    dataset_label = Path(dataset_path).stem

    print(f"=" * 60)
    print(f"Phase 7 — Baseline ETA Benchmark Evaluation")
    print(f"=" * 60)
    print(f"Dataset : {dataset_path}")
    print(f"Output  : {output_dir}/")
    print()

    # 1. Load dataset
    print("[1/4] Loading dataset...")
    rows = load_dataset(dataset_path)
    print(f"       Loaded {len(rows)} section-level observations.")
    if not rows:
        print("ERROR: No valid rows found in dataset. Exiting.")
        sys.exit(1)

    # 2. Overall evaluation
    print("[2/4] Evaluating baselines (overall)...")
    overall = evaluate_baselines(rows)
    print("       Done.")
    for method, metrics in overall.items():
        print(f"       {method:25s} -> MAE={metrics['mae']:.2f}  RMSE={metrics['rmse']:.2f}  "
              f"P90={metrics['p90_error']:.2f}  +/-5min={metrics['accuracy_within_5_min']:.1f}%  "
              f"+/-10min={metrics['accuracy_within_10_min']:.1f}%")

    # 3. Sliced evaluation
    print("[3/4] Evaluating operational condition slices...")
    sliced = evaluate_sliced(rows)
    print(f"       Evaluated {len(sliced)} condition slices.")

    # 4. Section-level breakdown
    print("[4/4] Evaluating per-section breakdown...")
    by_section = evaluate_by_section(rows)
    print(f"       Evaluated {len(by_section)} sections.")
    print()

    # Generate markdown report
    md_report = generate_report(dataset_path, rows, overall, sliced, by_section)
    md_path = output_dir / f"baseline_benchmark_{dataset_label}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)
    print(f"Markdown report saved: {md_path}")

    # Generate JSON metrics
    json_path = output_dir / f"baseline_benchmark_{dataset_label}.json"
    save_report_json(str(json_path), overall, sliced, by_section)
    print(f"JSON metrics saved  : {json_path}")

    print()
    print(f"{'=' * 60}")
    print(f"Benchmark complete. Review the report at: {md_path}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
