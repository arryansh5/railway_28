"""
CLI script to generate historical synthetic datasets.
"""

import json
import sys
from pathlib import Path

from src.data_generator.generator import DatasetGenerator


def main():
    root = Path(__file__).resolve().parent.parent.parent
    route_path = root / "Data" / "routes" / "delhi_dehradun_route.json"
    output_dir = root / "Data" / "historical"

    print(f"Loading route from: {route_path}")
    with open(route_path, "r", encoding="utf-8") as f:
        route = json.load(f)

    generator = DatasetGenerator(route, seed=42)
    print("Generating synthetic datasets with causal operations & disruptions...")
    train_path, val_path, test_path = generator.export_split_datasets(
        str(output_dir), num_days=45, train_ratio=0.70, val_ratio=0.15
    )

    print("\nDatasets successfully exported:")
    print(f"  Train: {train_path}")
    print(f"  Val:   {val_path}")
    print(f"  Test:  {test_path}")


if __name__ == "__main__":
    main()
