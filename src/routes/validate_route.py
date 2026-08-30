import json 

def load_route(filepath):
    with open(filepath , 'r') as f:
        data = json.load(f)
    return data  


def validate_stations(stations):
    print("Validating stations...")

    # --- Check 1: Required fields (next_station_id excluded — null for terminal) ---
    always_required = [
        "station_id", "station_name", "sequence",
        "distance_from_origin_km",
        "scheduled_arrival_offset_min", "scheduled_departure_offset_min",
        "scheduled_dwell_min", "is_origin", "is_terminal"
    ]
    for station in stations:
        sid = station.get("station_id", "?")
        for field in always_required:
            if station.get(field) is None:
                raise ValueError(f"Station '{sid}' is missing required field: '{field}'")
        # next_station_id can be null ONLY for terminal
        if station.get("next_station_id") is None and not station.get("is_terminal"):
            raise ValueError(f"Station '{sid}' has null next_station_id but is not terminal")
        # previous_station_id can be null ONLY for origin
        if station.get("previous_station_id") is None and not station.get("is_origin"):
            raise ValueError(f"Station '{sid}' has null previous_station_id but is not origin")
    print("  [OK] Required fields and nullable exceptions passed")

    # --- Check 2: Unique station_id and sequence ---
    ids = [s["station_id"] for s in stations]
    seqs = [s["sequence"] for s in stations]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate station_id found: {ids}")
    if len(seqs) != len(set(seqs)):
        raise ValueError(f"Duplicate sequence numbers found: {seqs}")
    print("  [OK] station_id and sequence are unique")

    # --- Check 3: Sequence must be 1, 2, 3... with no gaps ---
    sorted_stations = sorted(stations, key=lambda s: s["sequence"])
    for i, s in enumerate(sorted_stations):
        if s["sequence"] != i + 1:
            raise ValueError(f"Sequence gap: expected {i+1}, got {s['sequence']} at '{s['station_id']}'")
    print("  [OK] Sequence is continuous with no gaps")

    # --- Check 4: Exactly one origin and one terminal ---
    origins = [s for s in stations if s.get("is_origin")]
    terminals = [s for s in stations if s.get("is_terminal")]
    if len(origins) != 1:
        raise ValueError(f"Expected exactly 1 origin, found {len(origins)}")
    if len(terminals) != 1:
        raise ValueError(f"Expected exactly 1 terminal, found {len(terminals)}")
    print("  [OK] Exactly one origin and one terminal")

    # --- Check 5: Origin must have distance = 0 ---
    origin = origins[0]
    if origin["distance_from_origin_km"] != 0.0:
        raise ValueError(f"Origin '{origin['station_id']}' must have distance_from_origin_km = 0.0")
    print("  [OK] Origin distance is 0.0")

    # --- Check 6: Distance must strictly increase ---
    for i in range(1, len(sorted_stations)):
        prev = sorted_stations[i - 1]
        curr = sorted_stations[i]
        if curr["distance_from_origin_km"] <= prev["distance_from_origin_km"]:
            raise ValueError(
                f"Distance must increase: '{curr['station_id']}' ({curr['distance_from_origin_km']} km) "
                f"<= '{prev['station_id']}' ({prev['distance_from_origin_km']} km)"
            )
    print("  [OK] Distance increases monotonically")

    # --- Check 7: Departure offset >= Arrival offset ---
    for s in stations:
        arr = s["scheduled_arrival_offset_min"]
        dep = s["scheduled_departure_offset_min"]
        if dep < arr:
            raise ValueError(f"Station '{s['station_id']}': departure offset ({dep}) < arrival offset ({arr})")
    print("  [OK] Departure offsets >= arrival offsets")

    # --- Check 8: Dwell time consistency ---
    for s in stations:
        arr = s["scheduled_arrival_offset_min"]
        dep = s["scheduled_departure_offset_min"]
        dwell = s["scheduled_dwell_min"]
        if dwell != (dep - arr):
            raise ValueError(
                f"Station '{s['station_id']}': dwell_min ({dwell}) != dep - arr ({dep - arr})"
            )
    print("  [OK] Dwell times are consistent")

    # --- Check 9: Linked-list next/previous integrity ---
    for i in range(len(sorted_stations) - 1):
        curr = sorted_stations[i]
        nxt = sorted_stations[i + 1]
        if curr.get("next_station_id") != nxt["station_id"]:
            raise ValueError(
                f"'{curr['station_id']}' next_station_id='{curr.get('next_station_id')}' "
                f"but next station is '{nxt['station_id']}'"
            )
        if nxt.get("previous_station_id") != curr["station_id"]:
            raise ValueError(
                f"'{nxt['station_id']}' previous_station_id='{nxt.get('previous_station_id')}' "
                f"but previous station is '{curr['station_id']}'"
            )
    # Origin's previous_station_id must be null
    if origins[0].get("previous_station_id") is not None:
        raise ValueError(f"Origin '{origins[0]['station_id']}' must have previous_station_id = null")
    # Terminal's next_station_id must be null
    if terminals[0].get("next_station_id") is not None:
        raise ValueError(f"Terminal '{terminals[0]['station_id']}' must have next_station_id = null")
    print("  [OK] Linked-list next/previous IDs are consistent")

    print("\nAll station checks passed!")


def validate_sections(sections, stations):
    print("\nValidating sections...")

    # --- Check 10: Required fields not null ---
    required_fields = [
        "section_id", "from_station_id", "to_station_id",
        "distance_km", "sequence", "scheduled_running_time_min"
    ]
    for sec in sections:
        sid = sec.get("section_id", "?")
        for field in required_fields:
            if sec.get(field) is None:
                raise ValueError(f"Section '{sid}' is missing required field: '{field}'")
    print("  [OK] Required fields present")

    # --- Check 11: from/to station references exist ---
    station_ids = {s["station_id"] for s in stations}
    station_dist = {s["station_id"]: s["distance_from_origin_km"] for s in stations}
    for sec in sections:
        sid = sec["section_id"]
        if sec["from_station_id"] not in station_ids:
            raise ValueError(f"Section '{sid}': from_station_id='{sec['from_station_id']}' not in stations")
        if sec["to_station_id"] not in station_ids:
            raise ValueError(f"Section '{sid}': to_station_id='{sec['to_station_id']}' not in stations")
    print("  [OK] from/to station references exist")

    # --- Check 12: Sequence unique and continuous ---
    seqs = [sec["sequence"] for sec in sections]
    if len(seqs) != len(set(seqs)):
        raise ValueError(f"Duplicate section sequences: {seqs}")
    sorted_sections = sorted(sections, key=lambda s: s["sequence"])
    for i, sec in enumerate(sorted_sections):
        if sec["sequence"] != i + 1:
            raise ValueError(f"Section sequence gap: expected {i+1}, got {sec['sequence']} at '{sec['section_id']}'")
    print("  [OK] Sequence is unique and continuous")

    # --- Check 13: Section connectivity ---
    for i in range(len(sorted_sections) - 1):
        curr = sorted_sections[i]
        nxt = sorted_sections[i + 1]
        if curr["to_station_id"] != nxt["from_station_id"]:
            raise ValueError(
                f"Connectivity break: '{curr['section_id']}' ends at '{curr['to_station_id']}' "
                f"but '{nxt['section_id']}' starts at '{nxt['from_station_id']}'"
            )
    print("  [OK] Section connectivity is consistent")

    # --- Check 14: Per-section distance matches station distance difference ---
    for sec in sorted_sections:
        frm = sec["from_station_id"]
        to = sec["to_station_id"]
        expected = station_dist[to] - station_dist[frm]
        actual = sec["distance_km"]
        if abs(actual - expected) > 0.01:
            raise ValueError(
                f"Section '{sec['section_id']}': distance_km ({actual}) "
                f"!= station distance difference ({expected})"
            )
    print("  [OK] Section distances match station distances")

    # --- Check 15: Sum of section distances == total route distance ---
    total = sum(sec["distance_km"] for sec in sections)
    route_total = station_dist[sorted_sections[-1]["to_station_id"]]
    if abs(total - route_total) > 0.01:
        raise ValueError(
            f"Sum of section distances ({total} km) != route total distance ({route_total} km)"
        )
    print("  [OK] Sum of section distances matches total route distance")

    print("\nAll section checks passed!")


def validate_route_metadata(route):
    print("Validating route metadata...")

    # --- Check 16: Required top-level fields ---
    required = [
        "route_id", "route_name", "origin_station_id",
        "destination_station_id", "total_distance_km",
        "total_scheduled_duration_min"
    ]
    for field in required:
        if route.get(field) is None:
            raise ValueError(f"Route metadata missing: '{field}'")
    print("  [OK] Required metadata fields present")

    # --- Check 17: stations and sections must be non-empty lists ---
    if not isinstance(route.get("stations"), list) or len(route["stations"]) == 0:
        raise ValueError("'stations' must be a non-empty list")
    if not isinstance(route.get("sections"), list) or len(route["sections"]) == 0:
        raise ValueError("'sections' must be a non-empty list")
    print("  [OK] stations and sections are non-empty lists")

    stations = route["stations"]
    sections = route["sections"]
    origin   = next(s for s in stations if s.get("is_origin"))
    terminal = next(s for s in stations if s.get("is_terminal"))

    # --- Check 22: sections count == stations count - 1 ---
    if len(sections) != len(stations) - 1:
        raise ValueError(
            f"Expected {len(stations) - 1} sections for {len(stations)} stations, "
            f"found {len(sections)}"
        )
    print("  [OK] sections count matches stations count")

    # --- Check 23: first section starts at origin, last ends at destination ---
    first_sec = min(sections, key=lambda s: s["sequence"])
    last_sec  = max(sections, key=lambda s: s["sequence"])
    if first_sec["from_station_id"] != route["origin_station_id"]:
        raise ValueError(
            f"First section starts at '{first_sec['from_station_id']}' "
            f"!= origin '{route['origin_station_id']}'"
        )
    if last_sec["to_station_id"] != route["destination_station_id"]:
        raise ValueError(
            f"Last section ends at '{last_sec['to_station_id']}' "
            f"!= destination '{route['destination_station_id']}'"
        )
    print("  [OK] sections start/end in sync with origin/destination")


    # --- Check 18 & 19: origin/destination sync ---
    if route["origin_station_id"] != origin["station_id"]:
        raise ValueError(
            f"origin_station_id '{route['origin_station_id']}' != actual origin '{origin['station_id']}'"
        )
    if route["destination_station_id"] != terminal["station_id"]:
        raise ValueError(
            f"destination_station_id '{route['destination_station_id']}' != actual terminal '{terminal['station_id']}'"
        )
    print("  [OK] origin/destination IDs in sync")

    # --- Check 20: total_distance_km sync ---
    if route["total_distance_km"] != terminal["distance_from_origin_km"]:
        raise ValueError(
            f"total_distance_km ({route['total_distance_km']}) "
            f"!= terminal distance ({terminal['distance_from_origin_km']})"
        )
    print("  [OK] total_distance_km in sync")

    # --- Check 21: total_scheduled_duration_min sync ---
    if route["total_scheduled_duration_min"] != terminal["scheduled_arrival_offset_min"]:
        raise ValueError(
            f"total_scheduled_duration_min ({route['total_scheduled_duration_min']}) "
            f"!= terminal arrival offset ({terminal['scheduled_arrival_offset_min']})"
        )
    print("  [OK] total_scheduled_duration_min in sync")

    print("\nAll metadata checks passed!")


if __name__ == "__main__":
    import sys
    from pathlib import Path
    default_path = Path(__file__).resolve().parent.parent.parent / "Data" / "routes" / "delhi_dehradun_route.json"
    route_path = sys.argv[1] if len(sys.argv) > 1 else str(default_path)
    route = load_route(route_path)
    print(f"Route loaded : {route['route_name']}")
    print(f"route id     : {route['route_id']}")
    print(f"stations     : {len(route['stations'])}")
    print(f"sections     : {len(route['sections'])}\n")
    validate_route_metadata(route)
    validate_stations(route['stations'])
    validate_sections(route['sections'], route['stations'])