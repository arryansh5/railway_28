"""
dataset_builder.py — Phase 6: Step 6
Full 30-Second Closed-Loop Orchestrator & Synthetic Dataset Generator.

Coordinates:
- SYSTEM 1: RTIS / Physics Simulator (kinematics, speed controller, station lifecycle, GPS interpolation)
- SYSTEM 2: Delay Risk Predictor (probabilistic condition risk evaluation at timestamp t)
- SYSTEM 3: Dynamic Restriction Engine (state machine: CREATE, UPDATE, DOWNGRADE, EXPIRE)

Order of Operations (every 30 seconds):
System 1 (State t) -> System 2 (Risk Prediction) -> System 3 (Decision / Speed Cap) -> System 1 (Physics 30s) -> Dynamic ETA -> Log Row -> Repeat

Anti-Leakage Guaranteed:
System 2 consumes ONLY current features at timestamp t.
Target labels (target_eta_to_destination_min, target_eta_to_next_station_min) are strictly back-populated AFTER journey completion.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

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

from src.data_generator.prediction_engine import BaselinePredictiveEngine, BasePredictor, ConditionPrediction
from src.data_generator.restriction_engine import RestrictionEngine, RestrictionDecision

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
    journey_id: str = "JRN_0001",
    season: str = "Winter/Fog",
    zone: str = "NR",
    output_csv_path: str = str(PROJECT_ROOT / "Data" / "synthetic_rtis" / "synthetic_journey_01.csv"),
    output_json_path: str = str(PROJECT_ROOT / "Data" / "synthetic_rtis" / "synthetic_journey_01.json"),
    predictor: Optional[BasePredictor] = None,
    max_steps: Optional[int] = None,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Executes a complete 30-second closed-loop journey combining System 1, System 2, and System 3.
    """
    if verbose:
        print("\n" + "=" * 80)
        print("      FULL 30-SECOND CLOSED-LOOP SIMULATION: NDLS -> DDN CORRIDOR")
        print("=" * 80)
        print(f"  Journey ID       : {journey_id}")
        print(f"  Start Time       : {start_time_str}")
        print(f"  Season           : {season}")
        print(f"  Zone             : {zone}")

    # 1. Load Route, Configuration & Events
    route = load_route(route_filepath)
    config = load_config(config_filepath)
    events = load_events(events_filepath)

    # 2. Instantiate System 2 Predictor & System 3 Restriction Engine
    system2_engine = predictor or BaselinePredictiveEngine(calibration_filepath)
    system3_engine = RestrictionEngine(calibration_filepath)

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

    observations: List[Dict[str, Any]] = []
    step = 1
    station_arrival_times: Dict[str, float] = {}

    # Tracking metrics
    stats = {
        "create_actions": 0,
        "update_actions": 0,
        "downgrade_actions": 0,
        "expire_actions": 0,
        "total_cycles": 0,
    }

    # Main 30-Second Closed Loop
    while not journey_completed and elapsed_sec < 43200:  # 12-hour timeout safety
        if max_steps is not None and step > max_steps:
            break

        current_time_str = _format_time(start_time_str, elapsed_sec)
        current_pos_km = current_pos_m / 1000.0
        current_speed_kmph = mps_to_kmph(current_speed_mps)

        # -------------------------------------------------------------
        # 1. SYSTEM 1: Current State Extraction (timestamp t)
        # -------------------------------------------------------------
        current_section_id = current_section["section_id"] if current_section and not journey_completed else None
        section_limit_kmph = current_section["max_sectional_speed_kmph"] if current_section else 0.0
        
        # Calculate current delay against scheduled timetable progress
        current_delay_min = (elapsed_sec / 60.0) - (current_pos_km / total_km * route["total_scheduled_duration_min"])

        # Strict Safe State Input (Zero Future Fields)
        safe_current_state = {
            "timestamp": current_time_str,
            "current_position_km": current_pos_km,
            "current_speed_kmph": current_speed_kmph,
            "current_delay_min": current_delay_min,
            "current_section_id": current_section_id,
            "current_station_id": stations[station_idx]["station_id"] if dwelling else None,
            "departure_hour": int(current_time_str.split(":")[0]),
            "season": season,
            "zone": zone,
            "late_incoming_rake": False,
        }

        # -------------------------------------------------------------
        # 2. SYSTEM 2: Predict Operational Risks (Based ONLY on state t)
        # -------------------------------------------------------------
        prediction: ConditionPrediction = system2_engine.predict(
            current_state=safe_current_state,
            context={"season": season, "zone": zone, "prediction_horizon_min": 30.0}
        )

        # -------------------------------------------------------------
        # 3. SYSTEM 3: Dynamic Decision & Restriction State Machine
        # -------------------------------------------------------------
        decision: RestrictionDecision = system3_engine.evaluate_and_decide(
            prediction=prediction,
            current_state=safe_current_state
        )

        # Update action stats
        if decision.action == "CREATE":
            stats["create_actions"] += 1
        elif decision.action == "UPDATE":
            stats["update_actions"] += 1
        elif decision.action == "DOWNGRADE":
            stats["downgrade_actions"] += 1
        elif decision.action == "EXPIRE":
            stats["expire_actions"] += 1

        v_synthetic_cap_kmph = decision.effective_speed_cap_kmph

        # -------------------------------------------------------------
        # 4. SYSTEM 1: Evaluate Physical + Synthetic Constraints
        # -------------------------------------------------------------
        active_evts = get_active_events(
            events=events,
            current_time_str=current_time_str,
            current_section_id=current_section_id,
            current_position_km=current_pos_km,
            route_id=route["route_id"]
        )
        physical_constraints = resolve_speed_constraints(active_evts, config)

        # Effective Target Speed Cap = min(Section, Signal, TSR, Congestion, Weather, System 3 Synthetic Cap)
        effective_speed_cap_kmph = min(
            section_limit_kmph,
            physical_constraints["v_signal_kmph"],
            physical_constraints["v_restriction_kmph"],
            physical_constraints["v_congestion_kmph"],
            physical_constraints["v_weather_kmph"],
            v_synthetic_cap_kmph
        )

        # -------------------------------------------------------------
        # 5. SYSTEM 1: Physics Acceleration, Braking & Target Speed
        # -------------------------------------------------------------
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

        # -------------------------------------------------------------
        # 6. SYSTEM 1: Kinematic Advancement (30-second Integration)
        # -------------------------------------------------------------
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

        # -------------------------------------------------------------
        # 7. SYSTEM 1: Dynamic ETA & GPS Interpolation
        # -------------------------------------------------------------
        dist_to_dest_km = max(0.0, total_km - (current_pos_m / 1000.0))
        dist_to_next_stn_km = max(0.0, next_station["distance_from_origin_km"] - (current_pos_m / 1000.0)) if not journey_completed else 0.0

        est_speed = max(25.0, mps_to_kmph(current_speed_mps))
        eta_to_next_stn_min = round(dist_to_next_stn_km / est_speed * 60.0, 1)
        eta_to_dest_min = round(dist_to_dest_km / est_speed * 60.0, 1)

        # Live Continuous GPS Coordinates
        if current_station_id:
            stn = stn_lookup[current_station_id]
            lat, lon = stn["latitude"], stn["longitude"]
        else:
            lat, lon = interpolate_coordinates(current_pos_m / 1000.0, current_section, stn_lookup)

        movement_state = get_movement_state(
            current_speed_mps=current_speed_mps,
            acceleration_mps2=accel_mps2,
            at_station=bool(current_station_id),
            dwelling=dwelling,
            journey_complete=journey_completed
        )

        prev_stn_id = stations[station_idx]["station_id"] if station_idx > 0 else origin["station_id"]
        next_stn_id = next_station["station_id"] if not journey_completed else None

        active_res_desc = ", ".join([r.description for r in decision.active_restrictions if r.status in ["ACTIVE", "UPDATED", "UNCHANGED"]]) or "NONE"

        # -------------------------------------------------------------
        # 8. Log 30-Second Observation Record
        # -------------------------------------------------------------
        state_obj = TrainState(
            train_id=train_id,
            route_id=route["route_id"],
            simulation_time_sec=elapsed_sec,
            timestamp=current_time_str,
            current_position_km=round(current_pos_m / 1000.0, 3),
            current_position_m=round(current_pos_m, 2),
            current_speed_mps=round(current_speed_mps, 2),
            current_speed_kmph=round(mps_to_kmph(current_speed_mps), 2),
            target_speed_kmph=round(target_speed_kmph, 2),
            current_acceleration_mps2=round(accel_mps2, 3),
            current_section_id=current_section_id,
            current_station_id=current_station_id,
            previous_station_id=prev_stn_id,
            next_station_id=next_stn_id,
            distance_to_next_station_km=round(dist_to_next_stn_km, 3),
            distance_to_destination_km=round(dist_to_dest_km, 3),
            braking_distance_m=round(compute_braking_distance(current_speed_mps, max_brake), 2),
            movement_state=movement_state,
            station_event=station_event,
            actual_arrival_time=actual_arrival_time,
            actual_departure_time=actual_departure_time,
            actual_dwell_min=actual_dwell_min,
            current_delay_min=round(current_delay_min, 2),
            arrival_delay_min=arrival_delay_min,
            departure_delay_min=departure_delay_min,
            signal_state=physical_constraints["signal_state"],
            speed_restriction_kmph=v_synthetic_cap_kmph if v_synthetic_cap_kmph < 900 else None,
            congestion_level="HIGH" if prediction.congestion_risk >= 0.70 else ("MEDIUM" if prediction.congestion_risk >= 0.45 else "LOW"),
            fog_active=prediction.fog_risk >= 0.40,
            fog_visibility_km=physical_constraints.get("fog_visibility_km"),
            unscheduled_halt=physical_constraints.get("unscheduled_halt", False),
            active_event_ids=physical_constraints["active_event_ids"],
            latitude=round(lat, 6),
            longitude=round(lon, 6),
            data_quality_status="OK"
        )

        obs = generate_observation(
            step=step,
            state=state_obj,
            section_speed_limit_kmph=section_limit_kmph,
            approach_speed_kmph=approach_spd_kmph
        )

        # Attach System 2 & 3 Fields
        obs["journey_id"] = journey_id
        obs["predicted_congestion_probability"] = prediction.congestion_risk
        obs["predicted_fog_risk"] = prediction.fog_risk
        obs["predicted_delay_risk"] = prediction.delay_risk
        obs["predicted_operational_risk"] = prediction.operational_risk
        obs["prediction_confidence"] = prediction.confidence
        obs["predicted_speed_impact"] = prediction.expected_speed_impact
        obs["active_predicted_restriction"] = active_res_desc
        obs["predicted_restriction_speed_kmph"] = v_synthetic_cap_kmph if v_synthetic_cap_kmph < 900 else None
        obs["eta_to_next_station_min"] = eta_to_next_stn_min
        obs["eta_to_destination_min"] = eta_to_dest_min
        obs["prediction_timestamp"] = current_time_str
        obs["prediction_horizon_min"] = 30.0
        obs["prediction_source"] = prediction.prediction_source

        observations.append(obs)
        stats["total_cycles"] = step

        if verbose and (step % 50 == 0 or journey_completed or decision.action in ["CREATE", "UPDATE", "EXPIRE"]):
            print(f"[{current_time_str}] Pos: {current_pos_km:5.1f}km | Speed: {mps_to_kmph(current_speed_mps):5.1f}km/h | Sys2 (Fog={prediction.fog_risk:.2f}, Cong={prediction.congestion_risk:.2f}) | Sys3 ({decision.action}) -> Cap: {effective_speed_cap_kmph:5.1f}km/h")

        if journey_completed:
            break

        elapsed_sec += dt
        step += 1

    # -------------------------------------------------------------
    # 9. POST-SIMULATION: Ground Truth Target Back-Population (Anti-Leakage Guaranteed)
    # -------------------------------------------------------------
    actual_total_journey_sec = elapsed_sec
    final_arrival_timestamp = _format_time(start_time_str, elapsed_sec)

    for obs in observations:
        obs_sec = float(obs.get("simulation_time_sec", 0.0))
        target_dest_min = max(0.0, (actual_total_journey_sec - obs_sec) / 60.0)
        obs["target_eta_to_destination_min"] = round(target_dest_min, 1)

        next_stn = obs["next_station_id"]
        if next_stn and next_stn in station_arrival_times:
            arr_sec = station_arrival_times[next_stn]
            target_next_min = max(0.0, (arr_sec - obs_sec) / 60.0)
            obs["target_eta_to_next_station_min"] = round(target_next_min, 1)
        else:
            obs["target_eta_to_next_station_min"] = 0.0

    # 10. Validation & File Export
    is_valid, errors = validate_observations(observations, route)

    # Save CSV
    out_csv = Path(output_csv_path)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    write_observations_to_csv(observations, str(out_csv))

    # Save JSON trace
    out_json = Path(output_json_path)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({
            "journey_id": journey_id,
            "route_id": route["route_id"],
            "start_time": start_time_str,
            "arrival_time": final_arrival_timestamp,
            "total_duration_min": round(actual_total_journey_sec / 60.0, 1),
            "total_observations": len(observations),
            "stats": stats,
            "observations": observations
        }, f, indent=2)

    # Save ML Ready dataset
    ml_csv = PROJECT_ROOT / "Data" / "ml" / "ml_ready_dataset.csv"
    ml_csv.parent.mkdir(parents=True, exist_ok=True)
    write_observations_to_csv(observations, str(ml_csv))

    if verbose:
        print("\n" + "=" * 80)
        print("      CLOSED-LOOP SIMULATION COMPLETE")
        print("=" * 80)
        print(f"  Total 30s Cycles             : {len(observations)}")
        print(f"  Final Arrival Time           : {final_arrival_timestamp} ({actual_total_journey_sec / 60.0:.1f} min)")
        print(f"  System 3 Actions (C/U/D/E)   : {stats['create_actions']}/{stats['update_actions']}/{stats['downgrade_actions']}/{stats['expire_actions']}")
        print(f"  17-Point Validation Status   : {'PASS (100% Verified)' if is_valid else f'WARNING ({len(errors)} errors)'}")
        print(f"  Output CSV                   : {out_csv}")
        print(f"  Output JSON Trace            : {out_json}")
        print(f"  ML-Ready Dataset CSV         : {ml_csv}")

    return {
        "journey_id": journey_id,
        "observations": observations,
        "stats": stats,
        "actual_duration_min": actual_total_journey_sec / 60.0,
        "final_arrival_time": final_arrival_timestamp,
        "is_valid": is_valid
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run 30-second closed-loop simulation on a specified corridor.")
    parser.add_argument("--route", type=str, default=str(PROJECT_ROOT / "Data" / "routes" / "delhi_dehradun_route.json"), help="Route JSON filepath")
    parser.add_argument("--events", type=str, default=str(PROJECT_ROOT / "src" / "simulator" / "events" / "simulation_events.json"), help="Events JSON filepath")
    parser.add_argument("--train-id", type=str, default="12017", help="Train number / ID")
    parser.add_argument("--journey-id", type=str, default="JRN_0001", help="Journey ID")
    parser.add_argument("--start-time", type=str, default="06:45:00", help="Departure start time (HH:MM:SS)")
    parser.add_argument("--season", type=str, default="Winter/Fog", help="Season environment")
    parser.add_argument("--zone", type=str, default="NR", help="Geographic railway zone (NR / NCR)")
    parser.add_argument("--output-csv", type=str, default=str(PROJECT_ROOT / "Data" / "synthetic_rtis" / "synthetic_journey_01.csv"), help="Output CSV path")
    parser.add_argument("--output-json", type=str, default=str(PROJECT_ROOT / "Data" / "synthetic_rtis" / "synthetic_journey_01.json"), help="Output JSON path")

    args = parser.parse_args()

    build_synthetic_journey(
        route_filepath=args.route,
        events_filepath=args.events,
        train_id=args.train_id,
        journey_id=args.journey_id,
        start_time_str=args.start_time,
        season=args.season,
        zone=args.zone,
        output_csv_path=args.output_csv,
        output_json_path=args.output_json
    )
