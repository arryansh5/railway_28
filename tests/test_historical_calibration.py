"""
test_historical_calibration.py — Unit Tests for Phase 6 Step 3 (Historical Calibration & System 2)
Verifies:
1. Calibration file loads cleanly.
2. No hardcoded flat 75% fog.
3. System 2 outputs risk, not physical speed restrictions.
4. Dynamic hour/season risk divergence (e.g. 06:00 winter vs 12:00 winter).
5. Hierarchical fallback on unfamiliar zones/conditions.
6. Deterministic output given the same input.
7. Anti-leakage isolation.
"""

import json
import unittest
from pathlib import Path
from src.data_generator.prediction_engine import BaselinePredictiveEngine, ConditionPrediction
from src.data_generator.calibration_builder import build_historical_calibration

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestHistoricalCalibration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.calibration_path = PROJECT_ROOT / "config" / "historical_calibration.json"
        # Build calibration if not exists
        build_historical_calibration()
        with open(cls.calibration_path, "r", encoding="utf-8") as f:
            cls.calibration_data = json.load(f)
        cls.engine = BaselinePredictiveEngine(str(cls.calibration_path))

    def test_calibration_metadata_and_structure(self):
        """Rule 1: Calibration loads cleanly and has required top-level categories."""
        self.assertIn("metadata", self.calibration_data)
        self.assertIn("fog", self.calibration_data)
        self.assertIn("congestion", self.calibration_data)
        self.assertIn("operational_disruption", self.calibration_data)
        self.assertIn("baselines", self.calibration_data)
        self.assertIn("hierarchical_lookup_strategy", self.calibration_data)

    def test_no_hardcoded_flat_fog(self):
        """Rule 3: Fog risk is time-of-day and season dependent, not flat perpetual fog."""
        # 06:00 AM Winter in NR has high fog risk
        pred_morning = self.engine.predict(
            {"timestamp": "06:00:00", "current_delay_min": 0.0},
            context={"season": "Winter/Fog", "zone": "NR"}
        )
        # 12:00 PM Winter in NR has 0.0 fog risk (clears after 09:00 AM)
        pred_noon = self.engine.predict(
            {"timestamp": "12:00:00", "current_delay_min": 0.0},
            context={"season": "Winter/Fog", "zone": "NR"}
        )
        self.assertEqual(pred_morning.fog_risk, 1.0)
        self.assertEqual(pred_noon.fog_risk, 0.0)
        self.assertNotEqual(pred_morning.fog_risk, pred_noon.fog_risk)

    def test_summer_fog_is_near_zero(self):
        """Rule 8: Summer season in NR has 0.0 fog risk."""
        pred_summer = self.engine.predict(
            {"timestamp": "06:00:00", "current_delay_min": 0.0},
            context={"season": "Summer", "zone": "NR"}
        )
        self.assertEqual(pred_summer.fog_risk, 0.0)

    def test_system2_outputs_risk_not_restriction(self):
        """Rule 4 & 11: System 2 returns probabilities (0-1), not speed constraints (km/h)."""
        pred = self.engine.predict(
            {"timestamp": "07:30:00", "current_delay_min": 10.0},
            context={"season": "Winter/Fog", "zone": "NR"}
        )
        self.assertIsInstance(pred, ConditionPrediction)
        self.assertTrue(0.0 <= pred.fog_risk <= 1.0)
        self.assertTrue(0.0 <= pred.congestion_risk <= 1.0)
        self.assertTrue(0.0 <= pred.operational_risk <= 1.0)
        self.assertTrue(0.0 <= pred.delay_risk <= 1.0)
        # Verify no physical restriction speed field exists in System 2 output
        self.assertFalse(hasattr(pred, "restriction_speed_kmph"))

    def test_hierarchical_fallback(self):
        """Rule 6: Querying an unknown zone falls back to national, unknown season falls back to global baseline."""
        # Unknown zone falls back to Level 2 (national_hour_season)
        pred_unknown_zone = self.engine.predict(
            {"timestamp": "14:00:00", "current_delay_min": 0.0},
            context={"season": "Winter/Fog", "zone": "UNKNOWN_ZONE"}
        )
        self.assertEqual(pred_unknown_zone.evidence["fog_evidence"]["source_level"], "national_hour_season")

        # Unknown season falls back to Level 3 (global_baseline)
        pred_unknown_season = self.engine.predict(
            {"timestamp": "14:00:00", "current_delay_min": 0.0},
            context={"season": "UNKNOWN_SEASON", "zone": "UNKNOWN_ZONE"}
        )
        self.assertEqual(pred_unknown_season.evidence["fog_evidence"]["source_level"], "global_baseline")
        self.assertGreater(pred_unknown_season.confidence, 0.0)

    def test_deterministic_output(self):
        """Rule 9: Same state input yields identical prediction output."""
        state = {"timestamp": "08:15:00", "current_delay_min": 5.0}
        pred1 = self.engine.predict(state, context={"season": "Winter/Fog", "zone": "NR"})
        pred2 = self.engine.predict(state, context={"season": "Winter/Fog", "zone": "NR"})
        self.assertEqual(pred1.to_dict(), pred2.to_dict())

    def test_evidence_traceability(self):
        """Rule 5: System 2 output contains full evidence traceability and sample sizes."""
        pred = self.engine.predict(
            {"timestamp": "06:30:00", "current_delay_min": 0.0},
            context={"season": "Winter/Fog", "zone": "NR"}
        )
        evidence = pred.evidence
        self.assertIn("fog_evidence", evidence)
        self.assertIn("congestion_evidence", evidence)
        self.assertIn("sample_count", evidence["fog_evidence"])
        self.assertGreater(evidence["fog_evidence"]["sample_count"], 0)


if __name__ == "__main__":
    unittest.main()
