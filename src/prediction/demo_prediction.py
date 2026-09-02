"""
demo_prediction.py — Live Demonstration of Phase 8 ML ETA Predictions

Demonstrates how the trained Phase 8 Machine Learning Model (MLETAEngine)
predicts destination ETA, next station ETA, and operational impact at
different milestones along the New Delhi -> Dehradun corridor.
"""

import json
from src.prediction.ml_predictor import MLETAEngine


def run_live_prediction_demo():
    print("=" * 78)
    print("      PHASE 8: LIVE MACHINE LEARNING ETA PREDICTION DEMONSTRATION")
    print("=" * 78)

    # 1. Initialize ML Engine (loads trained XGBoost / Gradient Boosting artifact)
    engine = MLETAEngine()

    # Define 3 operational milestones along the 314 km NDLS -> DDN corridor
    milestones = [
        {
            "name": "1. NDLS Departure (Start of Journey)",
            "state": {
                "timestamp": "06:45:00",
                "current_position_km": 0.0,
                "current_speed_kmph": 0.0,
                "current_acceleration_mps2": 0.5,
                "movement_state": "ACCELERATING",
                "current_delay_min": 0.0,
                "current_section_id": "SEC_NDLS_GZB",
                "current_station_id": "NDLS",
                "distance_to_next_station_km": 25.0,
                "distance_to_destination_km": 314.0,
                "departure_hour": 6,
                "season": "Winter/Fog",
                "is_peak_hour": True,
                "is_fog_risk": True,
                "fog_active": True,
            },
            "context": {"season": "Winter/Fog", "zone": "NR"}
        },
        {
            "name": "2. Passing Meerut City (Mid-Corridor Cruising)",
            "state": {
                "timestamp": "08:15:00",
                "current_position_km": 72.0,
                "current_speed_kmph": 85.0,
                "current_acceleration_mps2": 0.0,
                "movement_state": "CRUISING",
                "current_delay_min": 12.5,
                "current_section_id": "SEC_MTC_MOZ",
                "current_station_id": None,
                "distance_to_next_station_km": 54.0,
                "distance_to_destination_km": 242.0,
                "departure_hour": 8,
                "season": "Winter/Fog",
                "is_peak_hour": True,
                "is_fog_risk": True,
                "fog_active": False,
            },
            "context": {"season": "Winter/Fog", "zone": "NR"}
        },
        {
            "name": "3. Approaching Haridwar (Single-Line Section)",
            "state": {
                "timestamp": "11:30:00",
                "current_position_km": 262.0,
                "current_speed_kmph": 60.0,
                "current_acceleration_mps2": -0.2,
                "movement_state": "DECELERATING",
                "current_delay_min": 18.0,
                "current_section_id": "SEC_RK_HW",
                "current_station_id": None,
                "distance_to_next_station_km": 52.0,
                "distance_to_destination_km": 52.0,
                "departure_hour": 11,
                "season": "Winter/Fog",
                "is_peak_hour": False,
                "is_fog_risk": False,
                "fog_active": False,
            },
            "context": {"season": "Winter/Fog", "zone": "NR"}
        }
    ]

    for m in milestones:
        print(f"\n>>> Milestone: {m['name']}")
        print(f"    Current State: Pos={m['state']['current_position_km']}km | Speed={m['state']['current_speed_kmph']}km/h | Delay={m['state']['current_delay_min']}min | Section={m['state']['current_section_id']}")

        # Predict using Phase 8 ML Engine
        pred = engine.predict(m['state'], context=m['context'])

        print(f"    Prediction Source     : {pred.prediction_source}")
        print(f"    Predicted Condition   : {pred.predicted_condition_summary}")
        print(f"    Fog Risk Probability  : {pred.fog_risk * 100:.1f}%")
        print(f"    Congestion Risk Prob  : {pred.congestion_risk * 100:.1f}%")
        print(f"    Overall Delay Risk    : {pred.delay_risk * 100:.1f}%")
        print(f"    Expected Speed Impact : {pred.expected_speed_impact}")

    print("\n" + "=" * 78)
    print("Demo complete! Phase 8 ML Engine successfully predicts dynamic ETA & operational risks.")
    print("=" * 78)


if __name__ == "__main__":
    run_live_prediction_demo()
