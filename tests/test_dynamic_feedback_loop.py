"""
test_dynamic_feedback_loop.py — Tests for System 1, System 2, and System 3 integration.
Tests:
- System 2 predictor risk evaluation
- System 3 restriction state machine (ACTIVE -> UPDATED -> EXPIRED)
- Closed-loop synthetic journey generation
"""

import unittest
from pathlib import Path
from src.data_generator.prediction_engine import BaselinePredictiveEngine, ConditionPrediction
from src.data_generator.restriction_engine import RestrictionEngine
from src.data_generator.dataset_builder import build_synthetic_journey

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestDynamicFeedbackLoop(unittest.TestCase):

    def setUp(self):
        self.calibration_path = str(PROJECT_ROOT / "config" / "historical_calibration.json")
        self.predictor = BaselinePredictiveEngine(self.calibration_path)
        self.restriction_engine = RestrictionEngine(self.calibration_path)

    def test_system2_prediction(self):
        """Test System 2 probabilistic risk prediction."""
        mock_state = {
            "timestamp": "08:30:00",
            "current_position_km": 145.0,
            "current_speed_kmph": 82.0,
            "current_section_id": "SEC_MTC_MOZ",
            "current_delay_min": 18.0
        }
        pred = self.predictor.predict(mock_state, context={"season": "Winter/Fog"})

        self.assertIsInstance(pred, ConditionPrediction)
        self.assertGreaterEqual(pred.congestion_risk, 0.0)
        self.assertLessEqual(pred.congestion_risk, 1.0)
        self.assertGreaterEqual(pred.fog_risk, 0.0)
        self.assertLessEqual(pred.fog_risk, 1.0)
        self.assertIn(pred.expected_speed_impact, ["NONE", "LIGHT", "MEDIUM", "SEVERE"])

    def test_system3_restriction_lifecycle(self):
        """Test System 3 restriction lifecycle (ACTIVE -> UPDATED -> EXPIRED)."""
        mock_state = {
            "timestamp": "08:30:00",
            "current_position_km": 145.0,
            "current_section_id": "SEC_MTC_MOZ",
            "current_delay_min": 18.0
        }

        # 1. Medium Congestion -> ACTIVE restriction at 60 km/h
        pred1 = ConditionPrediction(
            prediction_timestamp="08:30:00",
            prediction_horizon_min=30.0,
            congestion_risk=0.55,
            fog_risk=0.20,
            delay_risk=0.40,
            expected_speed_impact="MEDIUM",
            predicted_condition_summary="MODERATE CONGESTION PREDICTED",
            prediction_source="BASELINE_HISTORICAL_PRIOR"
        )
        res1 = self.restriction_engine.evaluate_prediction(pred1, mock_state)
        self.assertEqual(len(res1), 1)
        self.assertEqual(res1[0].status, "ACTIVE")
        self.assertEqual(res1[0].restriction_speed_kmph, 60.0)

        # 2. Escalated High Congestion -> UPDATED restriction at 25 km/h
        pred2 = ConditionPrediction(
            prediction_timestamp="08:30:30",
            prediction_horizon_min=30.0,
            congestion_risk=0.75,
            fog_risk=0.20,
            delay_risk=0.60,
            expected_speed_impact="SEVERE",
            predicted_condition_summary="HIGH CONGESTION PREDICTED",
            prediction_source="BASELINE_HISTORICAL_PRIOR"
        )
        res2 = self.restriction_engine.evaluate_prediction(pred2, mock_state)
        self.assertEqual(len(res2), 1)
        self.assertEqual(res2[0].status, "UPDATED")
        self.assertEqual(res2[0].restriction_speed_kmph, 25.0)

        # 3. Risk Clears -> EXPIRED restriction
        pred3 = ConditionPrediction(
            prediction_timestamp="08:31:00",
            prediction_horizon_min=30.0,
            congestion_risk=0.10,
            fog_risk=0.10,
            delay_risk=0.10,
            expected_speed_impact="NONE",
            predicted_condition_summary="NORMAL CONDITIONS PREDICTED",
            prediction_source="BASELINE_HISTORICAL_PRIOR"
        )
        res3 = self.restriction_engine.evaluate_prediction(pred3, mock_state)
        self.assertEqual(len(res3), 1)
        self.assertEqual(res3[0].status, "EXPIRED")

    def test_closed_loop_synthetic_journey(self):
        """Test full closed-loop synthetic journey execution."""
        obs = build_synthetic_journey(
            start_time_str="06:45:00",
            season="Winter/Fog",
            output_csv_path=str(PROJECT_ROOT / "Data" / "synthetic_rtis" / "test_journey.csv")
        )
        self.assertGreater(len(obs), 100)
        self.assertIn("target_eta_to_destination_min", obs[0])
        self.assertIn("predicted_congestion_probability", obs[0])


if __name__ == "__main__":
    unittest.main()
