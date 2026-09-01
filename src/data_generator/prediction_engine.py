"""
prediction_engine.py — Phase 6: Step 3
System 2: Delay Risk / Condition Prediction Engine.

Consumes:
- Current RTIS State at timestamp t (position, speed, delay, section, station, hour, weather observation)
- Historical Calibration (config/historical_calibration.json)

Produces:
- ConditionPrediction object containing:
  - fog_risk (0.0 to 1.0)
  - congestion_risk (0.0 to 1.0)
  - operational_risk (0.0 to 1.0)
  - overall_delay_risk (0.0 to 1.0)
  - confidence (0.0 to 1.0 based on sample counts)
  - evidence (detailed hierarchical lookup lineage)

STRICT RULES:
1. System 2 produces RISK ONLY (NO physical speed restrictions — that belongs to System 3).
2. Zero future state leakage (only timestamp t features consumed).
3. Pure data-derived hierarchical lookup (no arbitrary multipliers).
"""

import os
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class ConditionPrediction:
    """Dataclass holding predicted operational risk conditions for System 2."""
    prediction_timestamp: str
    prediction_horizon_min: float
    congestion_risk: float        # 0.0 to 1.0 (empirical probability of high congestion/delay)
    fog_risk: float               # 0.0 to 1.0 (empirical probability of active fog)
    operational_risk: float       # 0.0 to 1.0 (empirical probability of operational delay)
    delay_risk: float             # 0.0 to 1.0 (empirical overall probability of destination delay)
    confidence: float             # 0.0 to 1.0 (data reliability score based on sample size N)
    expected_speed_impact: str    # "NONE" | "LIGHT" | "MEDIUM" | "SEVERE"
    predicted_condition_summary: str
    prediction_source: str        # "BASELINE_HISTORICAL_CALIBRATION" or "ML_MODEL"
    evidence: Dict[str, Any] = field(default_factory=dict)

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
    Baseline System 2 Predictor using pure empirical calibration priors from Step 3.
    """

    def __init__(
        self,
        calibration_filepath: str = str(PROJECT_ROOT / "config" / "historical_calibration.json")
    ):
        if not os.path.exists(calibration_filepath):
            raise FileNotFoundError(f"Calibration file not found at: {calibration_filepath}")

        with open(calibration_filepath, "r", encoding="utf-8") as f:
            self.calibration = json.load(f)

        self.fog_data = self.calibration.get("fog", {})
        self.congestion_data = self.calibration.get("congestion", {})
        self.op_data = self.calibration.get("operational_disruption", {})
        self.baselines = self.calibration.get("baselines", {})
        self.reliability_weights = {
            "HIGH": 1.00,
            "MEDIUM": 0.75,
            "LOW": 0.40,
            "INSUFFICIENT": 0.10
        }

    def _extract_hour(self, timestamp_str: str) -> int:
        """Extracts integer hour from HH:MM:SS string."""
        try:
            return int(timestamp_str.split(":")[0])
        except Exception:
            return 7

    def _lookup_fog_risk(self, season: str, hour: int, zone: str = "NR") -> Dict[str, Any]:
        """Hierarchical lookup for empirical fog risk."""
        hr_str = str(hour)
        
        # Level 1: NR/NCR Regional Matrix (Corridor Proxy)
        if zone in ["NR", "NCR"]:
            nr_ncr_season = self.fog_data.get("by_hour_and_season_NR_NCR", {}).get(season, {})
            if hr_str in nr_ncr_season:
                entry = nr_ncr_season[hr_str]
                if entry.get("sample_count", 0) >= 30:
                    return {
                        "probability": entry["probability"],
                        "sample_count": entry["sample_count"],
                        "reliability": entry["reliability"],
                        "source_level": "NR_NCR_hour_season"
                    }

        # Level 2: National Season x Hour Matrix
        nat_season = self.fog_data.get("by_hour_and_season_national", {}).get(season, {})
        if hr_str in nat_season:
            entry = nat_season[hr_str]
            if entry.get("sample_count", 0) >= 30:
                return {
                    "probability": entry["probability"],
                    "sample_count": entry["sample_count"],
                    "reliability": entry["reliability"],
                    "source_level": "national_hour_season"
                }

        # Level 3: Global Baseline Fallback
        base = self.fog_data.get("global_baseline", {})
        return {
            "probability": base.get("probability", 0.0367),
            "sample_count": base.get("sample_count", 1043531),
            "reliability": "HIGH",
            "source_level": "global_baseline"
        }

    def _lookup_congestion_risk(self, hour: int, zone: str = "NR") -> Dict[str, Any]:
        """Hierarchical lookup for empirical congestion risk."""
        hr_str = str(hour)

        # Level 1: NR/NCR Regional Matrix
        if zone in ["NR", "NCR"]:
            nr_ncr_cong = self.congestion_data.get("by_hour_NR_NCR", {})
            if hr_str in nr_ncr_cong:
                entry = nr_ncr_cong[hr_str]
                if entry.get("sample_count", 0) >= 30:
                    return {
                        "probability": entry.get("p_congestion_delay_cause", 0.20),
                        "mean_index": entry.get("mean_congestion_index", 0.77),
                        "sample_count": entry.get("sample_count", 0),
                        "reliability": entry.get("reliability", "HIGH"),
                        "source_level": "NR_NCR_hour_congestion_cause"
                    }

        # Level 2: Global Fallback
        base = self.congestion_data.get("global_baseline", {})
        return {
            "probability": 0.2093,
            "mean_index": base.get("mean_congestion_index", 0.773),
            "sample_count": base.get("sample_count", 1043531),
            "reliability": "HIGH",
            "source_level": "global_baseline"
        }

    def _lookup_operational_risk(
        self,
        late_incoming_rake: bool = False,
        fog_active: bool = False,
        high_congestion: bool = False
    ) -> Dict[str, Any]:
        """Hierarchical lookup for empirical operational delay risk."""
        compounds = self.op_data.get("compound_conditions", {})

        # Compound Interactions
        if late_incoming_rake and fog_active:
            entry = compounds.get("LateRake_AND_Fog")
            if entry and entry.get("sample_count", 0) >= 30:
                return {
                    "probability": entry["p_delayed"],
                    "p_heavy_delay": entry["p_heavy_delay"],
                    "mean_delay_min": entry["mean_delay_min"],
                    "sample_count": entry["sample_count"],
                    "reliability": entry["reliability"],
                    "source_level": "compound_LateRake_Fog"
                }

        if late_incoming_rake and high_congestion:
            entry = compounds.get("LateRake_AND_HighCongestion")
            if entry and entry.get("sample_count", 0) >= 30:
                return {
                    "probability": entry["p_delayed"],
                    "p_heavy_delay": entry["p_heavy_delay"],
                    "mean_delay_min": entry["mean_delay_min"],
                    "sample_count": entry["sample_count"],
                    "reliability": entry["reliability"],
                    "source_level": "compound_LateRake_HighCongestion"
                }

        # Single Factor Lookup
        if late_incoming_rake:
            entry = self.op_data.get("late_incoming_rake", {}).get("active", {})
            return {
                "probability": entry.get("p_delayed", 0.87),
                "p_heavy_delay": entry.get("p_heavy_delay", 0.87),
                "mean_delay_min": entry.get("mean_delay_min", 130.39),
                "sample_count": entry.get("sample_count", 112555),
                "reliability": "HIGH",
                "source_level": "late_incoming_rake_active"
            }

        # Clean Baseline
        entry = compounds.get("Clean_Conditions (No LateRake, No Fog, Normal Congestion)", {})
        return {
            "probability": entry.get("p_delayed", 0.4541),
            "p_heavy_delay": entry.get("p_heavy_delay", 0.45),
            "mean_delay_min": entry.get("mean_delay_min", 58.63),
            "sample_count": entry.get("sample_count", 250000),
            "reliability": "HIGH",
            "source_level": "clean_baseline"
        }

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
        - zone (default "NR")
        - is_fog_active_observed (bool, if local locomotive sensor detects fog)
        - late_incoming_rake (bool)
        """
        ctx = context or {}
        season = ctx.get("season", "Winter/Fog")
        zone = ctx.get("zone", "NR")
        prediction_horizon_min = float(ctx.get("prediction_horizon_min", 30.0))

        timestamp_str = current_state.get("timestamp", "07:00:00")
        hour_int = self._extract_hour(timestamp_str)
        current_delay = float(current_state.get("current_delay_min", 0.0))
        late_rake = bool(current_state.get("late_incoming_rake", False))

        # 1. Fog Risk Hierarchical Lookup
        fog_res = self._lookup_fog_risk(season=season, hour=hour_int, zone=zone)
        fog_risk = fog_res["probability"]
        # If train physically observes fog in current section, observed state confirms active fog
        if current_state.get("is_fog_active_observed", False):
            fog_risk = max(fog_risk, 1.0)

        # 2. Congestion Risk Hierarchical Lookup
        cong_res = self._lookup_congestion_risk(hour=hour_int, zone=zone)
        congestion_risk = cong_res["probability"]

        # 3. Operational Disruption Risk Lookup
        is_high_cong = congestion_risk >= 0.70
        is_fog = fog_risk >= 0.50
        op_res = self._lookup_operational_risk(
            late_incoming_rake=late_rake,
            fog_active=is_fog,
            high_congestion=is_high_cong
        )
        operational_risk = op_res["probability"]

        # 4. Overall Delay Risk (Empirical Destination Delay Probability)
        # Directly derived from operational, congestion, and fog historical conditions
        overall_delay_risk = max(operational_risk, congestion_risk, fog_risk)
        if current_delay > 15.0:
            overall_delay_risk = min(1.0, max(overall_delay_risk, 0.95))

        # 5. Data Reliability Confidence Score
        conf_scores = [
            self.reliability_weights.get(fog_res.get("reliability", "HIGH"), 1.0),
            self.reliability_weights.get(cong_res.get("reliability", "HIGH"), 1.0),
            self.reliability_weights.get(op_res.get("reliability", "HIGH"), 1.0),
        ]
        confidence = round(sum(conf_scores) / len(conf_scores), 2)

        # 6. Expected Speed Impact Categorization (Risk Severity only)
        if congestion_risk >= 0.70 or (late_rake and is_fog):
            speed_impact = "SEVERE"
            summary = "HIGH TRACK CONGESTION / DISRUPTION RISK (Severe operational friction expected)"
        elif congestion_risk >= 0.45 or fog_risk >= 0.40:
            speed_impact = "MEDIUM"
            summary = "MODERATE CONGESTION / FOG RISK (Moderate operational friction expected)"
        elif congestion_risk >= 0.25:
            speed_impact = "LIGHT"
            summary = "LIGHT CONGESTION RISK (Minor operational friction expected)"
        else:
            speed_impact = "NONE"
            summary = "NORMAL CLEAR OPERATIONAL RISK BASELINE"

        evidence = {
            "fog_evidence": fog_res,
            "congestion_evidence": cong_res,
            "operational_evidence": op_res,
            "hour": hour_int,
            "season": season,
            "zone": zone,
        }

        return ConditionPrediction(
            prediction_timestamp=timestamp_str,
            prediction_horizon_min=prediction_horizon_min,
            congestion_risk=round(congestion_risk, 4),
            fog_risk=round(fog_risk, 4),
            operational_risk=round(operational_risk, 4),
            delay_risk=round(overall_delay_risk, 4),
            confidence=confidence,
            expected_speed_impact=speed_impact,
            predicted_condition_summary=summary,
            prediction_source="BASELINE_HISTORICAL_CALIBRATION",
            evidence=evidence
        )


if __name__ == "__main__":
    predictor = BaselinePredictiveEngine()
    test_state = {
        "timestamp": "06:45:00",
        "current_position_km": 15.2,
        "current_speed_kmph": 85.0,
        "current_delay_min": 0.0,
    }
    pred = predictor.predict(test_state, context={"season": "Winter/Fog", "zone": "NR"})
    print("\n--- Sample System 2 Risk Prediction ---")
    print(json.dumps(pred.to_dict(), indent=2))
