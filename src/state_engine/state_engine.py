"""
State Engine Module.
Ingests 30-second train observations and maintains a real-time, queryable TrainState.
"""

from typing import Dict, Any, List, Optional
from src.state_engine.train_state import TrainState


class StateEngine:
    """
    Maintains and updates the canonical state of a train along a route
    as observation events arrive.
    """

    def __init__(self, route: Dict[str, Any]):
        """
        Initialize the StateEngine with a route configuration.

        Args:
            route: Generic route configuration dictionary.
        """
        self.route = route
        self.route_id = route.get("route_id", "")
        self.total_distance_km = float(route.get("total_distance_km", 0.0))
        self.stations: List[Dict[str, Any]] = route.get("stations", [])
        self.sections: List[Dict[str, Any]] = route.get("sections", [])

        # Lookups
        self.station_lookup = {s["station_id"]: s for s in self.stations}
        self.section_lookup = {sec["section_id"]: sec for sec in self.sections}

        # Internal state
        self.state: Optional[TrainState] = None
        self._recent_delays: List[float] = []
        self._station_history_map: Dict[str, Dict[str, Any]] = {}
        self._last_arrival_delay: Optional[float] = None
        self._last_departure_delay: Optional[float] = None

    def ingest(self, observation: Dict[str, Any]) -> TrainState:
        """
        Consumes one 30-second observation dict and updates internal TrainState.

        Args:
            observation: Dictionary containing train observation metrics.

        Returns:
            Updated TrainState dataclass instance.
        """
        train_id = str(observation.get("train_id") or "TRAIN_01")
        route_id = str(observation.get("route_id") or self.route_id)
        timestamp = str(observation.get("timestamp") or "")

        # Position & Kinematics
        pos_raw = observation.get("current_position_km")
        if pos_raw is None:
            pos_raw = observation.get("distance_from_origin_km", 0.0)
        current_position_km = round(float(pos_raw), 3)

        speed_raw = observation.get("current_speed_kmph")
        if speed_raw is None:
            speed_raw = observation.get("speed_kmph", 0.0)
        current_speed_kmph = round(float(speed_raw), 2)

        movement_state = str(observation.get("movement_state") or ("STOPPED" if current_speed_kmph == 0.0 else "CRUISING"))

        # Section and Station relationships
        current_section_id = observation.get("current_section_id")
        current_station_id = observation.get("current_station_id")
        previous_station_id = observation.get("previous_station_id")
        next_station_id = observation.get("next_station_id")

        # Geo
        latitude = float(observation.get("latitude", 0.0) or 0.0)
        longitude = float(observation.get("longitude", 0.0) or 0.0)

        # Distances & Journey Progress
        if self.total_distance_km > 0.0:
            percent_journey = round(min(100.0, max(0.0, (current_position_km / self.total_distance_km) * 100.0)), 2)
            dist_to_dest = round(max(0.0, self.total_distance_km - current_position_km), 3)
        else:
            percent_journey = 0.0
            dist_to_dest = 0.0

        dist_next_raw = observation.get("distance_to_next_station_km")
        if dist_next_raw is not None:
            distance_to_next_station_km = round(max(0.0, float(dist_next_raw)), 3)
        elif next_station_id and next_station_id in self.station_lookup:
            next_st_dist = float(self.station_lookup[next_station_id]["distance_from_origin_km"])
            distance_to_next_station_km = round(max(0.0, next_st_dist - current_position_km), 3)
        else:
            distance_to_next_station_km = 0.0

        # Check for journey completion
        if current_position_km >= self.total_distance_km and self.total_distance_km > 0:
            movement_state = "COMPLETED"
            percent_journey = 100.0
            dist_to_dest = 0.0
            distance_to_next_station_km = 0.0

        # Delay Handling & Trend
        delay_raw = observation.get("current_delay_min")
        current_delay_min = round(float(delay_raw), 2) if delay_raw is not None else 0.0

        self._recent_delays.append(current_delay_min)
        if len(self._recent_delays) > 3:
            self._recent_delays.pop(0)

        delay_trend = self._compute_delay_trend()

        # Station Event and History Tracking
        arr_delay = observation.get("arrival_delay_min")
        if arr_delay is not None:
            self._last_arrival_delay = round(float(arr_delay), 2)

        dep_delay = observation.get("departure_delay_min")
        if dep_delay is not None:
            self._last_departure_delay = round(float(dep_delay), 2)

        self._update_station_history(observation, current_station_id, timestamp)

        # Active Events
        active_events = self._extract_active_events(observation)

        self.state = TrainState(
            train_id=train_id,
            route_id=route_id,
            timestamp=timestamp,
            current_position_km=current_position_km,
            current_section_id=current_section_id,
            current_station_id=current_station_id,
            previous_station_id=previous_station_id,
            next_station_id=next_station_id,
            current_speed_kmph=current_speed_kmph,
            movement_state=movement_state,
            distance_to_next_station_km=distance_to_next_station_km,
            distance_to_destination_km=dist_to_dest,
            percent_journey_complete=percent_journey,
            current_delay_min=current_delay_min,
            delay_trend=delay_trend,
            last_arrival_delay_min=self._last_arrival_delay,
            last_departure_delay_min=self._last_departure_delay,
            station_history=list(self._station_history_map.values()),
            active_events=active_events,
            latitude=latitude,
            longitude=longitude,
        )

        return self.state

    def _compute_delay_trend(self) -> str:
        """
        Computes the delay trend across recent observations.
        - delta >= +0.5 min -> "WORSENING"
        - delta <= -0.5 min -> "IMPROVING"
        - otherwise -> "STABLE"
        """
        if len(self._recent_delays) < 2:
            return "STABLE"

        delta = self._recent_delays[-1] - self._recent_delays[0]
        if delta >= 0.5:
            return "WORSENING"
        elif delta <= -0.5:
            return "IMPROVING"
        return "STABLE"

    def _update_station_history(
        self,
        observation: Dict[str, Any],
        station_id: Optional[str],
        timestamp: str
    ) -> None:
        """Tracks arrival, dwelling, and departure events per station."""
        st_event = observation.get("station_event")
        actual_arr = observation.get("actual_arrival_time")
        actual_dep = observation.get("actual_departure_time")
        dwell_min = observation.get("actual_dwell_min")

        target_station = station_id
        if not target_station and observation.get("current_station_id"):
            target_station = observation.get("current_station_id")

        if target_station and target_station in self.station_lookup:
            if target_station not in self._station_history_map:
                st_info = self.station_lookup[target_station]
                self._station_history_map[target_station] = {
                    "station_id": target_station,
                    "station_name": st_info.get("station_name"),
                    "sequence": st_info.get("sequence"),
                    "distance_from_origin_km": st_info.get("distance_from_origin_km"),
                    "arrival_time": actual_arr or (timestamp if st_event == "ARRIVED" else None),
                    "departure_time": actual_dep or (timestamp if st_event == "DEPARTED" else None),
                    "arrival_delay_min": self._last_arrival_delay,
                    "departure_delay_min": self._last_departure_delay,
                    "dwell_min": float(dwell_min) if dwell_min is not None else None,
                    "status": st_event or "VISITED"
                }
            else:
                record = self._station_history_map[target_station]
                if actual_arr:
                    record["arrival_time"] = actual_arr
                elif st_event == "ARRIVED" and not record["arrival_time"]:
                    record["arrival_time"] = timestamp

                if actual_dep:
                    record["departure_time"] = actual_dep
                elif st_event == "DEPARTED":
                    record["departure_time"] = timestamp

                if dwell_min is not None:
                    record["dwell_min"] = float(dwell_min)
                if self._last_arrival_delay is not None:
                    record["arrival_delay_min"] = self._last_arrival_delay
                if self._last_departure_delay is not None:
                    record["departure_delay_min"] = self._last_departure_delay
                if st_event:
                    record["status"] = st_event

    def _extract_active_events(self, observation: Dict[str, Any]) -> List[str]:
        """Extract active disruption / operational events as a list of strings."""
        events: List[str] = []
        raw_events = observation.get("active_event_ids") or observation.get("active_events")
        if isinstance(raw_events, list):
            events.extend([str(e) for e in raw_events if e])
        elif isinstance(raw_events, str) and raw_events.strip():
            events.append(raw_events.strip())

        op_evt = observation.get("operational_event")
        if op_evt and str(op_evt) not in events:
            events.append(str(op_evt))

        return events

    def get_state(self) -> Optional[TrainState]:
        """Returns the current state snapshot."""
        return self.state
