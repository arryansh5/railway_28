"""
simulation_engine.py — Phase 3: Physics-Based RTIS Simulator
The main simulation orchestrator. Runs the 30-second physics loop, manages train lifecycle,
coordinates speed constraints, interpolates GPS, validates data, and exports logs.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional

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


def _format_time(base_time_str: str, elapsed_seconds: float) -> str:
    """Calculates HH:MM:SS by adding elapsed seconds to a base time string."""
    base_dt = datetime.strptime(base_time_str, "%H:%M:%S")
    current_dt = base_dt + timedelta(seconds=elapsed_seconds)
    return current_dt.strftime("%H:%M:%S")


def _calculate_delay_min(
    elapsed_seconds: float,
    station: dict,
    is_arrival: bool
) -> float:
    """Calculates delay in minutes against scheduled arrival/departure offset."""
    scheduled_offset_sec = (
        station["scheduled_arrival_offset_min"] if is_arrival
        else station["scheduled_departure_offset_min"]
    ) * 60.0
    return (elapsed_seconds - scheduled_offset_sec) / 60.0


def run_simulation(
    route_filepath: str = r"D:\Projects\railway\Data\routes\delhi_dehradun_route.json",
    config_filepath: str = r"D:\Projects\railway\src\simulator\config\simulator_config.json",
    events_filepath: str = r"D:\Projects\railway\src\simulator\events\simulation_events.json",
    start_time_str: str = "06:45:00",
    train_id: str = "12017"
) -> List[Dict]:
    """
    Executes a complete synthetic journey simulation.
    """
    # 1. Load Route, Config & Events
    route = load_route(route_filepath)
    config = load_config(config_filepath)
    events = load_events(events_filepath)

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

    # 2. Simulation State Initialization
    elapsed_sec = 0.0
    current_pos_m = 0.0
    current_speed_mps = 0.0
    target_speed_kmph = 0.0
    accel_mps2 = 0.0

    station_idx = 0
    next_station = stations[1]
    current_section_idx = 0
    current_section = sections[0]

    dwelling = False
    dwell_time_remaining_sec = 0.0
    journey_completed = False

    observations = []
    step = 1

    while not journey_completed and elapsed_sec < 43200:  # 12-hour max run
        current_time_str = _format_time(start_time_str, elapsed_sec)

        station_event = None
        current_station_id = None
        actual_arrival_time = None
        actual_departure_time = None
        actual_dwell_min = None
        arrival_delay_min = None
        departure_delay_min = None

        # --- 3. Dwell Countdown & Departure Handling ---
        if dwelling:
            current_station_id = stations[station_idx]["station_id"]
            current_speed_mps = 0.0
            accel_mps2 = 0.0
            dwell_time_remaining_sec -= dt

            if dwell_time_remaining_sec <= 0.0:
                dwelling = False
                station_event = "DEPARTED"
                actual_departure_time = current_time_str
                departure_delay_min = _calculate_delay_min(elapsed_sec, stations[station_idx], is_arrival=False)
                actual_dwell_min = stations[station_idx]["scheduled_dwell_min"]

        # Initial origin departure event on tick 1
        if step == 1 and not dwelling:
            current_station_id = origin["station_id"]
            station_event = "DEPARTED"
            actual_departure_time = current_time_str
            departure_delay_min = 0.0

        # --- 4. Section and Speed Limit ---
        current_section_id = current_section["section_id"] if not dwelling and not journey_completed else None
        section_limit_kmph = current_section["max_sectional_speed_kmph"] if current_section else 0.0

        # Distance to next station platform
        target_station_km = next_station["distance_from_origin_km"]
        dist_to_next_stn_m = max(0.0, (target_station_km * 1000.0) - current_pos_m)

        # --- 5. Event Constraints ---
        active_evts = get_active_events(
            events=events,
            current_time_str=current_time_str,
            current_section_id=current_section_id or "",
            current_position_km=current_pos_m / 1000.0,
            route_id=route["route_id"]
        )
        constraints = resolve_speed_constraints(active_evts, config)

        # --- 6. Speed Controller & Physics Acceleration ---
        if journey_completed:
            v_target_mps = 0.0
            target_speed_kmph = 0.0
            accel_mps2 = 0.0
            current_speed_mps = 0.0
            approach_spd_kmph = 0.0
        elif dwelling:
            v_target_mps = 0.0
            target_speed_kmph = 0.0
            accel_mps2 = 0.0
            approach_spd_kmph = 0.0
        else:
            speed_decision = compute_target_speed(
                section_speed_limit_kmph=section_limit_kmph,
                constraints=constraints,
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

        # --- 7. Kinematic Update (if in transit) ---
        if not dwelling and not journey_completed:
            current_speed_mps = update_speed(current_speed_mps, accel_mps2, dt)
            if accel_mps2 > 0 and current_speed_mps > v_target_mps:
                current_speed_mps = v_target_mps
            current_pos_m = update_position(current_pos_m, current_speed_mps, accel_mps2, dt)

            # Check if train arrived at next station platform
            target_m = target_station_km * 1000.0
            if current_pos_m >= target_m - 10.0:
                current_pos_m = target_m
                current_speed_mps = 0.0
                accel_mps2 = 0.0
                station_idx += 1
                curr_stn = stations[station_idx]

                if curr_stn.get("is_terminal"):
                    journey_completed = True
                    station_event = "ARRIVED"
                    current_station_id = curr_stn["station_id"]
                    actual_arrival_time = current_time_str
                    arrival_delay_min = _calculate_delay_min(elapsed_sec, curr_stn, is_arrival=True)
                else:
                    dwelling = True
                    
                    base_dwell_sec = curr_stn["scheduled_dwell_min"] * 60.0
                    scheduled_dep_sec = curr_stn["scheduled_departure_offset_min"] * 60.0
                    projected_dep_sec = elapsed_sec + base_dwell_sec
                    
                    if projected_dep_sec < scheduled_dep_sec:
                        dwell_time_remaining_sec = scheduled_dep_sec - elapsed_sec
                    else:
                        dwell_time_remaining_sec = base_dwell_sec
                        
                    station_event = "ARRIVED"
                    current_station_id = curr_stn["station_id"]
                    actual_arrival_time = current_time_str
                    arrival_delay_min = _calculate_delay_min(elapsed_sec, curr_stn, is_arrival=True)
                    if station_idx < len(stations) - 1:
                        next_station = stations[station_idx + 1]
                    if current_section_idx < len(sections) - 1:
                        current_section_idx += 1
                        current_section = sections[current_section_idx]

        current_pos_km = current_pos_m / 1000.0
        dist_to_dest_km = max(0.0, total_km - current_pos_km)
        dist_to_next_stn_km = max(0.0, next_station["distance_from_origin_km"] - current_pos_km) if not journey_completed else 0.0

        current_speed_kmph = mps_to_kmph(current_speed_mps)
        braking_dist_m = compute_braking_distance(current_speed_mps, max_brake)

        # --- 8. GPS Interpolation ---
        if current_station_id:
            stn = stn_lookup[current_station_id]
            lat, lon = stn["latitude"], stn["longitude"]
        else:
            lat, lon = interpolate_coordinates(current_pos_km, current_section, stn_lookup)

        # --- 9. Movement State ---
        movement_state = get_movement_state(
            current_speed_mps=current_speed_mps,
            acceleration_mps2=accel_mps2,
            at_station=bool(current_station_id),
            dwelling=dwelling,
            journey_complete=journey_completed
        )

        current_delay_min = (elapsed_sec / 60.0) - (current_pos_km / total_km * route["total_scheduled_duration_min"])

        # --- 10. Construct TrainState & Observation ---
        prev_stn_id = stations[station_idx]["station_id"] if station_idx > 0 else origin["station_id"]
        next_stn_id = next_station["station_id"] if not journey_completed else None

        state = TrainState(
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
            braking_distance_m=braking_dist_m,
            movement_state=movement_state,
            station_event=station_event,
            actual_arrival_time=actual_arrival_time,
            actual_departure_time=actual_departure_time,
            actual_dwell_min=actual_dwell_min,
            current_delay_min=current_delay_min,
            arrival_delay_min=arrival_delay_min,
            departure_delay_min=departure_delay_min,
            signal_state=constraints["signal_state"],
            speed_restriction_kmph=constraints["v_restriction_kmph"] if constraints["v_restriction_kmph"] < 900 else None,
            congestion_level=constraints["congestion_level"],
            fog_active=constraints["fog_active"],
            fog_visibility_km=constraints["fog_visibility_km"],
            unscheduled_halt=constraints["unscheduled_halt"],
            active_event_ids=constraints["active_event_ids"],
            latitude=lat,
            longitude=lon,
            data_quality_status="OK"
        )

        obs = generate_observation(
            step=step,
            state=state,
            section_speed_limit_kmph=section_limit_kmph,
            approach_speed_kmph=approach_spd_kmph
        )
        observations.append(obs)

        if journey_completed:
            break

        elapsed_sec += dt
        step += 1

    # --- 11. 17-Rule Data Validation ---
    is_valid, errors = validate_observations(observations, route)
    if not is_valid:
        print(f"[SimulationEngine] WARNING: Validation reported {len(errors)} issues:")
        for err in errors[:5]:
            print(f"  - {err}")
    else:
        print("[SimulationEngine] Validation Gate: PASS (All 17 integrity rules verified)")

    # --- 12. Export to CSV & JSON ---
    csv_path = config["output"].get("csv_filepath", "Data/simulations/simulation_output.csv")
    json_path = config["output"].get("json_filepath", "Data/simulations/simulation_output.json")
    write_observations_to_csv(observations, csv_path)
    write_observations_to_json(observations, json_path)

    print(f"[SimulationEngine] Simulation Complete.")
    print(f"  - Total Observations: {len(observations)}")
    print(f"  - Total Journey Time: {elapsed_sec / 60.0:.1f} minutes (Scheduled: {route['total_scheduled_duration_min']} min)")
    print(f"  - Final Arrival Time: {observations[-1]['timestamp']}")
    print(f"  - Final Delay       : {observations[-1]['current_delay_min']:.1f} minutes")
    print(f"  - Saved to CSV      : {csv_path}")
    print(f"  - Saved to JSON     : {json_path}")

    return observations


if __name__ == "__main__":
    print("=== Running Delhi-Dehradun RTIS Simulation ===")
    run_simulation()
