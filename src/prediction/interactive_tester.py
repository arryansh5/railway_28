"""
interactive_tester.py — Interactive Terminal AI Prediction Tester

Allows the user to interactively test the Phase 8 Machine Learning ETA Model
by entering custom train positions, speeds, delays, and seasons.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.prediction.ml_predictor import MLETAEngine


def main():
    print("=" * 78)
    print("      INDIAN RAILWAYS AI DELAY & ETA PREDICTION — INTERACTIVE TESTER")
    print("=" * 78)
    print("Loading Phase 8 Machine Learning Engine...")

    engine = MLETAEngine()
    print("Engine loaded successfully!\n")

    routes = {
        "1": {"name": "New Delhi -> Dehradun (314 km)", "dest": 314.0, "code": "DDN"},
        "2": {"name": "New Delhi -> Agra Cantt (195 km)", "dest": 195.0, "code": "AGC"},
        "3": {"name": "New Delhi -> Lucknow (512 km)", "dest": 512.0, "code": "LKO"}
    }

    while True:
        print("\n" + "-" * 78)
        print("Select a route to test:")
        print("  1. New Delhi -> Dehradun (314 km)")
        print("  2. New Delhi -> Agra Cantt (195 km)")
        print("  3. New Delhi -> Lucknow (512 km)")
        print("  q. Quit")
        choice = input("\nEnter choice (1/2/3/q): ").strip()

        if choice.lower() == "q":
            print("\nExiting interactive tester. Happy testing!")
            break

        if choice not in routes:
            print("Invalid choice, defaulting to New Delhi -> Dehradun.")
            choice = "1"

        rinfo = routes[choice]
        total_dist = rinfo["dest"]

        print(f"\nTesting Route: {rinfo['name']}")

        # Get user inputs with sensible defaults
        try:
            pos_input = input(f"Enter Current Position in km (0 to {total_dist}) [default: 75]: ").strip()
            pos = float(pos_input) if pos_input else 75.0
            pos = max(0.0, min(total_dist, pos))

            speed_input = input("Enter Current Speed in km/h (0 to 160) [default: 90]: ").strip()
            speed = float(speed_input) if speed_input else 90.0

            delay_input = input("Enter Current Delay in minutes (0 to 180) [default: 15]: ").strip()
            delay = float(delay_input) if delay_input else 15.0

            print("\nSelect Season: 1. Winter/Fog  2. Monsoon  3. Summer [default: 1]")
            s_choice = input("Enter choice (1/2/3): ").strip()
            season = "Monsoon" if s_choice == "2" else ("Summer" if s_choice == "3" else "Winter/Fog")

        except ValueError:
            print("Invalid number entered, using defaults (Pos=75km, Speed=90km/h, Delay=15min, Winter/Fog).")
            pos, speed, delay, season = 75.0, 90.0, 15.0, "Winter/Fog"

        dist_to_dest = max(0.0, total_dist - pos)
        dist_to_next = min(35.0, dist_to_dest)

        mock_state = {
            "timestamp": "08:30:00",
            "current_position_km": pos,
            "current_speed_kmph": speed,
            "current_acceleration_mps2": 0.0,
            "movement_state": "CRUISING" if speed > 20 else "ACCELERATING",
            "current_delay_min": delay,
            "distance_to_next_station_km": dist_to_next,
            "distance_to_destination_km": dist_to_dest,
            "departure_hour": 8,
            "season": season,
            "is_peak_hour": True,
            "is_fog_risk": season == "Winter/Fog",
            "fog_active": season == "Winter/Fog" and pos < 100.0,
        }

        print("\n" + "=" * 50)
        print("          AI PREDICTION RESULTS")
        print("=" * 50)
        pred = engine.predict(mock_state, context={"season": season, "zone": "NR"})

        print(f"  • Destination Remaining Dist : {dist_to_dest:.1f} km")
        print(f"  • Current Accumulated Delay  : {delay:.1f} min")
        print(f"  • AI Predicted Condition     : {pred.predicted_condition_summary}")
        print(f"  • Fog Risk Probability       : {pred.fog_risk * 100:.1f}%")
        print(f"  • Track Congestion Risk      : {pred.congestion_risk * 100:.1f}%")
        print(f"  • Overall Delay Risk Level   : {pred.delay_risk * 100:.1f}%")
        print(f"  • Operational Speed Impact   : {pred.expected_speed_impact}")
        print("=" * 50)


if __name__ == "__main__":
    main()
