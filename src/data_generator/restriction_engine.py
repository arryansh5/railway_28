"""
restriction_engine.py — Phase 6: Step 5
System 3: Dynamic Restriction / Scenario Decision Engine.

Translates System 2 operational risk predictions into stateful simulation constraints.

Key Responsibilities:
1. Evaluates ConditionPrediction probabilities against calibration thresholds.
2. Manages restriction lifecycle: ACTIVE, UPDATED, DOWNGRADED, UNCHANGED, EXPIRED, REMOVED.
3. Prevents duplicate active restrictions across 30-second simulation steps.
4. Handles section transitions and scope association.
5. Rejects stale/out-of-order predictions.
6. Emits clean structured RestrictionDecision and effective speed caps to System 1.
"""

import os
import json
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.data_generator.prediction_engine import ConditionPrediction

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class SyntheticRestriction:
    """Dataclass representing a dynamic synthetic restriction managed by System 3."""
    restriction_id: str
    source: str                      # "PREDICTED_SYNTHETIC"
    condition_type: str              # "CONGESTION" | "FOG" | "OPERATIONAL_RISK"
    status: str                      # "ACTIVE" | "UPDATED" | "UNCHANGED" | "EXPIRED"
    restriction_speed_kmph: float    # e.g., 25.0, 40.0, 60.0
    start_time: str
    last_updated_time: str
    target_section_id: str
    target_position_km: float
    description: str

    def to_dict(self) -> Dict[str, Any]:
        """Converts restriction to a plain dictionary."""
        return asdict(self)


@dataclass
class RestrictionDecision:
    """Dataclass representing System 3's output to System 1 at timestamp t."""
    timestamp: str
    action: str                      # "NO_ACTION" | "CREATE" | "UPDATE" | "DOWNGRADE" | "EXPIRE"
    active_restrictions: List[SyntheticRestriction]
    effective_speed_cap_kmph: float  # Min speed cap across all active restrictions (999.0 if clear)
    decision_log: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Converts decision to a plain dictionary."""
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "active_restrictions": [r.to_dict() for r in self.active_restrictions],
            "effective_speed_cap_kmph": self.effective_speed_cap_kmph,
            "decision_log": self.decision_log
        }


class RestrictionEngine:
    """
    System 3 Restriction Decision Engine & State Machine.
    """

    def __init__(
        self,
        calibration_filepath: str = str(PROJECT_ROOT / "config" / "historical_calibration.json")
    ):
        if not os.path.exists(calibration_filepath):
            raise FileNotFoundError(f"Calibration file not found at: {calibration_filepath}")

        with open(calibration_filepath, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.thresholds = self.config.get("speed_impact_thresholds", {
            "HIGH_CONGESTION": {"probability_threshold": 0.70, "restriction_speed_kmph": 25.0},
            "MEDIUM_CONGESTION": {"probability_threshold": 0.45, "restriction_speed_kmph": 60.0},
            "FOG_RESTRICTION": {"probability_threshold": 0.40, "restriction_speed_kmph": 40.0}
        })

        # Stateful registry for active synthetic restrictions
        self.active_restrictions: Dict[str, SyntheticRestriction] = {}
        self.last_processed_timestamp: Optional[str] = None
        self.last_section_id: Optional[str] = None

    def _parse_time(self, time_str: str) -> datetime:
        """Helper to parse HH:MM:SS string."""
        return datetime.strptime(time_str, "%H:%M:%S")

    def evaluate_prediction(
        self,
        prediction: ConditionPrediction,
        current_state: Dict[str, Any]
    ) -> List[SyntheticRestriction]:
        """
        Evaluates System 2 prediction against thresholds and updates active restrictions.
        Returns all current active/expired restrictions in this 30s step.
        """
        decision_obj = self.evaluate_and_decide(prediction, current_state)
        return decision_obj.active_restrictions

    def evaluate_and_decide(
        self,
        prediction: ConditionPrediction,
        current_state: Dict[str, Any]
    ) -> RestrictionDecision:
        """
        Main decision loop:
        1. Checks for stale predictions.
        2. Handles section transitions.
        3. Evaluates congestion and fog risks against calibration thresholds.
        4. Updates lifecycle (CREATE / UPDATE / DOWNGRADE / EXPIRE).
        5. Emits RestrictionDecision with effective speed cap.
        """
        timestamp = prediction.prediction_timestamp
        current_section = current_state.get("current_section_id", "UNKNOWN_SECTION")
        current_pos_km = float(current_state.get("current_position_km", 0.0))
        decision_logs = []
        overall_action = "NO_ACTION"

        # Stale Prediction Protection
        if self.last_processed_timestamp is not None:
            curr_dt = self._parse_time(timestamp)
            last_dt = self._parse_time(self.last_processed_timestamp)
            if curr_dt < last_dt:
                log_msg = f"REJECTED STALE PREDICTION: Incoming timestamp {timestamp} is older than last processed {self.last_processed_timestamp}"
                decision_logs.append(log_msg)
                effective_speed = self.resolve_effective_speed_cap(list(self.active_restrictions.values()))
                return RestrictionDecision(
                    timestamp=timestamp,
                    action="REJECTED_STALE",
                    active_restrictions=list(self.active_restrictions.values()),
                    effective_speed_cap_kmph=effective_speed,
                    decision_log=decision_logs
                )

        self.last_processed_timestamp = timestamp

        # Section Transition Handling
        if self.last_section_id is not None and self.last_section_id != current_section:
            for r in self.active_restrictions.values():
                if r.target_section_id == self.last_section_id:
                    r.target_section_id = current_section
                    r.target_position_km = current_pos_km
                    decision_logs.append(f"SECTION_TRANSITION: [{r.restriction_id}] shifted to new section {current_section}")
        self.last_section_id = current_section

        effective_restrictions: List[SyntheticRestriction] = []

        # --- 1. Evaluate Congestion Risk ---
        cong_high_thresh = self.thresholds.get("HIGH_CONGESTION", {}).get("probability_threshold", 0.70)
        cong_med_thresh = self.thresholds.get("MEDIUM_CONGESTION", {}).get("probability_threshold", 0.45)

        target_cong_speed = None
        cong_level_name = None

        if prediction.congestion_risk >= cong_high_thresh:
            target_cong_speed = self.thresholds.get("HIGH_CONGESTION", {}).get("restriction_speed_kmph", 25.0)
            cong_level_name = "HIGH"
        elif prediction.congestion_risk >= cong_med_thresh:
            target_cong_speed = self.thresholds.get("MEDIUM_CONGESTION", {}).get("restriction_speed_kmph", 60.0)
            cong_level_name = "MEDIUM"

        res_key_cong = "PRED_CONG_01"

        if target_cong_speed is not None:
            if res_key_cong in self.active_restrictions:
                existing = self.active_restrictions[res_key_cong]
                if existing.restriction_speed_kmph != target_cong_speed:
                    prev_spd = existing.restriction_speed_kmph
                    existing.restriction_speed_kmph = target_cong_speed
                    if target_cong_speed < prev_spd:
                        existing.status = "UPDATED"
                        overall_action = "UPDATE"
                        decision_logs.append(f"UPDATE: [{res_key_cong}] Congestion escalated ({prev_spd} -> {target_cong_speed} km/h)")
                    else:
                        existing.status = "UPDATED"
                        overall_action = "DOWNGRADE"
                        decision_logs.append(f"DOWNGRADE: [{res_key_cong}] Congestion eased ({prev_spd} -> {target_cong_speed} km/h)")
                    existing.description = f"Predicted {cong_level_name} Congestion (Speed adjusted to {target_cong_speed} km/h)"
                else:
                    existing.status = "UNCHANGED"
                existing.last_updated_time = timestamp
                effective_restrictions.append(existing)
            else:
                new_res = SyntheticRestriction(
                    restriction_id=res_key_cong,
                    source="PREDICTED_SYNTHETIC",
                    condition_type="CONGESTION",
                    status="ACTIVE",
                    restriction_speed_kmph=target_cong_speed,
                    start_time=timestamp,
                    last_updated_time=timestamp,
                    target_section_id=current_section,
                    target_position_km=current_pos_km,
                    description=f"Predicted {cong_level_name} Congestion (Speed cap {target_cong_speed} km/h)"
                )
                self.active_restrictions[res_key_cong] = new_res
                effective_restrictions.append(new_res)
                overall_action = "CREATE"
                decision_logs.append(f"CREATE: [{res_key_cong}] Created {cong_level_name} Congestion restriction ({target_cong_speed} km/h)")
        else:
            if res_key_cong in self.active_restrictions:
                expired_res = self.active_restrictions.pop(res_key_cong)
                expired_res.status = "EXPIRED"
                expired_res.last_updated_time = timestamp
                effective_restrictions.append(expired_res)
                overall_action = "EXPIRE"
                decision_logs.append(f"EXPIRE: [{res_key_cong}] Congestion risk cleared below threshold")

        # --- 2. Evaluate Fog Risk ---
        fog_thresh = self.thresholds.get("FOG_RESTRICTION", {}).get("probability_threshold", 0.40)
        res_key_fog = "PRED_FOG_01"

        if prediction.fog_risk >= fog_thresh:
            target_fog_speed = self.thresholds.get("FOG_RESTRICTION", {}).get("restriction_speed_kmph", 40.0)

            if res_key_fog in self.active_restrictions:
                existing_fog = self.active_restrictions[res_key_fog]
                existing_fog.status = "UNCHANGED"
                existing_fog.last_updated_time = timestamp
                effective_restrictions.append(existing_fog)
            else:
                new_fog = SyntheticRestriction(
                    restriction_id=res_key_fog,
                    source="PREDICTED_SYNTHETIC",
                    condition_type="FOG",
                    status="ACTIVE",
                    restriction_speed_kmph=target_fog_speed,
                    start_time=timestamp,
                    last_updated_time=timestamp,
                    target_section_id=current_section,
                    target_position_km=current_pos_km,
                    description=f"Predicted Fog Visibility Risk (Speed cap {target_fog_speed} km/h)"
                )
                self.active_restrictions[res_key_fog] = new_fog
                effective_restrictions.append(new_fog)
                if overall_action == "NO_ACTION":
                    overall_action = "CREATE"
                decision_logs.append(f"CREATE: [{res_key_fog}] Created Fog restriction ({target_fog_speed} km/h)")
        else:
            if res_key_fog in self.active_restrictions:
                expired_fog = self.active_restrictions.pop(res_key_fog)
                expired_fog.status = "EXPIRED"
                expired_fog.last_updated_time = timestamp
                effective_restrictions.append(expired_fog)
                if overall_action == "NO_ACTION":
                    overall_action = "EXPIRE"
                decision_logs.append(f"EXPIRE: [{res_key_fog}] Fog risk cleared below threshold")

        effective_speed_cap = self.resolve_effective_speed_cap(effective_restrictions)

        return RestrictionDecision(
            timestamp=timestamp,
            action=overall_action,
            active_restrictions=effective_restrictions,
            effective_speed_cap_kmph=effective_speed_cap,
            decision_log=decision_logs
        )

    def resolve_effective_speed_cap(self, restrictions: List[SyntheticRestriction]) -> float:
        """
        Returns the minimum speed cap across all active/updated synthetic restrictions (999.0 if clear).
        """
        min_speed = 999.0
        for r in restrictions:
            if r.status in ["ACTIVE", "UPDATED", "UNCHANGED"]:
                min_speed = min(min_speed, r.restriction_speed_kmph)
        return min_speed


if __name__ == "__main__":
    engine = RestrictionEngine()
    print("[System3 RestrictionEngine] Initialized and verified.")
