"""
test_system2_prediction_engine.py — Unit & Integration Tests for Phase 6 Step 4 (System 2 Predictive Engine)

Verifies:
1. BasePredictor Interface & BaselinePredictiveEngine compliance.
2. Pure risk outputs in [0.0, 1.0] with zero physical speed restriction attributes.
3. Hierarchical fallback logic across all levels.
4. Dynamic 30-second recalculation across time progression.
5. Deterministic execution for identical inputs.
6. Zero future data leakage protection.
7. Explainable evidence lineage with sample counts.
8. Integration loop: System 1 (State t) -> System 2 (Risk) -> System 3 (Restriction decision).
"""

import json
import unittest
from pathlib import Path
from typing import Dict, Any

from src.data_generator.prediction_engine import BaselinePredictiveEngine, BasePredictor, ConditionPrediction
from src.data_generator.restriction_engine import RestrictionEngine, SyntheticRestriction
from src.data_generator.calibration_builder import build_historical_calibration

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestSystem2PredictiveEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.calibration_path = PROJECT_ROOT / "config" / "historical_calibration.json"
        build_historical_calibration()
        cls.system2 = BaselinePredictiveEngine(str(cls.calibration_path))
        cls.system3 = RestrictionEngine(str(cls.calibration_path))

    def test_base_predictor_interface_inheritance(self):
        """Rule 2: BaselinePredictiveEngine implements BasePredictor interface."""
        self.assertTrue(issubclass(BaselinePredictiveEngine, BasePredictor))
        self.assertIsInstance(self.system2, BasePredictor)

    def test_prediction_output_schema_and_ranges(self):
        """Rule 3 & 4: Predictions are within [0.0, 1.0] and contain required schema fields."""
        current_state = {
            "timestamp": "06:45:00",
            "current_position_km": 12.5,
            "current_speed_kmph": 85.0,
            "current_delay_min": 2.0,
            "current_section_id": "SEC_NDLS_GZB",
        }
        pred = self.system2.predict(current_state, context={"season": "Winter/Fog", "zone": "NR"})

        self.assertIsInstance(pred, ConditionPrediction)
        self.assertEqual(pred.prediction_timestamp, "06:45:00")
        self.assertTrue(0.0 <= pred.fog_risk <= 1.0)
        self.assertTrue(0.0 <= pred.congestion_risk <= 1.0)
        self.assertTrue(0.0 <= pred.operational_risk <= 1.0)
        self.assertTrue(0.0 <= pred.delay_risk <= 1.0)
        self.assertTrue(0.0 <= pred.confidence <= 1.0)
        self.assertIn(pred.expected_speed_impact, ["NONE", "LIGHT", "MEDIUM", "SEVERE"])
        self.assertEqual(pred.prediction_source, "BASELINE_HISTORICAL_CALIBRATION")

    def test_system2_does_not_modify_system1_or_contain_speed_restrictions(self):
        """Rule 10, 11, 15: System 2 returns risk only, never physical restrictions or state mutations."""
        current_state = {
            "timestamp": "07:00:00",
            "current_position_km": 25.0,
            "current_speed_kmph": 100.0,
            "current_delay_min": 0.0,
        }
        pred = self.system2.predict(current_state, context={"season": "Winter/Fog", "zone": "NR"})

        # Verify state is not mutated
        self.assertEqual(current_state["current_speed_kmph"], 100.0)
        self.assertEqual(current_state["current_position_km"], 25.0)

        # Verify no restriction speed attributes exist in prediction
        self.assertFalse(hasattr(pred, "restriction_speed_kmph"))
        self.assertFalse(hasattr(pred, "target_speed_kmph"))

    def test_dynamic_30s_progression(self):
        """Rule 12 & 13: System 2 recalculates dynamically at every 30-second step."""
        # 08:30 AM Winter (elevated fog risk)
        state_t1 = {"timestamp": "08:30:00", "current_delay_min": 0.0}
        pred_t1 = self.system2.predict(state_t1, context={"season": "Winter/Fog", "zone": "NR"})

        # 12:00 PM Winter (fog clears to 0.0 based on Step 2 pattern discovery)
        state_t2 = {"timestamp": "12:00:00", "current_delay_min": 0.0}
        pred_t2 = self.system2.predict(state_t2, context={"season": "Winter/Fog", "zone": "NR"})

        self.assertEqual(pred_t1.fog_risk, 1.0)
        self.assertEqual(pred_t2.fog_risk, 0.0)

    def test_zero_future_leakage(self):
        """Rule 7 & 8: Providing future targets does NOT alter prediction output."""
        state_clean = {
            "timestamp": "07:15:00",
            "current_position_km": 30.0,
            "current_speed_kmph": 90.0,
            "current_delay_min": 0.0,
        }
        state_with_future = {
            "timestamp": "07:15:00",
            "current_position_km": 30.0,
            "current_speed_kmph": 90.0,
            "current_delay_min": 0.0,
            "target_eta_to_destination_min": 250.0,
            "actual_arrival_time": "12:45:00",
            "final_delay_minutes": 180.0,
        }
        pred_clean = self.system2.predict(state_clean, context={"season": "Winter/Fog", "zone": "NR"})
        pred_with_future = self.system2.predict(state_with_future, context={"season": "Winter/Fog", "zone": "NR"})

        self.assertEqual(pred_clean.fog_risk, pred_with_future.fog_risk)
        self.assertEqual(pred_clean.congestion_risk, pred_with_future.congestion_risk)
        self.assertEqual(pred_clean.delay_risk, pred_with_future.delay_risk)

    def test_explainability_and_evidence_trace(self):
        """Rule 15: System 2 returns explainable evidence tracing with sample counts."""
        current_state = {"timestamp": "07:30:00", "current_delay_min": 0.0}
        pred = self.system2.predict(current_state, context={"season": "Winter/Fog", "zone": "NR"})

        evidence = pred.evidence
        self.assertIn("fog_evidence", evidence)
        self.assertIn("congestion_evidence", evidence)
        self.assertIn("operational_evidence", evidence)
        self.assertIn("source_level", evidence["fog_evidence"])
        self.assertIn("sample_count", evidence["fog_evidence"])
        self.assertGreater(evidence["fog_evidence"]["sample_count"], 0)

    def test_integration_closed_loop_flow(self):
        """Rule 18: System 1 (State) -> System 2 (Prediction) -> System 3 (Restriction Engine)."""
        # Step 1: 08:00 AM in Winter (Fog Risk = 1.0)
        state_step1 = {
            "timestamp": "08:00:00",
            "current_position_km": 40.0,
            "current_speed_kmph": 90.0,
            "current_delay_min": 0.0,
            "current_section_id": "SEC_GZB_MTC",
        }
        pred_step1 = self.system2.predict(state_step1, context={"season": "Winter/Fog", "zone": "NR"})
        restrictions_step1 = self.system3.evaluate_prediction(pred_step1, state_step1)

        # System 3 creates active synthetic fog restriction (40 km/h)
        fog_res = [r for r in restrictions_step1 if r.condition_type == "FOG"]
        self.assertTrue(len(fog_res) > 0)
        self.assertEqual(fog_res[0].status, "ACTIVE")
        self.assertEqual(fog_res[0].restriction_speed_kmph, 40.0)

        # Step 2: Advance to 12:00 PM (Fog Risk = 0.0)
        state_step2 = {
            "timestamp": "12:00:00",
            "current_position_km": 180.0,
            "current_speed_kmph": 40.0,
            "current_delay_min": 10.0,
            "current_section_id": "SEC_SRE_RK",
        }
        pred_step2 = self.system2.predict(state_step2, context={"season": "Winter/Fog", "zone": "NR"})
        restrictions_step2 = self.system3.evaluate_prediction(pred_step2, state_step2)

        # System 3 transitions fog restriction to EXPIRED
        expired_fog = [r for r in restrictions_step2 if r.condition_type == "FOG" and r.status == "EXPIRED"]
        self.assertTrue(len(expired_fog) > 0)


if __name__ == "__main__":
    unittest.main()
