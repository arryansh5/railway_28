"""
Unit tests for the Baseline ETA Engine and Evaluation Metrics (Phase 5).
"""

import json
import unittest
from pathlib import Path

from src.state_engine.train_state import TrainState
from src.prediction.baseline_engine import BaselineETAEngine
from src.prediction.metrics import EvaluationMetrics


class TestBaselineETAEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        route_path = Path(__file__).resolve().parent.parent / "Data" / "routes" / "delhi_dehradun_route.json"
        with open(route_path, "r", encoding="utf-8") as f:
            cls.route = json.load(f)

    def setUp(self):
        self.engine = BaselineETAEngine(self.route)

    def test_scheduled_baseline_at_origin(self):
        """Test Baseline 1 (Scheduled ETA) from origin station."""
        state = TrainState(
            train_id="12017",
            route_id="ROUTE_NDLS_DDN_01",
            timestamp="2026-08-30T06:45:00",
            current_position_km=0.0,
            current_station_id="NDLS",
            current_speed_kmph=0.0,
            movement_state="STOPPED",
            current_delay_min=0.0
        )

        pred = self.engine.predict_scheduled(state)

        self.assertEqual(pred.model_name, "SCHEDULED")
        self.assertEqual(pred.train_id, "12017")
        self.assertEqual(len(pred.upcoming_stations), 7)  # GZB to DDN
        self.assertEqual(pred.upcoming_stations[0].station_id, "GZB")
        self.assertEqual(pred.upcoming_stations[0].predicted_arrival_time, "07:13")
        self.assertEqual(pred.upcoming_stations[0].predicted_delay_min, 0.0)

        # Destination ETA
        self.assertIsNotNone(pred.destination_eta)
        self.assertEqual(pred.destination_eta.station_id, "DDN")
        self.assertEqual(pred.destination_eta.predicted_arrival_time, "12:22")

    def test_schedule_plus_delay_propagation(self):
        """Test Baseline 2 (Scheduled + Delay) forward propagation."""
        state = TrainState(
            train_id="12017",
            route_id="ROUTE_NDLS_DDN_01",
            timestamp="2026-08-30T07:45:00",
            current_position_km=25.0,  # at GZB
            current_station_id="GZB",
            current_speed_kmph=0.0,
            movement_state="DWELLING",
            current_delay_min=15.0  # 15 minutes late
        )

        pred = self.engine.predict_schedule_plus_delay(state)

        self.assertEqual(pred.model_name, "SCHEDULE_PLUS_DELAY")
        self.assertEqual(len(pred.upcoming_stations), 6)  # MTC through DDN

        # MTC scheduled is 07:55 -> +15 min = 08:10
        mtc = pred.upcoming_stations[0]
        self.assertEqual(mtc.station_id, "MTC")
        self.assertEqual(mtc.predicted_arrival_time, "08:10")
        self.assertEqual(mtc.predicted_delay_min, 15.0)

        # DDN scheduled is 12:22 -> +15 min = 12:37
        self.assertEqual(pred.destination_eta.station_id, "DDN")
        self.assertEqual(pred.destination_eta.predicted_arrival_time, "12:37")
        self.assertEqual(pred.destination_eta.predicted_delay_min, 15.0)

    def test_mid_route_upcoming_filtering(self):
        """Test filtering of upcoming stations when train is midway through journey."""
        state = TrainState(
            train_id="12017",
            route_id="ROUTE_NDLS_DDN_01",
            timestamp="2026-08-30T08:50:00",
            current_position_km=130.0,  # Past MOZ (128.0 km)
            current_section_id="SEC_MOZ_SRE",
            current_speed_kmph=90.0,
            movement_state="CRUISING",
            current_delay_min=5.0
        )

        pred = self.engine.predict_schedule_plus_delay(state)

        # Upcoming stations should be: SRE (187.0), RK (221.0), HW (263.0), DDN (314.0)
        station_ids = [s.station_id for s in pred.upcoming_stations]
        self.assertEqual(station_ids, ["SRE", "RK", "HW", "DDN"])

    def test_completed_journey_empty_upcoming(self):
        """Test that reaching destination produces no upcoming stations."""
        state = TrainState(
            train_id="12017",
            route_id="ROUTE_NDLS_DDN_01",
            timestamp="2026-08-30T12:25:00",
            current_position_km=314.0,
            current_station_id="DDN",
            movement_state="COMPLETED",
            current_delay_min=3.0
        )

        pred = self.engine.predict_scheduled(state)
        self.assertEqual(len(pred.upcoming_stations), 0)
        self.assertIsNone(pred.destination_eta)

    def test_evaluation_metrics_calculations(self):
        """Test evaluation metrics calculations (MAE, RMSE, P90, accuracies)."""
        actuals = [10.0, 15.0, 20.0, 25.0, 30.0]
        preds = [12.0, 14.0, 22.0, 28.0, 31.0]
        # errors = [2.0, 1.0, 2.0, 3.0, 1.0] -> MAE = 9.0 / 5 = 1.8
        # squared = [4.0, 1.0, 4.0, 9.0, 1.0] = 19.0 -> RMSE = sqrt(3.8) ~= 1.95
        # sorted errors = [1.0, 1.0, 2.0, 2.0, 3.0] -> P90 = 3.0
        # all <= 5.0 -> accuracy_5 = 100%, accuracy_10 = 100%

        metrics = EvaluationMetrics.compute(actuals, preds)

        self.assertEqual(metrics["count"], 5)
        self.assertEqual(metrics["mae"], 1.8)
        self.assertEqual(metrics["rmse"], 1.95)
        self.assertEqual(metrics["p90_error"], 3.0)
        self.assertEqual(metrics["accuracy_within_5_min"], 100.0)
        self.assertEqual(metrics["accuracy_within_10_min"], 100.0)


if __name__ == "__main__":
    unittest.main()
