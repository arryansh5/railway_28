"""
Baseline ETA Prediction Engine.
Implements non-ML benchmark predictors:
1. Pure Scheduled ETA
2. Scheduled ETA + Current Delay Propagation
3. Section Running Time Aggregator
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from src.state_engine.train_state import TrainState
from src.prediction.schemas import StationETA, ETAPrediction


class BaselineETAEngine:
    """
    Computes baseline ETA predictions for all upcoming stations along a route.
    """

    def __init__(self, route: Dict[str, Any]):
        """
        Initialize with a route configuration.

        Args:
            route: Generic route dictionary containing stations and sections.
        """
        self.route = route
        self.route_id = route.get("route_id", "")
        self.total_distance_km = float(route.get("total_distance_km", 0.0))
        self.stations: List[Dict[str, Any]] = sorted(
            route.get("stations", []), key=lambda s: s.get("sequence", 0)
        )
        self.sections: List[Dict[str, Any]] = sorted(
            route.get("sections", []), key=lambda sec: sec.get("sequence", 0)
        )
        self.station_lookup = {s["station_id"]: s for s in self.stations}
        self.section_lookup = {sec["section_id"]: sec for sec in self.sections}

        # Terminal station
        self.terminal_station = next(
            (s for s in self.stations if s.get("is_terminal")),
            self.stations[-1] if self.stations else None
        )

    def _add_minutes_to_timestr(self, time_str: Optional[str], minutes_to_add: float) -> str:
        """
        Adds minutes to a time string (supporting 'HH:MM', 'HH:MM:SS', or ISO 'YYYY-MM-DDTHH:MM:SS').
        """
        if not time_str:
            return ""

        # Try ISO format first
        if "T" in time_str:
            try:
                dt = datetime.fromisoformat(time_str)
                new_dt = dt + timedelta(minutes=minutes_to_add)
                return new_dt.strftime("%Y-%m-%dT%H:%M:%S")
            except ValueError:
                pass

        # Try HH:MM or HH:MM:SS
        parts = time_str.split(":")
        try:
            hours = int(parts[0])
            mins = int(parts[1])
            secs = int(parts[2]) if len(parts) > 2 else 0
            total_secs = int(round((hours * 3600 + mins * 60 + secs) + (minutes_to_add * 60)))
            total_secs = total_secs % (24 * 3600)  # wrap around 24 hours
            new_h = total_secs // 3600
            new_m = (total_secs % 3600) // 60
            if len(parts) > 2:
                new_s = total_secs % 60
                return f"{new_h:02d}:{new_m:02d}:{new_s:02d}"
            return f"{new_h:02d}:{new_m:02d}"
        except (ValueError, IndexError):
            return time_str

    def get_upcoming_stations(self, state: TrainState) -> List[Dict[str, Any]]:
        """
        Returns all stations downstream from the current train position.
        """
        if state.movement_state == "COMPLETED" or state.current_position_km >= self.total_distance_km:
            return []

        upcoming = []
        for s in self.stations:
            dist = float(s.get("distance_from_origin_km", 0.0))
            # If train is stopped at station, that station is current, upcoming are next ones
            if dist > state.current_position_km:
                upcoming.append(s)
            elif dist == state.current_position_km and s.get("station_id") != state.current_station_id and dist > 0.0:
                upcoming.append(s)
        return upcoming

    def predict_scheduled(self, state: TrainState) -> ETAPrediction:
        """
        Baseline 1: Pure Scheduled ETA.
        Assumes zero delay; predicted arrival = scheduled arrival.
        """
        upcoming_meta = self.get_upcoming_stations(state)
        upcoming_etas: List[StationETA] = []

        for st in upcoming_meta:
            sch_arr = st.get("scheduled_arrival_time", "")
            sch_dep = st.get("scheduled_departure_time", "")
            sch_arr_offset = float(st.get("scheduled_arrival_offset_min", 0.0))

            eta = StationETA(
                station_id=st["station_id"],
                station_name=st.get("station_name", st["station_id"]),
                sequence=st.get("sequence", 0),
                distance_from_origin_km=float(st.get("distance_from_origin_km", 0.0)),
                scheduled_arrival_time=sch_arr,
                scheduled_departure_time=sch_dep,
                predicted_arrival_time=sch_arr,
                predicted_departure_time=sch_dep,
                predicted_arrival_offset_min=sch_arr_offset,
                predicted_delay_min=0.0
            )
            upcoming_etas.append(eta)

        dest_eta = upcoming_etas[-1] if upcoming_etas else None

        return ETAPrediction(
            train_id=state.train_id,
            route_id=state.route_id,
            model_name="SCHEDULED",
            prediction_timestamp=state.timestamp,
            current_delay_min=state.current_delay_min,
            current_position_km=state.current_position_km,
            upcoming_stations=upcoming_etas,
            destination_eta=dest_eta
        )

    def predict_schedule_plus_delay(self, state: TrainState) -> ETAPrediction:
        """
        Baseline 2: Scheduled ETA + Current Delay Propagation.
        Assumes current delay propagates statically to all downstream stations.
        """
        upcoming_meta = self.get_upcoming_stations(state)
        upcoming_etas: List[StationETA] = []
        delay = state.current_delay_min

        for st in upcoming_meta:
            sch_arr = st.get("scheduled_arrival_time", "")
            sch_dep = st.get("scheduled_departure_time", "")
            sch_arr_offset = float(st.get("scheduled_arrival_offset_min", 0.0))

            pred_arr = self._add_minutes_to_timestr(sch_arr, delay)
            pred_dep = self._add_minutes_to_timestr(sch_dep, delay)
            pred_offset = sch_arr_offset + delay

            eta = StationETA(
                station_id=st["station_id"],
                station_name=st.get("station_name", st["station_id"]),
                sequence=st.get("sequence", 0),
                distance_from_origin_km=float(st.get("distance_from_origin_km", 0.0)),
                scheduled_arrival_time=sch_arr,
                scheduled_departure_time=sch_dep,
                predicted_arrival_time=pred_arr,
                predicted_departure_time=pred_dep,
                predicted_arrival_offset_min=round(pred_offset, 2),
                predicted_delay_min=round(delay, 2)
            )
            upcoming_etas.append(eta)

        dest_eta = upcoming_etas[-1] if upcoming_etas else None

        return ETAPrediction(
            train_id=state.train_id,
            route_id=state.route_id,
            model_name="SCHEDULE_PLUS_DELAY",
            prediction_timestamp=state.timestamp,
            current_delay_min=state.current_delay_min,
            current_position_km=state.current_position_km,
            upcoming_stations=upcoming_etas,
            destination_eta=dest_eta
        )

    def predict_section_runtime(
        self, state: TrainState,
        section_medians: Optional[Dict[str, float]] = None
    ) -> ETAPrediction:
        """
        Baseline 3: Historical Section Median Aggregator.
        Calculates ETA by accumulating from the current timestamp forward, using
        historical section median running times (when available) + scheduled dwells.

        Args:
            state: Current train state snapshot.
            section_medians: Optional dict mapping section_id -> historical median
                running time in minutes. If not provided, falls back to scheduled
                section running times.
        """
        upcoming_meta = self.get_upcoming_stations(state)
        upcoming_etas: List[StationETA] = []

        if not upcoming_meta:
            return ETAPrediction(
                train_id=state.train_id,
                route_id=state.route_id,
                model_name="HISTORICAL_MEDIAN",
                prediction_timestamp=state.timestamp,
                current_delay_min=state.current_delay_min,
                current_position_km=state.current_position_km,
                upcoming_stations=[],
                destination_eta=None
            )

        # Accumulate time forward from the current timestamp
        cumulative_min = 0.0

        for i, st in enumerate(upcoming_meta):
            stn_id = st["station_id"]
            sch_arr = st.get("scheduled_arrival_time", "")
            sch_dep = st.get("scheduled_departure_time", "")
            sch_arr_offset = float(st.get("scheduled_arrival_offset_min", 0.0))

            # Find the section leading into this station
            sec = self._find_section_to_station(stn_id)
            if sec:
                sec_id = sec["section_id"]
                if section_medians and sec_id in section_medians:
                    section_time = section_medians[sec_id]
                else:
                    section_time = float(sec.get("scheduled_running_time_min", 0.0))
            else:
                section_time = 0.0

            cumulative_min += section_time

            # Add dwell time at intermediate stations (not the terminal)
            dwell = 0.0
            if not st.get("is_terminal", False) and i < len(upcoming_meta) - 1:
                dwell = float(st.get("scheduled_dwell_min", 0.0))

            # Predicted arrival = current time + cumulative travel
            pred_arr = self._add_minutes_to_timestr(state.timestamp, cumulative_min)

            # Predicted departure = arrival + dwell
            pred_dep = self._add_minutes_to_timestr(state.timestamp, cumulative_min + dwell)

            # Predicted delay = difference between predicted and scheduled arrival
            predicted_delay = cumulative_min - (sch_arr_offset - self._time_offset_from_origin(state))

            eta = StationETA(
                station_id=stn_id,
                station_name=st.get("station_name", stn_id),
                sequence=st.get("sequence", 0),
                distance_from_origin_km=float(st.get("distance_from_origin_km", 0.0)),
                scheduled_arrival_time=sch_arr,
                scheduled_departure_time=sch_dep,
                predicted_arrival_time=pred_arr,
                predicted_departure_time=pred_dep,
                predicted_arrival_offset_min=round(cumulative_min, 2),
                predicted_delay_min=round(predicted_delay, 2)
            )
            upcoming_etas.append(eta)

            # Add dwell to cumulative for next section
            cumulative_min += dwell

        dest_eta = upcoming_etas[-1] if upcoming_etas else None

        return ETAPrediction(
            train_id=state.train_id,
            route_id=state.route_id,
            model_name="HISTORICAL_MEDIAN",
            prediction_timestamp=state.timestamp,
            current_delay_min=state.current_delay_min,
            current_position_km=state.current_position_km,
            upcoming_stations=upcoming_etas,
            destination_eta=dest_eta
        )

    def _find_section_to_station(self, station_id: str) -> Optional[Dict[str, Any]]:
        """Find the section that leads into the given station (to_station_id == station_id)."""
        for sec in self.sections:
            if sec.get("to_station_id") == station_id:
                return sec
        return None

    def _time_offset_from_origin(self, state: TrainState) -> float:
        """
        Calculate the current elapsed time offset from the origin departure in minutes.
        Uses the station at/near the current position to estimate offset.
        """
        # If at origin, offset is 0
        if state.current_position_km <= 0.0:
            return 0.0

        # Find the station at or just before the current position
        for s in reversed(self.stations):
            dist = float(s.get("distance_from_origin_km", 0.0))
            if dist <= state.current_position_km:
                offset = float(s.get("scheduled_departure_offset_min", 0.0))
                return offset + state.current_delay_min
        return 0.0

    @staticmethod
    def predict_section_time(
        row: Dict[str, Any],
        method: str = "SCHEDULED"
    ) -> float:
        """
        Predict section running time for a single dataset row.

        Args:
            row: Dictionary with dataset columns.
            method: One of 'SCHEDULED', 'SCHEDULE_PLUS_DELAY', 'HISTORICAL_MEDIAN'.

        Returns:
            Predicted section running time in minutes.
        """
        scheduled = float(row.get("scheduled_running_time_min", 0.0))

        if method == "SCHEDULED":
            return scheduled

        elif method == "SCHEDULE_PLUS_DELAY":
            # Use scheduled time but adjust for known previous-section delay trend.
            # If the previous section added delay, assume this section will too (proportionally).
            prev_delta = float(row.get("previous_section_delay_min", 0.0))
            # Clamp: don't predict negative travel time
            return max(0.0, scheduled + prev_delta * 0.5)

        elif method == "HISTORICAL_MEDIAN":
            median = row.get("historical_section_median_min")
            if median is not None and float(median) > 0:
                return float(median)
            return scheduled

        else:
            return scheduled

