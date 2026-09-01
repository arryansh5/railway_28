"""
feature_pipeline.py — Phase 8: Feature Engineering & Preprocessing Pipeline
Extracts, transforms, and standardizes input state features at timestamp t for ML model training and real-time inference.

STRICT ANTI-LEAKAGE RULE:
Consumes strictly current state features (timestamp t).
Zero future targets or future states are accessed during feature construction.
"""

import math
from typing import Dict, Any, List, Tuple


FEATURE_NAMES = [
    "simulation_time_sec",
    "current_position_km",
    "current_speed_kmph",
    "current_speed_mps",
    "target_speed_kmph",
    "current_acceleration_mps2",
    "braking_distance_m",
    "section_speed_limit_kmph",
    "restriction_speed_kmph",
    "approach_speed_kmph",
    "distance_to_next_station_km",
    "distance_to_destination_km",
    "current_delay_min",
    "signal_state_encoded",
    "congestion_level_encoded",
    "fog_active_encoded",
    "fog_visibility_km",
    "unscheduled_halt_encoded",
    "predicted_congestion_probability",
    "predicted_fog_risk",
    "predicted_delay_risk",
    "predicted_speed_impact_encoded",
    "active_predicted_restriction_encoded",
    "predicted_restriction_speed_kmph"
]


def encode_categorical_features(state: Dict[str, Any]) -> Dict[str, float]:
    """Encodes categorical fields into numeric values suitable for tabular ML models."""
    signal_map = {"GREEN": 1.0, "YELLOW": 0.5, "RED": 0.0}
    congestion_map = {"LOW": 0.0, "MEDIUM": 0.5, "HIGH": 1.0}
    impact_map = {"NONE": 0.0, "LIGHT": 0.33, "MEDIUM": 0.66, "SEVERE": 1.0}

    sig_val = signal_map.get(str(state.get("signal_state", "GREEN")).upper(), 1.0)
    cong_val = congestion_map.get(str(state.get("congestion_level", "LOW")).upper(), 0.0)
    impact_val = impact_map.get(str(state.get("predicted_speed_impact", "NONE")).upper(), 0.0)

    fog_act = 1.0 if bool(state.get("fog_active", False)) else 0.0
    un_halt = 1.0 if bool(state.get("unscheduled_halt", False)) else 0.0
    has_res = 1.0 if state.get("active_predicted_restriction") and str(state.get("active_predicted_restriction")).upper() != "NONE" else 0.0

    return {
        "signal_state_encoded": sig_val,
        "congestion_level_encoded": cong_val,
        "fog_active_encoded": fog_act,
        "unscheduled_halt_encoded": un_halt,
        "predicted_speed_impact_encoded": impact_val,
        "active_predicted_restriction_encoded": has_res
    }


def extract_features_from_dict(state: Dict[str, Any]) -> List[float]:
    """
    Extracts a feature vector (List[float]) from a train state dictionary at timestamp t.
    """
    encoded = encode_categorical_features(state)

    def _get_num(key: str, default: float = 0.0) -> float:
        val = state.get(key)
        if val is None or val == "":
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    feature_vector = [
        _get_num("simulation_time_sec", 0.0),
        _get_num("current_position_km", 0.0),
        _get_num("current_speed_kmph", 0.0),
        _get_num("current_speed_mps", 0.0),
        _get_num("target_speed_kmph", 0.0),
        _get_num("current_acceleration_mps2", 0.0),
        _get_num("braking_distance_m", 0.0),
        _get_num("section_speed_limit_kmph", 110.0),
        _get_num("restriction_speed_kmph", 110.0),
        _get_num("approach_speed_kmph", 60.0),
        _get_num("distance_to_next_station_km", 0.0),
        _get_num("distance_to_destination_km", 0.0),
        _get_num("current_delay_min", 0.0),
        encoded["signal_state_encoded"],
        encoded["congestion_level_encoded"],
        encoded["fog_active_encoded"],
        _get_num("fog_visibility_km", 10.0),
        encoded["unscheduled_halt_encoded"],
        _get_num("predicted_congestion_probability", 0.0),
        _get_num("predicted_fog_risk", 0.0),
        _get_num("predicted_delay_risk", 0.0),
        encoded["predicted_speed_impact_encoded"],
        encoded["active_predicted_restriction_encoded"],
        _get_num("predicted_restriction_speed_kmph", 110.0)
    ]

    return feature_vector
