"""
speed_controller.py — Phase 3: Physics-Based RTIS Simulator
Computes V_target from all active constraints and decides the acceleration
to apply in the next timestep. Calls physics_engine for kinematic math.
"""

import math
from src.simulator.physics.physics_engine import (
    kmph_to_mps,
    mps_to_kmph,
    compute_braking_distance
)

_CRUISING_FACTOR = 0.95   # Train targets 95% of section limit when cruising
_STATION_STOP_M  = 10.0   # Within 10m of station = docking / stopped


def compute_approach_speed(
    distance_to_stop_m: float,
    braking_decel_mps2: float
) -> float:
    """
    Computes the maximum allowed approach speed given remaining distance to a stop point.
    Uses the kinematic equation v = sqrt(2 * a * d) allowing smooth deceleration to 0 at platform.
    """
    if distance_to_stop_m <= _STATION_STOP_M:
        return 0.0
    return math.sqrt(2.0 * braking_decel_mps2 * distance_to_stop_m)


def compute_target_speed(
    section_speed_limit_kmph: float,
    constraints: dict,
    distance_to_next_station_m: float,
    must_stop_at_next_station: bool,
    braking_decel_mps2: float,
    cruising_factor: float = _CRUISING_FACTOR
) -> dict:
    """
    Computes V_target (m/s) as the minimum of all active speed constraints.
    V_target = min(V_section, V_signal, V_restriction, V_weather, V_congestion, V_approach)
    """

    # 1. Section speed limit (cruise at 95% of max)
    v_section_mps = kmph_to_mps(section_speed_limit_kmph) * cruising_factor

    # 2. Signal constraint
    v_signal_mps = kmph_to_mps(constraints.get("v_signal_kmph", 999.0))

    # 3. TSR / Speed restriction constraint
    v_restriction_mps = kmph_to_mps(constraints.get("v_restriction_kmph", 999.0))

    # 4. Weather (fog) constraint
    v_weather_mps = kmph_to_mps(constraints.get("v_weather_kmph", 999.0))

    # 5. Congestion constraint
    v_congestion_mps = kmph_to_mps(constraints.get("v_congestion_kmph", 999.0))

    # 6. Approach / braking constraint (only if stopping at next station)
    if must_stop_at_next_station and distance_to_next_station_m > 0:
        v_approach_mps = compute_approach_speed(
            distance_to_next_station_m,
            braking_decel_mps2
        )
    else:
        v_approach_mps = 999.0

    # 7. Final V_target = minimum of ALL constraints
    candidates = {
        "section":     v_section_mps,
        "signal":      v_signal_mps,
        "restriction": v_restriction_mps,
        "weather":     v_weather_mps,
        "congestion":  v_congestion_mps,
        "approach":    v_approach_mps,
    }

    limiting_factor = min(candidates, key=candidates.get)
    v_target_mps    = candidates[limiting_factor]

    return {
        "v_target_mps":    v_target_mps,
        "v_target_kmph":   mps_to_kmph(v_target_mps),
        "limiting_factor": limiting_factor,
        "v_approach_mps":  v_approach_mps,
        "all_constraints": {k: round(mps_to_kmph(v), 2) for k, v in candidates.items()}
    }


def compute_acceleration(
    current_speed_mps: float,
    v_target_mps: float,
    max_accel_mps2: float,
    max_brake_mps2: float
) -> float:
    """
    Decides whether to accelerate, decelerate, or cruise.
    Returns acceleration in m/s².
    """
    delta = v_target_mps - current_speed_mps

    if delta > 0.5:
        return max_accel_mps2
    elif delta < -0.5:
        return -max_brake_mps2
    else:
        return 0.0


def get_movement_state(
    current_speed_mps: float,
    acceleration_mps2: float,
    at_station: bool,
    dwelling: bool,
    journey_complete: bool
) -> str:
    """Returns the human-readable movement state string."""
    if journey_complete:
        return "COMPLETED"
    if dwelling:
        return "DWELLING"
    if current_speed_mps <= 0.05:
        return "STOPPED"
    if acceleration_mps2 > 0.1:
        return "ACCELERATING"
    elif acceleration_mps2 < -0.1:
        return "DECELERATING"
    else:
        return "CRUISING"


if __name__ == "__main__":
    from src.simulator.route.route_loader import load_config, load_events
    from src.simulator.events.event_manager import get_active_events, resolve_speed_constraints

    config = load_config(r"D:\Projects\railway\src\simulator\config\simulator_config.json")
    events = load_events(r"D:\Projects\railway\src\simulator\events\scenario_05_heavy_disruption.json")
    physics = config["physics"]

    active = get_active_events(
        events=events,
        current_time_str="07:30:00",
        current_section_id="SEC_GZB_MTC",
        current_position_km=45.0,
        route_id="ROUTE_NDLS_DDN_01"
    )
    constraints = resolve_speed_constraints(active, config)

    result = compute_target_speed(
        section_speed_limit_kmph=110.0,
        constraints=constraints,
        distance_to_next_station_m=5000.0,
        must_stop_at_next_station=True,
        braking_decel_mps2=physics["max_braking_deceleration_mps2"]
    )

    accel = compute_acceleration(
        current_speed_mps=kmph_to_mps(90.0),
        v_target_mps=result["v_target_mps"],
        max_accel_mps2=physics["max_acceleration_mps2"],
        max_brake_mps2=physics["max_braking_deceleration_mps2"]
    )

    print("=== Speed Controller Test ===")
    print(f"All constraints (km/h) : {result['all_constraints']}")
    print(f"V_target               : {result['v_target_kmph']:.1f} km/h")
    print(f"Limiting factor        : {result['limiting_factor']}")
    print(f"Acceleration decision  : {accel} m/s²")
    print(f"Movement state         : {get_movement_state(kmph_to_mps(90.0), accel, False, False, False)}")
