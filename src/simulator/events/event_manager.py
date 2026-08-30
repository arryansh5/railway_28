"""
event_manager.py — Phase 3: Physics-Based RTIS Simulator
Evaluates which synthetic events are active at the current simulation time and position.
Returns active speed constraints consumed by the speed controller.
"""

from datetime import datetime


def _parse_time(time_str: str) -> datetime:
    """Converts HH:MM:SS string to a datetime object for comparison."""
    return datetime.strptime(time_str, "%H:%M:%S")


def get_active_events(
    events: list,
    current_time_str: str,
    current_section_id: str,
    current_position_km: float,
    route_id: str
) -> list:
    """
    Returns a list of all currently active events given:
    - current_time_str: "HH:MM:SS"
    - current_section_id: e.g. "SEC_GZB_MTC"
    - current_position_km: e.g. 45.2
    - route_id: e.g. "ROUTE_NDLS_DDN_01"

    An event is active when:
    1. enabled == True
    2. current_time >= start_time AND current_time <= end_time
    3. route_id matches (if specified in event)
    4. section_id matches current_section_id (if specified in event)
    """
    current_time = _parse_time(current_time_str)
    active = []

    for evt in events:
        # Check 1: enabled
        if not evt.get("enabled", False):
            continue

        # Check 2: time window
        start = _parse_time(evt["start_time"])
        end   = _parse_time(evt["end_time"])
        if not (start <= current_time <= end):
            continue

        # Check 3: route matches (if event specifies a route)
        if evt.get("route_id") and evt["route_id"] != route_id:
            continue

        # Check 4: section matches (if event specifies a section)
        if evt.get("section_id") and evt["section_id"] != current_section_id:
            continue

        active.append(evt)

    return active


def resolve_speed_constraints(active_events: list, config: dict) -> dict:
    """
    Given the list of active events, returns the effective speed constraint
    for each category (signal, restriction, congestion, weather).

    The physics speed_controller will take min() of all these.

    Returns:
    {
        "signal_state":             "GREEN" | "YELLOW" | "RED" | None
        "v_signal_kmph":            float (999 = no constraint)
        "v_restriction_kmph":       float (999 = no constraint)
        "congestion_level":         "LOW" | "MEDIUM" | "HIGH" | None
        "v_congestion_kmph":        float (999 = no constraint)
        "fog_active":               bool
        "fog_visibility_km":        float | None
        "v_weather_kmph":           float (999 = no constraint)
        "unscheduled_halt":         bool
        "active_event_ids":         list[str]
    }
    """
    # Defaults: no constraints
    signal_state       = None
    v_signal           = 999.0
    v_restriction      = 999.0
    congestion_level   = None
    v_congestion       = 999.0
    fog_active         = False
    fog_visibility_km  = None
    v_weather          = 999.0
    unscheduled_halt   = False
    active_ids         = []

    signal_map     = config["signal_speed_mapping_kmph"]
    congestion_map = config["congestion_speed_mapping_kmph"]
    fog_map        = config["fog_speed_mapping_kmph"]

    for evt in active_events:
        active_ids.append(evt["event_id"])
        etype = evt["event_type"]

        if etype == "SIGNAL_CHANGE":
            state = evt.get("signal_state", "GREEN")
            signal_state = state
            v_signal = min(v_signal, signal_map.get(state, 999.0))

        elif etype == "SPEED_RESTRICTION":
            v = evt.get("restriction_speed_kmph", 999.0)
            if v is not None:
                v_restriction = min(v_restriction, v)

        elif etype == "CONGESTION":
            level = evt.get("congestion_level", "LOW")
            congestion_level = level
            v_congestion = min(v_congestion, congestion_map.get(level, 999.0))

        elif etype == "FOG":
            fog_active = True
            fog_visibility_km = evt.get("fog_visibility_km")
            v_fog = evt.get("restriction_speed_kmph",
                            fog_map.get("DEFAULT_FOG_RESTRICTION", 40.0))
            if v_fog is not None:
                v_weather = min(v_weather, v_fog)

        elif etype == "UNSCHEDULED_HALT":
            unscheduled_halt = True
            v_signal = 0.0  # Force full stop

    return {
        "signal_state":       signal_state,
        "v_signal_kmph":      v_signal,
        "v_restriction_kmph": v_restriction,
        "congestion_level":   congestion_level,
        "v_congestion_kmph":  v_congestion,
        "fog_active":         fog_active,
        "fog_visibility_km":  fog_visibility_km,
        "v_weather_kmph":     v_weather,
        "unscheduled_halt":   unscheduled_halt,
        "active_event_ids":   active_ids
    }


if __name__ == "__main__":
    from src.simulator.route.route_loader import load_config, load_events

    config = load_config(r"D:\Projects\railway\src\simulator\config\simulator_config.json")
    events = load_events(r"D:\Projects\railway\src\simulator\events\scenario_05_heavy_disruption.json")

    # Simulate: train is in SEC_GZB_MTC at 07:30:00
    active = get_active_events(
        events=events,
        current_time_str="07:30:00",
        current_section_id="SEC_GZB_MTC",
        current_position_km=45.0,
        route_id="ROUTE_NDLS_DDN_01"
    )
    constraints = resolve_speed_constraints(active, config)

    print("=== Event Manager Test ===")
    print(f"Active events at 07:30 in SEC_GZB_MTC : {len(active)}")
    for e in active:
        print(f"  [{e['event_id']}] {e['event_type']}")
    print(f"\nResolved constraints:")
    for k, v in constraints.items():
        print(f"  {k}: {v}")
