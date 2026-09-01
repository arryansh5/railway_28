"""
test_system2_system3_integration.py — Integration Tests for Phase 6 Step 5 (System 2 -> System 3)

Tests:
1. Medium Congestion creation.
2. Severe Congestion escalation without duplicate event creation.
3. Risk clearing and restriction expiration.
4. Fog scenario creation and speed cap resolution.
5. Multiple simultaneous risks (min constraint prioritization).
6. Full risk fluctuation (CREATE -> UPDATE -> DOWNGRADE -> EXPIRE).
7. Section transition handling.
8. Stale/out-of-order prediction rejection.
9. 4-Cycle End-to-End Micro Simulation.
"""

import unittest
from pathlib import Path
from src.data_generator.prediction_engine import BaselinePredictiveEngine, ConditionPrediction
from src.data_generator.restriction_engine import RestrictionEngine, SyntheticRestriction, RestrictionDecision
from src.data_generator.calibration_builder import build_historical_calibration

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestSystem2System3Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.calibration_path = PROJECT_ROOT / "config" / "historical_calibration.json"
        build_historical_calibration()
        cls.system2 = BaselinePredictiveEngine(str(cls.calibration_path))

    def setUp(self):
        self.system3 = RestrictionEngine(str(self.calibration_path))

    def test_scenario_1_medium_congestion_creation(self):
        """Test 1: System 2 produces Medium Congestion risk -> System 3 creates 1 restriction (60 km/h)."""
        pred = ConditionPrediction(
            prediction_timestamp="08:30:00",
            prediction_horizon_min=30.0,
            congestion_risk=0.55,
            fog_risk=0.10,
            operational_risk=0.20,
            delay_risk=0.55,
            confidence=0.90,
            expected_speed_impact="MEDIUM",
            predicted_condition_summary="MODERATE CONGESTION",
            prediction_source="TEST"
        )
        state = {"current_section_id": "SEC_NDLS_GZB", "current_position_km": 10.0}
        decision = self.system3.evaluate_and_decide(pred, state)

        self.assertEqual(decision.action, "CREATE")
        self.assertEqual(len(decision.active_restrictions), 1)
        res = decision.active_restrictions[0]
        self.assertEqual(res.restriction_id, "PRED_CONG_01")
        self.assertEqual(res.status, "ACTIVE")
        self.assertEqual(res.restriction_speed_kmph, 60.0)
        self.assertEqual(decision.effective_speed_cap_kmph, 60.0)

    def test_scenario_2_severe_congestion_escalation_no_duplicates(self):
        """Test 2: Existing Medium restriction is escalated to High -> UPDATED, no duplicate."""
        state = {"current_section_id": "SEC_NDLS_GZB", "current_position_km": 10.0}
        
        # Step 1: Medium (60 km/h)
        pred1 = ConditionPrediction("08:30:00", 30.0, 0.55, 0.10, 0.20, 0.55, 0.90, "MEDIUM", "MED", "TEST")
        self.system3.evaluate_and_decide(pred1, state)

        # Step 2: High (25 km/h)
        pred2 = ConditionPrediction("08:30:30", 30.0, 0.80, 0.10, 0.40, 0.80, 0.90, "SEVERE", "HIGH", "TEST")
        decision2 = self.system3.evaluate_and_decide(pred2, state)

        self.assertEqual(decision2.action, "UPDATE")
        self.assertEqual(len(decision2.active_restrictions), 1)
        res = decision2.active_restrictions[0]
        self.assertEqual(res.restriction_id, "PRED_CONG_01")
        self.assertEqual(res.status, "UPDATED")
        self.assertEqual(res.restriction_speed_kmph, 25.0)
        self.assertEqual(decision2.effective_speed_cap_kmph, 25.0)

    def test_scenario_3_risk_clears_expiration(self):
        """Test 3: Risk drops below threshold -> Restriction EXPIRED, speed cap returns to 999.0."""
        state = {"current_section_id": "SEC_NDLS_GZB", "current_position_km": 10.0}
        
        # Active restriction
        pred1 = ConditionPrediction("08:30:00", 30.0, 0.55, 0.10, 0.20, 0.55, 0.90, "MEDIUM", "MED", "TEST")
        self.system3.evaluate_and_decide(pred1, state)

        # Cleared risk (0.20 < 0.45)
        pred2 = ConditionPrediction("08:31:00", 30.0, 0.20, 0.10, 0.10, 0.20, 0.90, "NONE", "CLEAR", "TEST")
        decision2 = self.system3.evaluate_and_decide(pred2, state)

        self.assertEqual(decision2.action, "EXPIRE")
        self.assertEqual(len(decision2.active_restrictions), 1)
        self.assertEqual(decision2.active_restrictions[0].status, "EXPIRED")
        self.assertEqual(decision2.effective_speed_cap_kmph, 999.0)

    def test_scenario_4_fog_scenario_creation(self):
        """Test 4: Fog risk above threshold -> Creates FOG restriction (40 km/h)."""
        pred = ConditionPrediction("06:45:00", 30.0, 0.10, 0.65, 0.20, 0.65, 0.90, "MEDIUM", "FOG", "TEST")
        state = {"current_section_id": "SEC_NDLS_GZB", "current_position_km": 5.0}
        decision = self.system3.evaluate_and_decide(pred, state)

        self.assertEqual(decision.action, "CREATE")
        fog_res = [r for r in decision.active_restrictions if r.condition_type == "FOG"]
        self.assertEqual(len(fog_res), 1)
        self.assertEqual(fog_res[0].restriction_speed_kmph, 40.0)
        self.assertEqual(decision.effective_speed_cap_kmph, 40.0)

    def test_scenario_5_multiple_simultaneous_risks(self):
        """Test 5: Fog (40 km/h) + High Congestion (25 km/h) -> Effective cap is min(40, 25) = 25 km/h."""
        pred = ConditionPrediction("07:00:00", 30.0, 0.80, 0.70, 0.50, 0.85, 0.90, "SEVERE", "MULTI", "TEST")
        state = {"current_section_id": "SEC_NDLS_GZB", "current_position_km": 15.0}
        decision = self.system3.evaluate_and_decide(pred, state)

        self.assertEqual(len(decision.active_restrictions), 2)
        self.assertEqual(decision.effective_speed_cap_kmph, 25.0)

    def test_scenario_6_risk_fluctuation_lifecycle(self):
        """Test 6: Lifecycle sequence: CREATE (60) -> UPDATE (25) -> DOWNGRADE (60) -> EXPIRE (999)."""
        state = {"current_section_id": "SEC_NDLS_GZB", "current_position_km": 15.0}

        # Step 1: CREATE Medium (60 km/h)
        p1 = ConditionPrediction("08:00:00", 30.0, 0.50, 0.0, 0.20, 0.50, 0.9, "MEDIUM", "MED", "TEST")
        d1 = self.system3.evaluate_and_decide(p1, state)
        self.assertEqual(d1.action, "CREATE")
        self.assertEqual(d1.effective_speed_cap_kmph, 60.0)

        # Step 2: UPDATE to High (25 km/h)
        p2 = ConditionPrediction("08:00:30", 30.0, 0.75, 0.0, 0.40, 0.75, 0.9, "SEVERE", "HIGH", "TEST")
        d2 = self.system3.evaluate_and_decide(p2, state)
        self.assertEqual(d2.action, "UPDATE")
        self.assertEqual(d2.effective_speed_cap_kmph, 25.0)

        # Step 3: DOWNGRADE back to Medium (60 km/h)
        p3 = ConditionPrediction("08:01:00", 30.0, 0.50, 0.0, 0.20, 0.50, 0.9, "MEDIUM", "MED", "TEST")
        d3 = self.system3.evaluate_and_decide(p3, state)
        self.assertEqual(d3.action, "DOWNGRADE")
        self.assertEqual(d3.effective_speed_cap_kmph, 60.0)

        # Step 4: EXPIRE (999.0 km/h)
        p4 = ConditionPrediction("08:01:30", 30.0, 0.20, 0.0, 0.10, 0.20, 0.9, "NONE", "CLEAR", "TEST")
        d4 = self.system3.evaluate_and_decide(p4, state)
        self.assertEqual(d4.action, "EXPIRE")
        self.assertEqual(d4.effective_speed_cap_kmph, 999.0)

    def test_scenario_7_section_transition_handling(self):
        """Test 7: Moving from SEC_NDLS_GZB to SEC_GZB_MTC shifts active restriction section."""
        state1 = {"current_section_id": "SEC_NDLS_GZB", "current_position_km": 24.0}
        pred1 = ConditionPrediction("07:15:00", 30.0, 0.60, 0.0, 0.20, 0.60, 0.9, "MEDIUM", "MED", "TEST")
        self.system3.evaluate_and_decide(pred1, state1)

        state2 = {"current_section_id": "SEC_GZB_MTC", "current_position_km": 26.5}
        pred2 = ConditionPrediction("07:15:30", 30.0, 0.60, 0.0, 0.20, 0.60, 0.9, "MEDIUM", "MED", "TEST")
        decision2 = self.system3.evaluate_and_decide(pred2, state2)

        self.assertEqual(decision2.active_restrictions[0].target_section_id, "SEC_GZB_MTC")

    def test_scenario_8_stale_prediction_rejection(self):
        """Test 8: Receiving older timestamp after newer timestamp is rejected."""
        state = {"current_section_id": "SEC_NDLS_GZB", "current_position_km": 10.0}
        pred_new = ConditionPrediction("08:30:00", 30.0, 0.50, 0.0, 0.20, 0.50, 0.9, "MED", "MED", "TEST")
        self.system3.evaluate_and_decide(pred_new, state)

        pred_old = ConditionPrediction("08:29:30", 30.0, 0.80, 0.0, 0.40, 0.80, 0.9, "HIGH", "HIGH", "TEST")
        decision_stale = self.system3.evaluate_and_decide(pred_old, state)

        self.assertEqual(decision_stale.action, "REJECTED_STALE")

    def test_four_cycle_end_to_end_micro_simulation(self):
        """Test 9: 4-cycle simulation across evolving System 1 states."""
        sim_states = [
            {"timestamp": "06:45:00", "current_position_km": 0.0, "current_speed_kmph": 0.0, "current_delay_min": 0.0, "current_section_id": "SEC_NDLS_GZB"},
            {"timestamp": "06:45:30", "current_position_km": 0.5, "current_speed_kmph": 38.0, "current_delay_min": 0.0, "current_section_id": "SEC_NDLS_GZB"},
            {"timestamp": "06:46:00", "current_position_km": 1.2, "current_speed_kmph": 75.0, "current_delay_min": 0.5, "current_section_id": "SEC_NDLS_GZB"},
            {"timestamp": "06:46:30", "current_position_km": 2.0, "current_speed_kmph": 85.0, "current_delay_min": 0.8, "current_section_id": "SEC_NDLS_GZB"}
        ]

        decisions = []
        for state in sim_states:
            # 1. System 2 Predicts from State
            pred = self.system2.predict(state, context={"season": "Winter/Fog", "zone": "NR"})
            # 2. System 3 Decides from Prediction
            decision = self.system3.evaluate_and_decide(pred, state)
            decisions.append(decision)

        # Verify all 4 cycles processed in order
        self.assertEqual(len(decisions), 4)
        for i in range(4):
            self.assertEqual(decisions[i].timestamp, sim_states[i]["timestamp"])
            self.assertTrue(decisions[i].effective_speed_cap_kmph <= 110.0)


if __name__ == "__main__":
    unittest.main()
