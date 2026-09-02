"""
ml_predictor.py — Phase 8: System 2 Machine Learning Predictor
Extends BasePredictor interface so that MLETAEngineModel can plug directly into System 2
within the 30-second closed-loop simulator.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

from src.data_generator.prediction_engine import BasePredictor, ConditionPrediction, BaselinePredictiveEngine
from src.prediction.ml_model import MLETAEngineModel

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class MLETAEngine(BasePredictor):
    """
    Phase 8 System 2 Predictor: Combines XGBoost ML ETA predictions
    with empirical condition risk assessment for System 3 consumption.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        calibration_filepath: str = str(PROJECT_ROOT / "config" / "historical_calibration.json")
    ):
        # Default baseline condition predictor for probabilistic risk thresholds
        self.baseline_predictor = None
        if os.path.exists(calibration_filepath):
            try:
                self.baseline_predictor = BaselinePredictiveEngine(calibration_filepath)
            except Exception:
                pass

        # Load or initialize ML model
        self.ml_model = None
        target_model_path = model_path or str(PROJECT_ROOT / "models" / "xgboost_eta_model.pkl")

        if os.path.exists(target_model_path):
            try:
                self.ml_model = MLETAEngineModel.load_model(target_model_path)
            except Exception as e:
                print(f"[MLETAEngine] Failed loading model from {target_model_path}: {e}")

        if self.ml_model is None:
            print("[MLETAEngine] No pre-trained model found. Training initial XGBoost/ML model...")
            self.ml_model = MLETAEngineModel(model_type="xgboost")
            dataset_path = str(PROJECT_ROOT / "Data" / "ml" / "ml_ready_dataset.csv")
            if os.path.exists(dataset_path):
                self.ml_model.train_from_csv(dataset_path)
                self.ml_model.save_model(str(PROJECT_ROOT / "models"))

    def predict(
        self,
        current_state: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ConditionPrediction:
        """
        Calculates predicted operational risk conditions and dynamic ETA using Phase 8 ML model.
        Features consumed strictly at timestamp t. Zero future state access.
        """
        # Get ML model ETA predictions
        eta_preds = self.ml_model.predict_state(current_state)

        operational_risk = 0.20
        confidence = 0.90
        evidence = {}
        if self.baseline_predictor:
            base_pred = self.baseline_predictor.predict(current_state, context)
            congestion_risk = base_pred.congestion_risk
            fog_risk = base_pred.fog_risk
            delay_risk = base_pred.delay_risk
            operational_risk = base_pred.operational_risk
            confidence = base_pred.confidence
            expected_speed_impact = base_pred.expected_speed_impact
            evidence = base_pred.evidence
        else:
            current_delay = float(current_state.get("current_delay_min", 0.0))
            delay_risk = min(1.0, current_delay / 60.0)
            congestion_risk = 0.5 if str(current_state.get("congestion_level")).upper() == "HIGH" else 0.1
            fog_risk = 0.6 if bool(current_state.get("fog_active")) else 0.1
            expected_speed_impact = "SEVERE" if congestion_risk > 0.7 or fog_risk > 0.7 else "NONE"

        summary = (
            f"ML ETA Dest: {eta_preds['predicted_eta_destination_min']}m | "
            f"Next: {eta_preds['predicted_eta_next_station_min']}m | Impact: {expected_speed_impact}"
        )

        return ConditionPrediction(
            prediction_timestamp=str(current_state.get("timestamp", "00:00:00")),
            prediction_horizon_min=float(context.get("prediction_horizon_min", 30.0) if context else 30.0),
            congestion_risk=round(congestion_risk, 4),
            fog_risk=round(fog_risk, 4),
            operational_risk=round(operational_risk, 4),
            delay_risk=round(delay_risk, 4),
            confidence=round(confidence, 2),
            expected_speed_impact=expected_speed_impact,
            predicted_condition_summary=summary,
            prediction_source=f"ML_XGBOOST_{self.ml_model.model_type.upper()}",
            evidence=evidence
        )
