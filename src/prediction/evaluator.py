"""
Baseline Evaluator — Phase 7.
Evaluates section-level travel time baselines on historical/synthetic CSV datasets.
Produces overall and operationally-sliced benchmark metrics.
"""

import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

from src.prediction.metrics import EvaluationMetrics
from src.prediction.baseline_engine import BaselineETAEngine


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS = [
    "section_id",
    "scheduled_running_time_min",
    "actual_section_running_time_min",
]


def load_dataset(filepath: str) -> List[Dict[str, Any]]:
    """
    Load a section-level CSV dataset.

    Args:
        filepath: Path to CSV file with columns matching the synthetic dataset schema.

    Returns:
        List of row dictionaries with numeric fields parsed.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {filepath}")

    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Validate required columns exist
            if any(row.get(col) is None for col in REQUIRED_COLUMNS):
                continue

            # Parse numeric fields
            parsed = _parse_row(row)
            if parsed is not None:
                rows.append(parsed)

    return rows


def _parse_row(row: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Parse a CSV row dict, converting numeric strings to floats."""
    try:
        parsed: Dict[str, Any] = {}
        for key, val in row.items():
            if val is None or val.strip() == "":
                parsed[key] = None
                continue

            # Try numeric conversion for known numeric fields
            if key in _NUMERIC_FIELDS:
                try:
                    parsed[key] = float(val)
                except ValueError:
                    parsed[key] = val
            else:
                parsed[key] = val

        return parsed
    except Exception:
        return None


_NUMERIC_FIELDS = {
    "section_distance_km",
    "scheduled_running_time_min",
    "max_sectional_speed_kmph",
    "entry_speed_kmph",
    "entry_delay_min",
    "previous_section_delay_min",
    "visibility_km",
    "speed_restriction_active",
    "restriction_speed_kmph",
    "unscheduled_halt_active",
    "unscheduled_halt_min",
    "recovery_applied_min",
    "historical_section_median_min",
    "historical_section_p90_min",
    "actual_section_running_time_min",
    "section_delay_delta_min",
    "exit_delay_min",
    "hour",
    "day_of_week",
    "is_weekend",
}


# ---------------------------------------------------------------------------
# Baseline prediction on dataset rows
# ---------------------------------------------------------------------------

BASELINE_METHODS = ["SCHEDULED", "SCHEDULE_PLUS_DELAY", "HISTORICAL_MEDIAN"]


def evaluate_baselines(
    rows: List[Dict[str, Any]],
    methods: Optional[List[str]] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Evaluate all baseline methods on a list of dataset rows.

    Args:
        rows: Parsed dataset rows.
        methods: Baseline method names to evaluate. Defaults to all three.

    Returns:
        Dict mapping method name -> evaluation metrics dict.
    """
    if methods is None:
        methods = BASELINE_METHODS

    results: Dict[str, Dict[str, Any]] = {}
    actuals = [float(r["actual_section_running_time_min"]) for r in rows]

    for method in methods:
        predictions = [
            BaselineETAEngine.predict_section_time(r, method=method)
            for r in rows
        ]
        metrics = EvaluationMetrics.compute(actuals, predictions)
        metrics["method"] = method
        results[method] = metrics

    return results


# ---------------------------------------------------------------------------
# Operational slicing
# ---------------------------------------------------------------------------

SliceFilter = Callable[[Dict[str, Any]], bool]

# Define operational slices as (slice_name, filter_function) pairs
OPERATIONAL_SLICES: Dict[str, SliceFilter] = {
    # Congestion
    "congestion_LOW": lambda r: r.get("congestion_level") == "LOW",
    "congestion_MEDIUM": lambda r: r.get("congestion_level") == "MEDIUM",
    "congestion_HIGH": lambda r: r.get("congestion_level") == "HIGH",

    # Speed restriction
    "speed_restriction_ON": lambda r: _is_truthy(r.get("speed_restriction_active")),
    "speed_restriction_OFF": lambda r: not _is_truthy(r.get("speed_restriction_active")),

    # Unscheduled halt
    "unscheduled_halt_YES": lambda r: _is_truthy(r.get("unscheduled_halt_active")),
    "unscheduled_halt_NO": lambda r: not _is_truthy(r.get("unscheduled_halt_active")),

    # Weather condition
    "weather_CLEAR": lambda r: r.get("weather_condition") == "CLEAR",
    "weather_RAIN": lambda r: r.get("weather_condition") == "RAIN",
    "weather_FOG": lambda r: r.get("weather_condition") == "FOG",

    # Entry delay magnitude
    "delay_on_time": lambda r: _float_or_zero(r.get("entry_delay_min")) <= 5.0,
    "delay_moderate": lambda r: 5.0 < _float_or_zero(r.get("entry_delay_min")) <= 15.0,
    "delay_heavy": lambda r: _float_or_zero(r.get("entry_delay_min")) > 15.0,

    # Section groups
    "section_plains": lambda r: r.get("section_id") in {
        "SEC_NDLS_GZB", "SEC_GZB_MTC", "SEC_MTC_MOZ", "SEC_MOZ_SRE"
    },
    "section_hills": lambda r: r.get("section_id") in {
        "SEC_SRE_RK", "SEC_RK_HW", "SEC_HW_DDN"
    },
}


def _is_truthy(val: Any) -> bool:
    """Check if a value is truthy (handles '0', '1', 0, 1, True, False, None)."""
    if val is None:
        return False
    if isinstance(val, (int, float)):
        return val != 0
    if isinstance(val, str):
        return val.strip() not in ("", "0", "0.0", "false", "False")
    return bool(val)


def _float_or_zero(val: Any) -> float:
    """Safely convert to float, default 0."""
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def evaluate_sliced(
    rows: List[Dict[str, Any]],
    methods: Optional[List[str]] = None,
    slices: Optional[Dict[str, SliceFilter]] = None,
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Evaluate baselines across operational slices.

    Returns:
        Dict mapping slice_name -> { method_name -> metrics_dict }.
    """
    if methods is None:
        methods = BASELINE_METHODS
    if slices is None:
        slices = OPERATIONAL_SLICES

    results: Dict[str, Dict[str, Dict[str, Any]]] = {}

    for slice_name, filter_fn in slices.items():
        filtered = [r for r in rows if filter_fn(r)]
        if len(filtered) < 2:
            continue
        results[slice_name] = evaluate_baselines(filtered, methods)
        # Add row count to each method result
        for method_metrics in results[slice_name].values():
            method_metrics["slice_count"] = len(filtered)

    return results


# ---------------------------------------------------------------------------
# Section-level breakdown
# ---------------------------------------------------------------------------

def evaluate_by_section(
    rows: List[Dict[str, Any]],
    methods: Optional[List[str]] = None,
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Evaluate baselines grouped by individual section_id.

    Returns:
        Dict mapping section_id -> { method_name -> metrics_dict }.
    """
    if methods is None:
        methods = BASELINE_METHODS

    # Group rows by section
    section_groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        sec = r.get("section_id", "UNKNOWN")
        section_groups.setdefault(sec, []).append(r)

    results: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for sec_id, sec_rows in sorted(section_groups.items()):
        results[sec_id] = evaluate_baselines(sec_rows, methods)
        for method_metrics in results[sec_id].values():
            method_metrics["section_count"] = len(sec_rows)

    return results


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(
    dataset_path: str,
    rows: List[Dict[str, Any]],
    overall: Dict[str, Dict[str, Any]],
    sliced: Dict[str, Dict[str, Dict[str, Any]]],
    by_section: Dict[str, Dict[str, Dict[str, Any]]],
) -> str:
    """
    Generate a human-readable markdown benchmark report.

    Returns:
        Markdown string.
    """
    lines: List[str] = []
    lines.append("# Phase 7 — Baseline ETA Benchmark Report")
    lines.append("")
    lines.append(f"**Dataset**: `{dataset_path}`")
    lines.append(f"**Total Rows**: {len(rows)}")
    lines.append(f"**Data Source**: SYNTHETIC_DATASET")
    lines.append(f"**Target Variable**: `actual_section_running_time_min`")
    lines.append("")

    # Overall metrics table
    lines.append("## 1. Overall Baseline Comparison")
    lines.append("")
    lines.append(_metrics_table(overall))
    lines.append("")

    # Section-level breakdown
    lines.append("## 2. Per-Section Breakdown")
    lines.append("")
    for sec_id, sec_results in by_section.items():
        count = next(iter(sec_results.values()), {}).get("section_count", "?")
        lines.append(f"### Section: `{sec_id}` ({count} rows)")
        lines.append("")
        lines.append(_metrics_table(sec_results))
        lines.append("")

    # Operational slices
    lines.append("## 3. Operational Condition Slices")
    lines.append("")
    for slice_name, slice_results in sliced.items():
        count = next(iter(slice_results.values()), {}).get("slice_count", "?")
        lines.append(f"### {slice_name} ({count} rows)")
        lines.append("")
        lines.append(_metrics_table(slice_results))
        lines.append("")

    return "\n".join(lines)


def _metrics_table(results: Dict[str, Dict[str, Any]]) -> str:
    """Format a comparison table for multiple baseline methods."""
    header = "| Model | Count | MAE | RMSE | Bias | P50 | P90 | P95 | Max Err | ±5 min (%) | ±10 min (%) |"
    sep = "|---|---|---|---|---|---|---|---|---|---|---|"
    rows = [header, sep]

    for method, m in results.items():
        row = (
            f"| {method} | {m.get('count', '-')} "
            f"| {m.get('mae', '-')} | {m.get('rmse', '-')} | {m.get('bias', '-')} "
            f"| {m.get('p50_error', '-')} | {m.get('p90_error', '-')} | {m.get('p95_error', '-')} "
            f"| {m.get('max_error', '-')} "
            f"| {m.get('accuracy_within_5_min', '-')} | {m.get('accuracy_within_10_min', '-')} |"
        )
        rows.append(row)

    return "\n".join(rows)


def save_report_json(
    filepath: str,
    overall: Dict[str, Dict[str, Any]],
    sliced: Dict[str, Dict[str, Dict[str, Any]]],
    by_section: Dict[str, Dict[str, Dict[str, Any]]],
) -> None:
    """Save the full evaluation results as JSON."""
    output = {
        "overall": overall,
        "by_section": by_section,
        "operational_slices": sliced,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
