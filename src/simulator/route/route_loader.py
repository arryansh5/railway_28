"""
route_loader.py — Phase 3: Physics-Based RTIS Simulator
Loads and parses the route JSON and simulator config into clean Python structures.
All downstream simulator modules receive their route/config data from here.
"""

import json
from pathlib import Path


def load_json(filepath: str) -> dict:
    """Loads a JSON file and returns it as a Python dict."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"[RouteLoader] File not found: {filepath}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_route(route_filepath: str) -> dict:
    """
    Loads the route JSON and returns an enriched route dict with:
    - Stations sorted by sequence
    - Sections sorted by sequence
    - Fast O(1) lookup dicts for stations and sections by ID
    - Validated origin and terminal station references
    """
    raw = load_json(route_filepath)

    # Sort stations and sections by sequence (defensive — guarantees correct order)
    stations = sorted(raw["stations"], key=lambda s: s["sequence"])
    sections = sorted(raw["sections"], key=lambda s: s["sequence"])

    # Build O(1) lookup dicts
    station_lookup = {s["station_id"]: s for s in stations}
    section_lookup = {s["section_id"]: s for s in sections}

    # Identify origin and terminal (used frequently by all modules)
    origin = next((s for s in stations if s.get("is_origin")), None)
    terminal = next((s for s in stations if s.get("is_terminal")), None)

    if origin is None:
        raise ValueError("[RouteLoader] No station marked as is_origin in route JSON.")
    if terminal is None:
        raise ValueError("[RouteLoader] No station marked as is_terminal in route JSON.")

    return {
        # Top-level route metadata
        "route_id": raw["route_id"],
        "route_name": raw["route_name"],
        "origin_station_id": raw["origin_station_id"],
        "destination_station_id": raw["destination_station_id"],
        "total_distance_km": raw["total_distance_km"],
        "total_scheduled_duration_min": raw["total_scheduled_duration_min"],
        "update_interval_sec": raw.get("update_interval_sec", 30),

        # Ordered lists (safe to iterate in sequence)
        "stations": stations,
        "sections": sections,

        # Fast lookup dicts
        "station_lookup": station_lookup,
        "section_lookup": section_lookup,

        # Convenience references
        "origin": origin,
        "terminal": terminal,
    }


def load_config(config_filepath: str) -> dict:
    """
    Loads simulator_config.json and returns the config dict.
    Validates that required keys exist before returning.
    """
    config = load_json(config_filepath)

    required_keys = [
        "simulation_timestep_seconds",
        "random_seed",
        "physics",
        "signal_speed_mapping_kmph",
        "congestion_speed_mapping_kmph",
        "fog_speed_mapping_kmph",
        "output"
    ]
    for key in required_keys:
        if key not in config:
            raise KeyError(f"[ConfigLoader] Missing required config key: '{key}'")

    return config


def load_events(events_filepath: str) -> list:
    """
    Loads a simulation event scenario JSON file.
    Returns only the events list with enabled=True entries validated.
    Both full event files (with 'events' key) and scenario files 
    (with 'events' key under scenario wrapper) are supported.
    """
    raw = load_json(events_filepath)

    # Support both formats: {"events": [...]} and {"scenario_id": ..., "events": [...]}
    events = raw.get("events", [])

    if not isinstance(events, list):
        raise ValueError(f"[EventLoader] 'events' must be a list in: {events_filepath}")

    # Validate each event has required fields
    required_event_keys = ["event_id", "event_type", "enabled"]
    for evt in events:
        for key in required_event_keys:
            if key not in evt:
                raise KeyError(
                    f"[EventLoader] Event '{evt.get('event_id', '?')}' "
                    f"missing required field: '{key}'"
                )

    return events


if __name__ == "__main__":
    route = load_route(r"D:\Projects\railway\Data\routes\delhi_dehradun_route.json")
    config = load_config(r"D:\Projects\railway\src\simulator\config\simulator_config.json")
    events = load_events(r"D:\Projects\railway\src\simulator\events\scenario_02_speed_restriction.json")

    print("=== Route Loader Test ===")
    print(f"Route        : {route['route_name']}")
    print(f"Route ID     : {route['route_id']}")
    print(f"Total km     : {route['total_distance_km']} km")
    print(f"Stations     : {len(route['stations'])}")
    print(f"Sections     : {len(route['sections'])}")
    print(f"Origin       : {route['origin']['station_id']} ({route['origin']['station_name']})")
    print(f"Terminal     : {route['terminal']['station_id']} ({route['terminal']['station_name']})")
    print(f"\n=== Config Loader Test ===")
    print(f"Timestep     : {config['simulation_timestep_seconds']}s")
    print(f"Max Accel    : {config['physics']['max_acceleration_mps2']} m/s²")
    print(f"Max Brake    : {config['physics']['max_braking_deceleration_mps2']} m/s²")
    print(f"Random Seed  : {config['random_seed']}")
    print(f"\n=== Event Loader Test ===")
    print(f"Events loaded : {len(events)}")
    for e in events:
        print(f"  [{e['event_id']}] {e['event_type']} | enabled={e['enabled']}")
