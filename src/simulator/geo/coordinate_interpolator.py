"""
coordinate_interpolator.py — Phase 3: Physics-Based RTIS Simulator
Interpolates synthetic GPS coordinates (lat/lon) along route sections.
Uses linear interpolation between station coordinates based on section progress.
"""

from typing import Tuple, Optional


def interpolate_coordinates(
    current_position_km: float,
    current_section: Optional[dict],
    station_lookup: dict
) -> Tuple[float, float]:
    """
    Computes current (latitude, longitude) for the train.

    Parameters:
    - current_position_km: Total km travelled from origin
    - current_section: Dict of current section (or None if at station/start/end)
    - station_lookup: Dict mapping station_id -> station details (with lat/lon)

    Returns:
    - (latitude, longitude) as a tuple of floats rounded to 6 decimal places.
    """
    if current_section is None:
        # Fallback: Find closest station or return 0,0
        return (0.0, 0.0)

    from_stn = station_lookup.get(current_section["from_station_id"])
    to_stn   = station_lookup.get(current_section["to_station_id"])

    if not from_stn or not to_stn:
        return (0.0, 0.0)

    from_km = from_stn["distance_from_origin_km"]
    to_km   = to_stn["distance_from_origin_km"]
    section_dist = to_km - from_km

    if section_dist <= 0.0:
        return (round(from_stn["latitude"], 6), round(from_stn["longitude"], 6))

    # Calculate fraction along the current section [0.0, 1.0]
    fraction = (current_position_km - from_km) / section_dist
    fraction = max(0.0, min(1.0, fraction))

    lat = from_stn["latitude"] + fraction * (to_stn["latitude"] - from_stn["latitude"])
    lon = from_stn["longitude"] + fraction * (to_stn["longitude"] - from_stn["longitude"])

    return (round(lat, 6), round(lon, 6))


if __name__ == "__main__":
    from src.simulator.route.route_loader import load_route

    route = load_route(r"D:\Projects\railway\Data\routes\delhi_dehradun_route.json")
    stn_lookup = route["station_lookup"]
    
    # Test case: Midpoint between NDLS (0 km) and GZB (25 km) -> 12.5 km
    sec_ndls_gzb = route["section_lookup"]["SEC_NDLS_GZB"]
    lat, lon = interpolate_coordinates(12.5, sec_ndls_gzb, stn_lookup)

    ndls = stn_lookup["NDLS"]
    gzb = stn_lookup["GZB"]

    print("=== Coordinate Interpolator Test ===")
    print(f"NDLS Coordinates : ({ndls['latitude']}, {ndls['longitude']}) at 0.0 km")
    print(f"Midpoint (12.5km): ({lat}, {lon}) [Interpolated]")
    print(f"GZB Coordinates  : ({gzb['latitude']}, {gzb['longitude']}) at 25.0 km")
