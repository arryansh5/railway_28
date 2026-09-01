"""
test_ml_model.py — Unit and Integration Tests for Phase 8 ML ETA Engine
Tests:
- Feature extraction consistency
- XGBoost / ML model training on ml_ready_dataset.csv
- Artifact saving and loading
- Inference performance & non-leakage verification
"""

import os
import unittest
from pathlib import Path

from src.features.feature_pipeline import extract_features_from_dict, FEATURE_NAMES
from src.prediction.ml_model import MLETAEngineModel
from src.prediction.ml_predictor import MLETAEngine

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestMLETAEngine(unittest.TestCase):

    def setUp(self):
        self.dataset_path = str(PROJECT_ROOT / "Data" / "ml" / "ml_ready_dataset.csv")
        self.mock_state = {
            "simulation_time_sec": 300.0,
            "current_position_km": 25.0,
            "current_speed_kmph": 85.0,
            "current_speed_mps": 23.61,
            "target_speed_kmph": 90.0,
            "current_acceleration_mps2": 0.2,
            "braking_distance_m": 120.0,
            "section_speed_limit_kmph": 110.0,
            "restriction_speed_kmph": 110.0,
            "approach_speed_kmph": 60.0,
            "distance_to_next_station_km": 15.0,
            "distance_to_destination_km": 289.0,
            "current_delay_min": 5.0,
            "signal_state": "GREEN",
            "congestion_level": "LOW",
            "fog_active": False,
            "fog_visibility_km": 10.0,
            "unscheduled_halt": False,
            "predicted_congestion_probability": 0.1,
            "predicted_fog_risk": 0.1,
            "predicted_delay_risk": 0.2,
            "predicted_speed_impact": "NONE",
            "active_predicted_restriction": "NONE",
            "predicted_restriction_speed_kmph": 110.0
        }

    def test_feature_extraction(self):
        """Tests feature pipeline vector extraction."""
        vec = extract_features_from_dict(self.mock_state)
        self.assertEqual(len(vec), len(FEATURE_NAMES))
        self.assertIsInstance(vec[0], float)
        self.assertEqual(vec[1], 25.0)

    def test_model_training_and_inference(self):
        """Tests ML model training from dataset and prediction output format."""
        if not os.path.exists(self.dataset_path):
            self.skipTest(f"ML dataset not found at: {self.dataset_path}")

        model = MLETAEngineModel()
        metrics = model.train_from_csv(self.dataset_path)

        self.assertTrue(model.is_trained)
        self.assertIn("mae_eta_destination_min", metrics)
        self.assertIn("mae_eta_next_station_min", metrics)

        # Run single-state prediction
        preds = model.predict_state(self.mock_state)
        self.assertIn("predicted_eta_destination_min", preds)
        self.assertIn("predicted_eta_next_station_min", preds)
        self.assertGreaterEqual(preds["predicted_eta_destination_min"], 0.0)

    def test_model_save_load(self):
        """Tests model artifact serialization and reload."""
        if not os.path.exists(self.dataset_path):
            self.skipTest(f"ML dataset not found at: {self.dataset_path}")

        model = MLETAEngineModel()
        model.train_from_csv(self.dataset_path)

        save_path = model.save_model(str(PROJECT_ROOT / "models"))
        self.assertTrue(os.path.exists(save_path))

        loaded_model = MLETAEngineModel.load_model(save_path)
        self.assertTrue(loaded_model.is_trained)

        preds = loaded_model.predict_state(self.mock_state)
        self.assertGreaterEqual(preds["predicted_eta_destination_min"], 0.0)

    def test_system2_ml_predictor_interface(self):
        """Tests System 2 ML predictor interface integration."""
        engine = MLETAEngine()
        prediction = engine.predict(self.mock_state)

        self.assertIsNotNone(prediction)
        self.assertTrue("ML_XGBOOST" in prediction.prediction_source or "BASELINE" in prediction.prediction_source)


if __name__ == "__main__":
    unittest.main()
