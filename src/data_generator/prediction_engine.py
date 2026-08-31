"""
prediction_engine.py — Phase 6: Steps 4 & 5
System 2: Delay Risk / Condition Prediction Engine.
Consumes current RTIS state (timestamp t) and historical calibration priors.
Predicts risk probabilities over prediction_horizon_minutes (default 30 min):
- congestion_risk (0.0 to 1.0)
- fog_risk (0.0 to 1.0)
- delay_risk (0.0 to 1.0)
- expected_speed_impact ("NONE", "LIGHT", "MEDIUM", "SEVERE")

STRICT ANTI-LEAKAGE RULE:
System 2 consumes ONLY features available at timestamp t.
Zero future states, target ETAs, or future event details are ever accessed.
"""

import os
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, Optional

# Automatically detect project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class ConditionPrediction:
    """Dataclass holding predicted operational risk conditions for System 2."""
    prediction_timestamp: str
    prediction_horizon_min: float
    congestion_risk: float        # 0.0 to 1.0
    fog_risk: float               # 0.0 to 1.0
    delay_risk: float             # 0.0 to 1.0
    expected_speed_impact: str    # "NONE" | "LIGHT" | "MEDIUM" | "SEVERE"
    predicted_condition_summary: str
    prediction_source: str        # "BASELINE_HISTORICAL_PRIOR" or "ML_MODEL"

    def to_dict(self) -> Dict[str, Any]:
        """Converts prediction to a plain dictionary."""
        return asdict(self)


class BasePredictor(ABC):
    """Abstract interface for System 2 Predictive Engine implementations."""

    @abstractmethod
    def predict(
        self,
        current_state: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ConditionPrediction:
        """
        Predicts probable future operational conditions given current state at timestamp t.
        """
        pass


class BaselinePredictiveEngine(BasePredictor):
    """
    Baseline System 2 Predictor using empirical calibration priors from historical data.
    """

    def __init__(
        self,
        calibration_filepath: str = str(PROJECT_ROOT / "config" / "historical_calibration.json")
    ):
        print(f"[System2 Predictor] Loading historical calibration from: {calibration_filepath}")
        if not os.path.exists(calibration_filepath):
            raise FileNotFoundError(f"Calibration file not found at: {calibration_filepath}")

        with open(calibration_filepath, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.hourly_congestion = self.config.get("hourly_congestion_risk", {})
        self.seasonal_fog = self.config.get("seasonal_fog_risk", {})
        self.multipliers = self.config.get("risk_multipliers", {})
        self.thresholds = self.config.get("speed_impact_thresholds", {})

    def predict(
        self,
        current_state: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ConditionPrediction:
        """
        Calculates predicted risk conditions using current state features at timestamp t.

        Features Consumed (Current t only):
        - timestamp (HH:MM:SS)
        - current_position_km
        - current_speed_kmph
        - current_delay_min
        - season (from context or default "Winter/Fog")
        """
        ctx = context or {}
        season = ctx.get("season", "Winter/Fog")
        prediction_horizon_min = float(ctx.get("prediction_horizon_min", 30.0))

        # Extract current time features
        timestamp_str = current_state.get("timestamp", "00:00:00")
        hour_str = str(self._extract_hour(timestamp_str))

        # 1. Congestion Risk Calculation
        base_congestion_prob = float(self.hourly_congestion.get(hour_str, 0.50))
        
        # Apply peak hour multiplier if departure hour is peak
        hour_int = int(hour_str)
        is_peak = (7 <= hour_int <= 10) or (17 <= hour_int <= 20)
        peak_mult = self.multipliers.get("peak_hour_multiplier", 1.20) if is_peak else 1.0
        
        # Current delay stress factor
        current_delay = float(current_state.get("current_delay_min", 0.0))
        delay_factor = 1.15 if current_delay > 15.0 else 1.0

        congestion_risk = min(1.0, max(0.0, base_congestion_prob * peak_mult * delay_factor))

        # 2. Fog Risk Calculation
        base_fog_prob = float(self.seasonal_fog.get(season, 0.34))
        is_night = (hour_int >= 22 or hour_int <= 6)
        night_mult = self.multipliers.get("night_departure_multiplier", 1.05) if is_night else 1.0

        fog_risk = min(1.0, max(0.0, base_fog_prob * night_mult))

        # 3. Overall Delay Risk Calculation
        delay_risk = min(1.0, max(0.0, congestion_risk * 0.5 + fog_risk * 0.3 + (0.2 if current_delay > 10 else 0.0)))

        # 4. Expected Speed Impact Categorization
        if congestion_risk >= 0.70:
            speed_impact = "SEVERE"
            summary = "HIGH TRACK CONGESTION PREDICTED (Speed restricted to ~25 km/h)"
        elif congestion_risk >= 0.45 or fog_risk >= 0.40:
            speed_impact = "MEDIUM"
            summary = "MODERATE CONGESTION / FOG PREDICTED (Speed restricted to 40-60 km/h)"
        elif congestion_risk >= 0.30:
            speed_impact = "LIGHT"
            summary = "LIGHT CONGESTION PREDICTED (Minor speed attenuation)"
        else:
            speed_impact = "NONE"
            summary = "NORMAL OPERATIONAL CONDITIONS PREDICTED"

        return ConditionPrediction(
            prediction_timestamp=timestamp_str,
            prediction_horizon_min=prediction_horizon_min,
            congestion_risk=round(congestion_risk, 4),
            fog_risk=round(fog_risk, 4),
            delay_risk=round(delay_risk, 4),
            expected_speed_impact=speed_impact,
            predicted_condition_summary=summary,
            prediction_source="BASELINE_HISTORICAL_PRIOR"
        )

    @staticmethod
    def _extract_hour(time_str: str) -> int:
        """Helper to extract hour int 0-23 from HH:MM:SS string."""
        try:
            parts = time_str.split(":")
            return int(parts[0]) % 24
        except (ValueError, IndexError):
            return 8  # fallback 8 AM


if __name__ == "__main__":
    predictor = BaselinePredictiveEngine()

    # Test state at 08:30 AM (Peak Hour in Winter/Fog)
    mock_state = {
        "timestamp": "08:30:00",
        "current_position_km": 145.0,
        "current_speed_kmph": 82.0,
        "current_section_id": "SEC_MTC_MOZ",
        "current_delay_min": 18.0
    }

    prediction = predictor.predict(mock_state, context={"season": "Winter/Fog"})

    print("\n" + "=" * 80)
    print("SYSTEM 2: PREDICTIVE CONDITION ENGINE TEST")
    print("=" * 80)
    print(f"Timestamp           : {prediction.prediction_timestamp}")
    print(f"Prediction Horizon  : {prediction.prediction_horizon_min} min")
    print(f"Congestion Risk     : {prediction.congestion_risk * 100:.1f}%")
    print(f"Fog Risk            : {prediction.fog_risk * 100:.1f}%")
    print(f"Overall Delay Risk  : {prediction.delay_risk * 100:.1f}%")
    print(f"Speed Impact Category: {prediction.expected_speed_impact}")
    print(f"Summary             : {prediction.predicted_condition_summary}")
    print("=" * 80)
