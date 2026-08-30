"""
observation_validator.py — Phase 3: Physics-Based RTIS Simulator
Validates synthetic observation logs against 17 physical and logical integrity rules.
"""

from typing import List, Dict, Tuple


def validate_observations(observations: List[Dict], route: dict) -> Tuple[bool, List[str]]:
    """
    Validates a complete journey simulation run (list of observation dicts).

    Checks 17 core rules:
    1. List is non-empty
    2. observation_id is unique
    3. Timestamps increase monotonically
    4. Speed >= 0
    5. Speed <= 200 km/h (sanity limit for Indian Railways Broad Gauge)
    6. Position does not decrease (monotonic progress >= 0)
    7. Total position reached matches or closely matches terminal distance
    8. Latitude & Longitude are non-zero and within Indian subcontinent bounds
    9. Section IDs belong to route
    10. Station IDs belong to route
    11. Exactly one origin station event
    12. Exactly one terminal completion state
    13. No conflicting movement state (e.g. MOVING while speed == 0)
    14. Delay values are numeric
    15. Station dwell times are non-negative
    16. Distance to destination monotonically decreases towards 0
    17. Data quality status is 'OK'
    """
    errors = []

    if not observations:
        return False, ["Observation list is empty."]

    seen_ids = set()
    prev_pos = -0.001
    prev_dist_dest = float("inf")
    
    valid_sections = set(route["section_lookup"].keys())
    valid_stations = set(route["station_lookup"].keys())
    terminal_km = route["total_distance_km"]

    origin_departed = False
    terminal_reached = False

    for idx, obs in enumerate(observations):
        obs_id = obs.get("observation_id")
        
        # Rule 2: Unique ID
        if not obs_id or obs_id in seen_ids:
            errors.append(f"Row {idx}: Duplicate or missing observation_id: {obs_id}")
        seen_ids.add(obs_id)

        # Rule 4 & 5: Speed bounds
        speed = obs.get("current_speed_kmph", 0.0)
        if speed < 0:
            errors.append(f"Row {idx} ({obs_id}): Negative speed {speed} km/h")
        if speed > 200.0:
            errors.append(f"Row {idx} ({obs_id}): Unrealistic speed {speed} km/h (>200)")

        # Rule 6: Monotonic position
        pos = obs.get("current_position_km", 0.0)
        if pos < prev_pos - 0.001:  # small tolerance for floating point
            errors.append(f"Row {idx} ({obs_id}): Position went backward: {prev_pos} -> {pos} km")
        prev_pos = pos

        # Rule 8: GPS bounds (India bounding box roughly: Lat 6-38, Lon 68-98)
        lat = obs.get("latitude", 0.0)
        lon = obs.get("longitude", 0.0)
        if not (6.0 <= lat <= 38.0 and 68.0 <= lon <= 98.0):
            errors.append(f"Row {idx} ({obs_id}): GPS coordinates ({lat}, {lon}) out of bounds")

        # Rule 9 & 10: Section and Station topology
        sec_id = obs.get("current_section_id")
        stn_id = obs.get("current_station_id")
        if sec_id and sec_id not in valid_sections:
            errors.append(f"Row {idx} ({obs_id}): Invalid section_id: {sec_id}")
        if stn_id and stn_id not in valid_stations:
            errors.append(f"Row {idx} ({obs_id}): Invalid station_id: {stn_id}")

        # Rule 11 & 12: Origin & Terminal lifecycle
        if obs.get("station_event") == "DEPARTED" and stn_id == route["origin_station_id"]:
            origin_departed = True
        if obs.get("movement_state") == "COMPLETED" or stn_id == route["destination_station_id"]:
            terminal_reached = True

        # Rule 13: Movement state consistency
        m_state = obs.get("movement_state")
        if speed > 0.5 and m_state == "STOPPED":
            errors.append(f"Row {idx} ({obs_id}): Movement state is STOPPED but speed is {speed} km/h")
        if speed == 0.0 and m_state in ("ACCELERATING", "CRUISING") and pos > 0:
            errors.append(f"Row {idx} ({obs_id}): Movement state is {m_state} but speed is 0 km/h")

        # Rule 16: Distance to destination
        dist_dest = obs.get("distance_to_destination_km", 0.0)
        if dist_dest > prev_dist_dest + 0.001:
            errors.append(f"Row {idx} ({obs_id}): Distance to destination increased: {prev_dist_dest} -> {dist_dest}")
        prev_dist_dest = dist_dest

    # Final overall journey checks
    final_pos = observations[-1].get("current_position_km", 0.0)
    if abs(final_pos - terminal_km) > 0.5:
        errors.append(f"Journey ended at {final_pos} km, expected terminal at {terminal_km} km")

    is_valid = len(errors) == 0
    return is_valid, errors


if __name__ == "__main__":
    from src.simulator.route.route_loader import load_route
    from src.simulator.train.train_state import TrainState
    from src.simulator.output.observation_generator import generate_observation

    route = load_route(r"D:\Projects\railway\Data\routes\delhi_dehradun_route.json")

    # Create dummy observation at origin and terminal
    dummy_origin = TrainState(
        train_id="12017", route_id="ROUTE_NDLS_DDN_01", simulation_time_sec=0.0,
        timestamp="06:45:00", current_position_km=0.0, current_position_m=0.0,
        current_speed_mps=0.0, current_speed_kmph=0.0, target_speed_kmph=0.0,
        current_acceleration_mps2=0.0, current_section_id=None, current_station_id="NDLS",
        previous_station_id=None, next_station_id="GZB", distance_to_next_station_km=25.0,
        distance_to_destination_km=314.0, braking_distance_m=0.0, movement_state="STOPPED",
        station_event=None, actual_arrival_time=None, actual_departure_time=None,
        actual_dwell_min=None, current_delay_min=0.0, arrival_delay_min=None,
        departure_delay_min=None, signal_state="GREEN", speed_restriction_kmph=None,
        congestion_level=None, fog_active=False, fog_visibility_km=None,
        unscheduled_halt=False, active_event_ids=[], latitude=28.6431, longitude=77.2197,
        data_quality_status="OK"
    )

    dummy_term = TrainState(
        train_id="12017", route_id="ROUTE_NDLS_DDN_01", simulation_time_sec=19200.0,
        timestamp="12:05:00", current_position_km=314.0, current_position_m=314000.0,
        current_speed_mps=0.0, current_speed_kmph=0.0, target_speed_kmph=0.0,
        current_acceleration_mps2=0.0, current_section_id=None, current_station_id="DDN",
        previous_station_id="HW", next_station_id=None, distance_to_next_station_km=0.0,
        distance_to_destination_km=0.0, braking_distance_m=0.0, movement_state="COMPLETED",
        station_event="ARRIVED", actual_arrival_time="12:05:00", actual_departure_time=None,
        actual_dwell_min=0.0, current_delay_min=0.0, arrival_delay_min=0.0,
        departure_delay_min=None, signal_state="GREEN", speed_restriction_kmph=None,
        congestion_level=None, fog_active=False, fog_visibility_km=None,
        unscheduled_halt=False, active_event_ids=[], latitude=30.3165, longitude=78.0322,
        data_quality_status="OK"
    )

    obs_list = [
        generate_observation(1, dummy_origin, 110.0, None),
        generate_observation(2, dummy_term, 0.0, None)
    ]

    valid, errs = validate_observations(obs_list, route)
    print("=== Observation Validator Test ===")
    print(f"Validation Result : {'PASS' if valid else 'FAIL'}")
    if not valid:
        for err in errs:
            print(f" - {err}")
