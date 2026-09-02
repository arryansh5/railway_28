"""
csv_writer.py — Phase 3: Physics-Based RTIS Simulator
Writes simulation observation logs to CSV and JSON files with file lock resilience.
"""

import csv
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict


def write_observations_to_csv(observations: List[Dict], output_filepath: str) -> str:
    """
    Writes a list of observation dictionaries to a CSV file.
    If the target file is locked by Excel/editor, automatically falls back to a timestamped file.

    Parameters:
    - observations: List of observation dicts from observation_generator
    - output_filepath: Destination CSV path (e.g. 'Data/simulations/journey_01_30s.csv')
    
    Returns:
    - Actual file path written to.
    """
    if not observations:
        return output_filepath

    path = Path(output_filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(observations[0].keys())

    target_path = path
    try:
        with open(target_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(observations)
    except PermissionError:
        # Fallback to alternative filename if locked by Excel/Viewer
        ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        fallback_name = f"{path.stem}_{ts_str}{path.suffix}"
        target_path = path.parent / fallback_name
        print(f"[CSVWriter] WARNING: '{path.name}' is currently open/locked. Writing to: '{target_path.name}'")
        with open(target_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(observations)

    return str(target_path)


def write_observations_to_json(observations: List[Dict], output_filepath: str) -> str:
    """
    Writes a list of observation dictionaries to a formatted JSON file with fallback.
    """
    if not observations:
        return output_filepath

    path = Path(output_filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    target_path = path
    try:
        with open(target_path, mode="w", encoding="utf-8") as f:
            json.dump({"observations": observations}, f, indent=2)
    except PermissionError:
        ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        fallback_name = f"{path.stem}_{ts_str}{path.suffix}"
        target_path = path.parent / fallback_name
        print(f"[JSONWriter] WARNING: '{path.name}' is locked. Writing to: '{target_path.name}'")
        with open(target_path, mode="w", encoding="utf-8") as f:
            json.dump({"observations": observations}, f, indent=2)

    return str(target_path)


if __name__ == "__main__":
    from src.simulator.train.train_state import TrainState
    from src.simulator.output.observation_generator import generate_observation

    dummy_state = TrainState(
        train_id="12017",
        route_id="ROUTE_NDLS_DDN_01",
        simulation_time_sec=0.0,
        timestamp="06:45:00",
        current_position_km=0.0,
        current_position_m=0.0,
        current_speed_mps=0.0,
        current_speed_kmph=0.0,
        target_speed_kmph=0.0,
        current_acceleration_mps2=0.0,
        current_section_id=None,
        current_station_id="NDLS",
        previous_station_id=None,
        next_station_id="GZB",
        distance_to_next_station_km=25.0,
        distance_to_destination_km=314.0,
        braking_distance_m=0.0,
        movement_state="STOPPED",
        station_event=None,
        actual_arrival_time=None,
        actual_departure_time=None,
        actual_dwell_min=None,
        current_delay_min=0.0,
        arrival_delay_min=None,
        departure_delay_min=None,
        signal_state="GREEN",
        speed_restriction_kmph=None,
        congestion_level=None,
        fog_active=False,
        fog_visibility_km=None,
        unscheduled_halt=False,
        active_event_ids=[],
        latitude=28.6431,
        longitude=77.2197,
        data_quality_status="OK"
    )

    sample_obs = [
        generate_observation(1, dummy_state, 110.0, None),
        generate_observation(2, dummy_state, 110.0, None)
    ]

    test_csv = r"D:\Projects\railway\Data\simulations\test_output.csv"
    written_to = write_observations_to_csv(sample_obs, test_csv)
    print("=== CSV Writer Test ===")
    print(f"Successfully wrote {len(sample_obs)} rows to {written_to}")
