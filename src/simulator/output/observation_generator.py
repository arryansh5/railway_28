"""
observation_generator.py — Phase 3: Physics-Based RTIS Simulator
Converts internal TrainState and context into a standardized RTIS-like observation dictionary.
"""

from typing import Optional
from src.simulator.train.train_state import TrainState


def generate_observation(
    step: int,
    state: TrainState,
    section_speed_limit_kmph: float = 0.0,
    approach_speed_kmph: Optional[float] = None
) -> dict:
    """
    Constructs a complete RTIS observation payload from TrainState.

    Parameters:
    - step: Simulation tick sequence number (1, 2, 3...)
    - state: Current TrainState dataclass
    - section_speed_limit_kmph: Speed limit of active section
    - approach_speed_kmph: Computed braking approach speed cap (if applicable)

    Returns:
    - Standardized observation dictionary ready for JSON/CSV serialization.
    """
    obs_id = f"OBS_{step:06d}"

    return {
        # --- Observation Metadata ---
        "observation_id": obs_id,
        "timestamp": state.timestamp,
        "simulation_time_sec": round(state.simulation_time_sec, 1),
        "train_id": state.train_id,
        "route_id": state.route_id,
        "data_source": "SYNTHETIC_SIMULATOR",
        "data_quality_status": state.data_quality_status,

        # --- Coordinates (Synthetic GPS) ---
        "latitude": state.latitude,
        "longitude": state.longitude,

        # --- Kinematics (Speeds & Position) ---
        "current_position_km": round(state.current_position_km, 3),
        "current_speed_kmph": round(state.current_speed_kmph, 2),
        "current_speed_mps": round(state.current_speed_mps, 2),
        "target_speed_kmph": round(state.target_speed_kmph, 2),
        "current_acceleration_mps2": round(state.current_acceleration_mps2, 3),
        "braking_distance_m": round(state.braking_distance_m, 1),

        # --- Speed Constraints Context ---
        "section_speed_limit_kmph": round(section_speed_limit_kmph, 2),
        "restriction_speed_kmph": state.speed_restriction_kmph,
        "approach_speed_kmph": round(approach_speed_kmph, 2) if approach_speed_kmph is not None else None,

        # --- Route Topology Tracking ---
        "current_section_id": state.current_section_id,
        "current_station_id": state.current_station_id,
        "previous_station_id": state.previous_station_id,
        "next_station_id": state.next_station_id,
        "distance_to_next_station_km": round(state.distance_to_next_station_km, 3),
        "distance_to_destination_km": round(state.distance_to_destination_km, 3),

        # --- Status & Operational State ---
        "movement_state": state.movement_state,
        "station_event": state.station_event,

        # --- Station Dwell & Timetable ---
        "actual_arrival_time": state.actual_arrival_time,
        "actual_departure_time": state.actual_departure_time,
        "actual_dwell_min": round(state.actual_dwell_min, 2) if state.actual_dwell_min is not None else None,

        # --- Delay Metrics (minutes, can be negative if early) ---
        "current_delay_min": round(state.current_delay_min, 2),
        "arrival_delay_min": round(state.arrival_delay_min, 2) if state.arrival_delay_min is not None else None,
        "departure_delay_min": round(state.departure_delay_min, 2) if state.departure_delay_min is not None else None,

        # --- Environmental / Event Context ---
        "signal_state": state.signal_state or "GREEN",
        "congestion_level": state.congestion_level or "NONE",
        "fog_active": state.fog_active,
        "fog_visibility_km": state.fog_visibility_km,
        "unscheduled_halt": state.unscheduled_halt,
        "active_event_ids": ",".join(state.active_event_ids) if state.active_event_ids else ""
    }


if __name__ == "__main__":
    # Test generation with a sample TrainState
    sample_state = TrainState(
        train_id="12017",
        route_id="ROUTE_NDLS_DDN_01",
        simulation_time_sec=900.0,
        timestamp="07:00:00",
        current_position_km=25.0,
        current_position_m=25000.0,
        current_speed_mps=0.0,
        current_speed_kmph=0.0,
        target_speed_kmph=0.0,
        current_acceleration_mps2=0.0,
        current_section_id=None,
        current_station_id="GZB",
        previous_station_id="NDLS",
        next_station_id="MTC",
        distance_to_next_station_km=42.0,
        distance_to_destination_km=289.0,
        braking_distance_m=0.0,
        movement_state="DWELLING",
        station_event="ARRIVED",
        actual_arrival_time="07:00:00",
        actual_departure_time=None,
        actual_dwell_min=0.0,
        current_delay_min=2.0,
        arrival_delay_min=2.0,
        departure_delay_min=None,
        signal_state="GREEN",
        speed_restriction_kmph=None,
        congestion_level=None,
        fog_active=False,
        fog_visibility_km=None,
        unscheduled_halt=False,
        active_event_ids=[],
        latitude=28.6679,
        longitude=77.4378,
        data_quality_status="OK"
    )

    obs = generate_observation(
        step=30,
        state=sample_state,
        section_speed_limit_kmph=110.0,
        approach_speed_kmph=0.0
    )

    print("=== Observation Generator Test ===")
    print(f"Obs ID       : {obs['observation_id']}")
    print(f"Timestamp    : {obs['timestamp']}")
    print(f"Station      : {obs['current_station_id']} (State: {obs['movement_state']})")
    print(f"Delay        : {obs['current_delay_min']} min")
    print(f"Coordinates  : ({obs['latitude']}, {obs['longitude']})")
    print(f"Total Fields : {len(obs)}")
