"""
test_all_scenarios.py — Runs all 10 scenario event scripts through the simulator
and prints a comparative summary matrix.
"""

import glob
import os
from src.simulator.simulation_engine import run_simulation


def main():
    scenarios = sorted(glob.glob("src/simulator/events/scenario_*.json"))
    if not scenarios:
        print("No scenarios found in src/simulator/events/")
        return

    print("=" * 95)
    print(f"RUNNING ALL {len(scenarios)} SIMULATOR SCENARIOS")
    print("=" * 95)

    results = []
    for sc in scenarios:
        sc_name = os.path.basename(sc).replace(".json", "")
        print(f"\n>> Executing: {sc_name} ...")
        obs = run_simulation(
            events_filepath=sc,
            config_filepath="src/simulator/config/simulator_config.json"
        )
        final = obs[-1]
        results.append({
            "name": sc_name,
            "observations": len(obs),
            "duration_min": final["simulation_time_sec"] / 60.0,
            "arrival_time": final["timestamp"],
            "delay_min": final["current_delay_min"],
            "status": "PASS" if obs[-1]["data_quality_status"] == "OK" else "FAIL"
        })

    print("\n" + "=" * 95)
    print("COMPLETE SIMULATOR TEST MATRIX (10 SCENARIOS)")
    print("=" * 95)
    print(f"{'Scenario File':<38} | {'Observations':<12} | {'Duration':<10} | {'Arrival':<8} | {'Delay':<8} | {'Gate'}")
    print("-" * 95)
    for r in results:
        print(
            f"{r['name']:<38} | "
            f"{r['observations']:>12} | "
            f"{r['duration_min']:>8.1f} m | "
            f"{r['arrival_time']:>8} | "
            f"{r['delay_min']:>6.1f} m | "
            f"{r['status']}"
        )
    print("=" * 95)


if __name__ == "__main__":
    main()
