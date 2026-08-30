"""
Unit tests for the Train State Engine (Phase 4).
"""

import json
import unittest
from pathlib import Path

from src.state_engine.state_engine import StateEngine
from src.state_engine.train_state import TrainState


class TestStateEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        route_path = Path(__file__).resolve().parent.parent / "Data" / "routes" / "delhi_dehradun_route.json"
        with open(route_path, "r", encoding="utf-8") as f:
            cls.route = json.load(f)

    def setUp(self):
        self.engine = StateEngine(self.route)

    def test_initial_state_at_origin(self):
        """Test state initialization on the first observation at NDLS origin."""
        obs = {
            "observation_id": "OBS_0001",
            "timestamp": "2026-08-30T07:00:00",
            "train_id": "12017",
            "route_id": "ROUTE_NDLS_DDN_01",
            "latitude": 28.6425,
            "longitude": 77.2195,
            "current_speed_kmph": 0.0,
            "current_position_km": 0.0,
            "current_section_id": None,
            "current_station_id": "NDLS",
            "previous_station_id": None,
            "next_station_id": "GZB",
            "distance_to_next_station_km": 25.0,
            "current_delay_min": 0.0,
            "movement_state": "STOPPED",
            "station_event": "ORIGIN_DEPARTURE",
            "active_event_ids": []
        }

        state = self.engine.ingest(obs)

        self.assertIsInstance(state, TrainState)
        self.assertEqual(state.train_id, "12017")
        self.assertEqual(state.route_id, "ROUTE_NDLS_DDN_01")
        self.assertEqual(state.current_position_km, 0.0)
        self.assertEqual(state.current_station_id, "NDLS")
        self.assertIsNone(state.previous_station_id)
        self.assertEqual(state.next_station_id, "GZB")
        self.assertEqual(state.percent_journey_complete, 0.0)
        self.assertEqual(state.distance_to_destination_km, 314.0)
        self.assertEqual(state.distance_to_next_station_km, 25.0)
        self.assertEqual(state.current_speed_kmph, 0.0)
        self.assertEqual(state.movement_state, "STOPPED")
        self.assertEqual(state.delay_trend, "STABLE")

    def test_mid_journey_progress_and_distances(self):
        """Test kinematics, distance calculations, and progress halfway through the corridor."""
        obs = {
            "observation_id": "OBS_0200",
            "timestamp": "2026-08-30T09:30:00",
            "train_id": "12017",
            "route_id": "ROUTE_NDLS_DDN_01",
            "latitude": 29.4700,
            "longitude": 77.7000,
            "current_speed_kmph": 92.5,
            "current_position_km": 157.0,
            "current_section_id": "SEC_MOZ_SRE",
            "current_station_id": None,
            "previous_station_id": "MOZ",
            "next_station_id": "SRE",
            "current_delay_min": 5.0,
            "movement_state": "CRUISING",
            "active_event_ids": ["EVT_CONGESTION_MED"]
        }

        state = self.engine.ingest(obs)

        self.assertEqual(state.current_position_km, 157.0)
        self.assertEqual(state.percent_journey_complete, 50.0)  # 157.0 / 314.0
        self.assertEqual(state.distance_to_destination_km, 157.0)
        # SRE is at km 187.0 -> distance_to_next_station should be 187.0 - 157.0 = 30.0
        self.assertEqual(state.distance_to_next_station_km, 30.0)
        self.assertEqual(state.current_speed_kmph, 92.5)
        self.assertEqual(state.movement_state, "CRUISING")
        self.assertIn("EVT_CONGESTION_MED", state.active_events)

    def test_delay_trend_transitions(self):
        """Test WORSENING, IMPROVING, and STABLE delay trend logic."""
        # 1. Rising delay -> WORSENING
        for delay in [0.0, 1.0, 3.0]:
            state = self.engine.ingest({"current_delay_min": delay, "current_position_km": 10.0})
        self.assertEqual(state.delay_trend, "WORSENING")

        # 2. Recovering delay -> IMPROVING
        for delay in [3.0, 2.0, 0.5]:
            state = self.engine.ingest({"current_delay_min": delay, "current_position_km": 50.0})
        self.assertEqual(state.delay_trend, "IMPROVING")

        # 3. Steady delay -> STABLE
        for delay in [0.5, 0.6, 0.7]:
            state = self.engine.ingest({"current_delay_min": delay, "current_position_km": 100.0})
        self.assertEqual(state.delay_trend, "STABLE")

    def test_station_history_and_events(self):
        """Test station history accumulation for arrival, dwell, and departure."""
        # Arrive at GZB
        self.engine.ingest({
            "current_station_id": "GZB",
            "timestamp": "2026-08-30T07:30:00",
            "current_position_km": 25.0,
            "station_event": "ARRIVED",
            "actual_arrival_time": "07:30:00",
            "arrival_delay_min": 2.0,
            "movement_state": "DWELLING"
        })

        # Depart from GZB
        state = self.engine.ingest({
            "current_station_id": "GZB",
            "timestamp": "2026-08-30T07:32:00",
            "current_position_km": 25.0,
            "station_event": "DEPARTED",
            "actual_departure_time": "07:32:00",
            "actual_dwell_min": 2.0,
            "departure_delay_min": 2.0,
            "movement_state": "DEPARTING"
        })

        self.assertEqual(len(state.station_history), 1)
        gzb_record = state.station_history[0]
        self.assertEqual(gzb_record["station_id"], "GZB")
        self.assertEqual(gzb_record["arrival_time"], "07:30:00")
        self.assertEqual(gzb_record["departure_time"], "07:32:00")
        self.assertEqual(gzb_record["dwell_min"], 2.0)
        self.assertEqual(gzb_record["arrival_delay_min"], 2.0)
        self.assertEqual(gzb_record["departure_delay_min"], 2.0)
        self.assertEqual(state.last_arrival_delay_min, 2.0)
        self.assertEqual(state.last_departure_delay_min, 2.0)

    def test_destination_completion(self):
        """Test journey completion state at Dehradun terminal."""
        obs = {
            "observation_id": "OBS_0491",
            "timestamp": "2026-08-30T12:40:00",
            "train_id": "12017",
            "route_id": "ROUTE_NDLS_DDN_01",
            "current_speed_kmph": 0.0,
            "current_position_km": 314.0,
            "current_station_id": "DDN",
            "next_station_id": None,
            "station_event": "ARRIVED",
            "current_delay_min": 3.0,
            "movement_state": "COMPLETED"
        }

        state = self.engine.ingest(obs)

        self.assertEqual(state.movement_state, "COMPLETED")
        self.assertEqual(state.percent_journey_complete, 100.0)
        self.assertEqual(state.distance_to_destination_km, 0.0)
        self.assertEqual(state.distance_to_next_station_km, 0.0)
        self.assertEqual(state.current_station_id, "DDN")
        self.assertIsNone(state.next_station_id)

    def test_to_dict_serialization(self):
        """Test serialization to dictionary."""
        obs = {
            "train_id": "12017",
            "route_id": "ROUTE_NDLS_DDN_01",
            "current_position_km": 100.0,
            "current_speed_kmph": 80.0
        }
        state = self.engine.ingest(obs)
        d = state.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["train_id"], "12017")
        self.assertEqual(d["current_position_km"], 100.0)
        self.assertEqual(d["current_speed_kmph"], 80.0)


if __name__ == "__main__":
    unittest.main()
