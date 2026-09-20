"""
tests/test_route_resolver.py — Phase 4 Dynamic Route Resolver Unit Tests
"""

import pytest
from src.network.resolver import RouteResolver, resolve_route


@pytest.fixture
def resolver():
    return RouteResolver()


def test_delhi_to_roorkee(resolver):
    res = resolver.resolve_route("NDLS", "RK")
    assert res.status == "RESOLVED"
    assert res.origin == "NDLS"
    assert res.destination == "RK"
    assert res.total_distance_km > 0
    assert len(res.ordered_stations) >= 2
    assert res.ordered_stations[0]["station_code"] == "NDLS"
    assert res.ordered_stations[-1]["station_code"] == "RK"


def test_roorkee_to_dehradun(resolver):
    res = resolver.resolve_route("RK", "DDN")
    assert res.status == "RESOLVED"
    assert res.direction == "FORWARD"
    assert res.ordered_stations[0]["station_code"] == "RK"
    assert res.ordered_stations[-1]["station_code"] == "DDN"


def test_dehradun_to_roorkee_reverse(resolver):
    res = resolver.resolve_route("DDN", "RK")
    assert res.status == "RESOLVED"
    assert res.direction == "REVERSE"
    assert res.ordered_stations[0]["station_code"] == "DDN"
    assert res.ordered_stations[-1]["station_code"] == "RK"
    assert res.ordered_stations[0]["distance_from_origin_km"] == 0.0


def test_full_delhi_to_dehradun_corridor(resolver):
    res = resolver.resolve_route("Delhi", "Dehradun")
    assert res.status == "RESOLVED"
    assert res.total_distance_km == 314.0
    assert len(res.ordered_stations) == 8
    # Test remaining distance support
    rem_from_ndls = res.get_remaining_distance("NDLS")
    rem_from_sre = res.get_remaining_distance("SRE")
    assert rem_from_ndls == 314.0
    assert rem_from_sre < rem_from_ndls
    assert res.get_remaining_distance("DDN") == 0.0


def test_unknown_station_error(resolver):
    res = resolver.resolve_route("NON_EXISTENT_STATION", "DDN")
    assert res.status == "UNKNOWN_STATION"
    assert "could not be found" in res.error_message


def test_identical_origin_destination(resolver):
    res = resolver.resolve_route("NDLS", "NDLS")
    assert res.status == "NO_ROUTE_FOUND"
