"""
dataset_builder.py — Phase 6: Steps 7–12
Closed-Loop Orchestrator & Synthetic Dataset Generator.

Brings together:
- System 1: RTIS / Physics Simulator (kinematics, speed controller, station lifecycle, GPS)
- System 2: Delay Risk / Condition Predictor (probabilistic risk evaluation at timestamp t)
- System 3: Dynamic Update / Restriction Engine (synthetic restriction state machine)

Workflow (every 30 seconds):
System 1 (State t) -> System 2 (Prediction) -> System 3 (Synthetic Restriction) -> System 1 (Physics 30s) -> Dynamic ETA -> Log CSV row

Post-Processing (Anti-Leakage Guaranteed):
Back-populates target_eta_to_next_station_min and target_eta_to_destination_min labels from actual eventual arrival.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.simulator.route.route_loader import load_route, load_config, load_events
from src.simulator.train.train_state import TrainState
from src.simulator.events.event_manager import get_active_events, resolve_speed_constraints
from src.simulator.physics.physics_engine import (
    update_speed,
    update_position,
    compute_braking_distance,
    kmph_to_mps,
    mps_to_kmph
)
from src.simulator.physics.speed_controller import (
    compute_target_speed,
    compute_acceleration,
    get_movement_state
)
from src.simulator.geo.coordinate_interpolator import interpolate_coordinates
from src.simulator.output.observation_generator import generate_observation
from src.simulator.output.csv_writer import write_observations_to_csv, write_observations_to_json
from src.simulator.validation.observation_validator import validate_observations

from src.data_generator.prediction_engine import BaselinePredictiveEngine
from src.data_generator.restriction_engine import RestrictionEngine

# Automatically detect project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _format_time(base_time_str: str, elapsed_seconds: float) -> str:
    """Helper to calculate HH:MM:SS by adding elapsed seconds."""
    base_dt = datetime.strptime(base_time_str, "%H:%M:%S")
    current_dt = base_dt + timedelta(seconds=elapsed_seconds)
    return current_dt.strftime("%H:%M:%S")


def build_synthetic_journey(
    route_filepath: str = str(PROJECT_ROOT / "Data" / "routes" / "delhi_dehradun_route.json"),
    config_filepath: str = str(PROJECT_ROOT / "src" / "simulator" / "config" / "simulator_config.json"),
    calibration_filepath: str = str(PROJECT_ROOT / "config" / "historical_calibration.json"),
    events_filepath: str = str(PROJECT_ROOT / "src" / "simulator" / "events" / "simulation_events.json"),
    start_time_str: str = "06:45:00",
    train_id: str = "12017",
    season: str = "Winter/Fog",
    output_csv_path: str = str(PROJECT_ROOT / "Data" / "synthetic_rtis" / "synthetic_journey_NDLS_DDN_01.csv")
) -> List[Dict[str, Any]]:
    """
    Executes a complete 30-second closed-loop journey combining System 1, System 2, and System 3.
    """
    print(f"\n[Closed-Loop Orchestrator] Starting journey simulation on NDLS -> DDN corridor...")
    print(f"  - Route File       : {route_filepath}")
    print(f"  - Start Time       : {start_time_str}")
    print(f"  - Season           : {season}")
    print(f"  - Calibration File : {calibration_filepath}")

    # 1. Load Route & Configuration
    route = load_route(route_filepath)
    config = load_config(config_filepath)
    events = load_events(events_filepath)

    # 2. Instantiate System 2 Predictor & System 3 Restriction Engine
    system2_predictor = BaselinePredictiveEngine(calibration_filepath)
    system3_decision = RestrictionEngine(calibration_filepath)

    dt = config["simulation_timestep_seconds"]
    physics = config["physics"]
    max_accel = physics["max_acceleration_mps2"]
    max_brake = physics["max_braking_deceleration_mps2"]

    stations = route["stations"]
    sections = route["sections"]
    stn_lookup = route["station_lookup"]
    origin = route["origin"]
    terminal = route["terminal"]
    total_km = route["total_distance_km"]

    # 3. Simulation State Initialization
    elapsed_sec = 0.0
    current_pos_m = 0.0
    current_speed_mps = 0.0

    station_idx = 0
    next_station = stations[1]
    current_section_idx = 0
    current_section = sections[0]

    dwelling = False
    dwell_time_remaining_sec = 0.0
    journey_completed = False

    observations = []
    step = 1

    station_arrival_times: Dict[str, float] = {}

    while not journey_completed and elapsed_sec < 43200:  # 12-hour max
        current_time_str = _format_time(start_time_str, elapsed_sec)
        current_pos_km = current_pos_m / 1000.0
        current_speed_kmph = mps_to_kmph(current_speed_mps)

        # --- A. SYSTEM 1: Current State Extraction ---
        current_section_id = current_section["section_id"] if current_section and not journey_completed else None
        section_limit_kmph = current_section["max_sectional_speed_kmph"] if current_section else 0.0
        current_delay_min = (elapsed_sec / 60.0) - (current_pos_km / total_km * route["total_scheduled_duration_min"])

        current_state_features = {
            "timestamp": current_time_str,
            "current_position_km": current_pos_km,
            "current_speed_kmph": current_speed_kmph,
            "current_section_id": current_section_id,
            "current_delay_min": current_delay_min
        }

        # --- B. SYSTEM 2: Predict Operational Condition Risks ---
        prediction = system2_predictor.predict(
            current_state_features,
            context={"season": season, "prediction_horizon_min": 30.0}
        )

        # --- C. SYSTEM 3: Update Dynamic Synthetic Restrictions ---
        synthetic_restrictions = system3_decision.evaluate_prediction(prediction, current_state_features)
        v_synthetic_kmph = system3_decision.resolve_effective_speed_cap(synthetic_restrictions)

        # --- D. SYSTEM 1: Evaluate Physical + Synthetic Constraints ---
        active_evts = get_active_events(
            events=events,
            current_time_str=current_time_str,
            current_section_id=current_section_id,
            current_position_km=current_pos_km,
            route_id=route["route_id"]
        )
        physical_constraints = resolve_speed_constraints(active_evts, config)

        # Combine sectional, physical, and System 3 synthetic speed caps
        effective_speed_cap_kmph = min(
            section_limit_kmph,
            physical_constraints["v_signal_kmph"],
            physical_constraints["v_restriction_kmph"],
            physical_constraints["v_congestion_kmph"],
            physical_constraints["v_weather_kmph"],
            v_synthetic_kmph
        )

        # --- E. SYSTEM 1: Physics Acceleration & Target Speed ---
        target_station_km = next_station["distance_from_origin_km"]
        dist_to_next_stn_m = max(0.0, (target_station_km * 1000.0) - current_pos_m)

        station_event = None
        current_station_id = None
        actual_arrival_time = None
        actual_departure_time = None
        actual_dwell_min = None
        arrival_delay_min = None
        departure_delay_min = None

        if dwelling:
            current_station_id = stations[station_idx]["station_id"]
            current_speed_mps = 0.0
            accel_mps2 = 0.0
            dwell_time_remaining_sec -= dt

            if dwell_time_remaining_sec <= 0.0:
                dwelling = False
                station_event = "DEPARTED"
                actual_departure_time = current_time_str
                actual_dwell_min = stations[station_idx]["scheduled_dwell_min"]

        if step == 1 and not dwelling:
            current_station_id = origin["station_id"]
            station_event = "DEPARTED"
            actual_departure_time = current_time_str
            station_arrival_times[origin["station_id"]] = elapsed_sec

        if journey_completed or dwelling:
            v_target_mps = 0.0
            target_speed_kmph = 0.0
            accel_mps2 = 0.0
            approach_spd_kmph = 0.0
        else:
            speed_decision = compute_target_speed(
                section_speed_limit_kmph=effective_speed_cap_kmph,
                constraints=physical_constraints,
                distance_to_next_station_m=dist_to_next_stn_m,
                must_stop_at_next_station=True,
                braking_decel_mps2=max_brake
            )
            v_target_mps = speed_decision["v_target_mps"]
            target_speed_kmph = speed_decision["v_target_kmph"]
            approach_spd_kmph = mps_to_kmph(speed_decision["v_approach_mps"])

            accel_mps2 = compute_acceleration(
                current_speed_mps=current_speed_mps,
                v_target_mps=v_target_mps,
                max_accel_mps2=max_accel,
                max_brake_mps2=max_brake
            )

        # --- F. Kinematic State Update ---
        if not dwelling and not journey_completed:
            current_speed_mps = update_speed(current_speed_mps, accel_mps2, dt)
            if accel_mps2 > 0 and current_speed_mps > v_target_mps:
                current_speed_mps = v_target_mps
            current_pos_m = update_position(current_pos_m, current_speed_mps, accel_mps2, dt)

            # Check station platform arrival
            target_m = target_station_km * 1000.0
            if current_pos_m >= target_m - 10.0:
                current_pos_m = target_m
                current_speed_mps = 0.0
                accel_mps2 = 0.0
                station_idx += 1
                curr_stn = stations[station_idx]
                station_arrival_times[curr_stn["station_id"]] = elapsed_sec

                if curr_stn.get("is_terminal"):
                    journey_completed = True
                    station_event = "ARRIVED"
                    current_station_id = curr_stn["station_id"]
                    actual_arrival_time = current_time_str
                else:
                    dwelling = True
                    dwell_time_remaining_sec = curr_stn["scheduled_dwell_min"] * 60.0
                    station_event = "ARRIVED"
                    current_station_id = curr_stn["station_id"]
                    actual_arrival_time = current_time_str
                    if station_idx < len(stations) - 1:
                        next_station = stations[station_idx + 1]
                    if current_section_idx < len(sections) - 1:
                        current_section_idx += 1
                        current_section = sections[current_section_idx]

        # --- G. Dynamic ETA Calculation ---
        dist_to_dest_km = max(0.0, total_km - current_pos_km)
        dist_to_next_stn_km = max(0.0, next_station["distance_from_origin_km"] - current_pos_km) if not journey_completed else 0.0

        est_speed = max(25.0, current_speed_kmph)
        eta_to_next_stn_min = round(dist_to_next_stn_km / est_speed * 60.0, 1)
        eta_to_dest_min = round(dist_to_dest_km / est_speed * 60.0, 1)

        # GPS & Movement State
        if current_station_id:
            stn = stn_lookup[current_station_id]
            lat, lon = stn["latitude"], stn["longitude"]
        else:
            lat, lon = interpolate_coordinates(current_pos_km, current_section, stn_lookup)

        movement_state = get_movement_state(
            current_speed_mps=current_speed_mps,
            acceleration_mps2=accel_mps2,
            at_station=bool(current_station_id),
            dwelling=dwelling,
            journey_complete=journey_completed
        )

        prev_stn_id = stations[station_idx]["station_id"] if station_idx > 0 else origin["station_id"]
        next_stn_id = next_station["station_id"] if not journey_completed else None

        active_res_desc = ", ".join([r.description for r in synthetic_restrictions if r.status in ["ACTIVE", "UPDATED"]]) or "NONE"

        # --- H. Construct Observation Record ---
        state_obj = TrainState(
            train_id=train_id,
            route_id=route["route_id"],
            simulation_time_sec=elapsed_sec,
            timestamp=current_time_str,
            current_position_km=current_pos_km,
            current_position_m=current_pos_m,
            current_speed_mps=current_speed_mps,
            current_speed_kmph=current_speed_kmph,
            target_speed_kmph=target_speed_kmph,
            current_acceleration_mps2=accel_mps2,
            current_section_id=current_section_id,
            current_station_id=current_station_id,
            previous_station_id=prev_stn_id,
            next_station_id=next_stn_id,
            distance_to_next_station_km=dist_to_next_stn_km,
            distance_to_destination_km=dist_to_dest_km,
            braking_distance_m=compute_braking_distance(current_speed_mps, max_brake),
            movement_state=movement_state,
            station_event=station_event,
            actual_arrival_time=actual_arrival_time,
            actual_departure_time=actual_departure_time,
            actual_dwell_min=actual_dwell_min,
            current_delay_min=current_delay_min,
            arrival_delay_min=arrival_delay_min,
            departure_delay_min=departure_delay_min,
            signal_state=physical_constraints["signal_state"],
            speed_restriction_kmph=v_synthetic_kmph if v_synthetic_kmph < 900 else None,
            congestion_level="HIGH" if prediction.congestion_risk >= 0.70 else ("MEDIUM" if prediction.congestion_risk >= 0.45 else "LOW"),
            fog_active=prediction.fog_risk >= 0.40,
            fog_visibility_km=physical_constraints.get("fog_visibility_km"),
            unscheduled_halt=physical_constraints.get("unscheduled_halt", False),
            active_event_ids=physical_constraints["active_event_ids"],
            latitude=lat,
            longitude=lon,
            data_quality_status="OK"
        )

        obs = generate_observation(
            step=step,
            state=state_obj,
            section_speed_limit_kmph=section_limit_kmph,
            approach_speed_kmph=approach_spd_kmph
        )

        # Attach System 2 & System 3 Prediction Fields
        obs["predicted_congestion_probability"] = prediction.congestion_risk
        obs["predicted_fog_risk"] = prediction.fog_risk
        obs["predicted_delay_risk"] = prediction.delay_risk
        obs["predicted_speed_impact"] = prediction.expected_speed_impact
        obs["active_predicted_restriction"] = active_res_desc
        obs["predicted_restriction_speed_kmph"] = v_synthetic_kmph
        obs["eta_to_next_station_min"] = eta_to_next_stn_min
        obs["eta_to_destination_min"] = eta_to_dest_min
        obs["prediction_timestamp"] = current_time_str
        obs["prediction_horizon_min"] = 30.0
        obs["prediction_source"] = prediction.prediction_source

        observations.append(obs)

        if journey_completed:
            break

        elapsed_sec += dt
        step += 1

    # --- I. Post-Processing: Target Label Generation (Ground Truth) ---
    actual_total_journey_sec = elapsed_sec
    terminal_id = terminal["station_id"]

    for obs in observations:
        obs_sec = float(obs.get("simulation_time_sec", 0.0))
        # Target ETA to destination = actual terminal arrival time - current observation time
        target_dest_min = max(0.0, (actual_total_journey_sec - obs_sec) / 60.0)
        obs["target_eta_to_destination_min"] = round(target_dest_min, 1)

        # Target ETA to next station
        next_stn = obs["next_station_id"]
        if next_stn and next_stn in station_arrival_times:
            arr_sec = station_arrival_times[next_stn]
            target_next_min = max(0.0, (arr_sec - obs_sec) / 60.0)
            obs["target_eta_to_next_station_min"] = round(target_next_min, 1)
        else:
            obs["target_eta_to_next_station_min"] = 0.0

    # --- J. Data Validation & Export ---
    is_valid, errors = validate_observations(observations, route)
    if not is_valid:
        print(f"[Closed-Loop Orchestrator] WARNING: 17-point validation reported {len(errors)} issues:")
        for err in errors[:3]:
            print(f"  - {err}")
    else:
        print("[Closed-Loop Orchestrator] Validation Gate: PASS (All 17 integrity rules verified)")

    out_csv = Path(output_csv_path)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    write_observations_to_csv(observations, str(out_csv))

    # Also save copy to Data/ml/ml_ready_dataset.csv
    ml_csv = PROJECT_ROOT / "Data" / "ml" / "ml_ready_dataset.csv"
    ml_csv.parent.mkdir(parents=True, exist_ok=True)
    write_observations_to_csv(observations, str(ml_csv))

    print(f"[Closed-Loop Orchestrator] Synthetic Journey Complete.")
    print(f"  - Total 30s Observations Recorded : {len(observations)}")
    print(f"  - Actual Journey Time              : {actual_total_journey_sec / 60.0:.1f} min (Scheduled: {route['total_scheduled_duration_min']} min)")
    print(f"  - Final Journey Delay              : {observations[-1]['current_delay_min']:.1f} min")
    print(f"  - Saved RTIS Observation CSV       : {out_csv}")
    print(f"  - Saved ML-Ready Dataset CSV       : {ml_csv}")

    return observations


if __name__ == "__main__":
    build_synthetic_journey()
