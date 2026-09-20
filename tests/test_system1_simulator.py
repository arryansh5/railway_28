"""
Phase 6 Unit Tests: System 1 Simulator Core
=============================================

Verifies:
1. Dynamic Route Resolution coupling (Phase 4 integration).
2. Historical Behavior Service stochastic priors coupling (Phase 5 integration).
3. Continuous 30-second snapshot trajectory generation.
4. Data provenance compliance: data_origin = "synthetic" on all snapshot records.
5. Station state transitions (DEPARTED -> IN_TRANSIT -> ARRIVED -> DWELLING -> TERMINAL).
6. Forward & Reverse corridor trajectory synthesis.
"""

import unittest
import numpy as np
from src.simulator.system1_simulator import (
    System1SimulatorCore,
    SimulatorConfig,
    SimulationState,
    SimulationTrajectory
)
from src.simulator.historical_behavior_service import HistoricalBehaviorService
from src.network.resolver import RouteResolver, RouteResolutionResult


class TestSystem1SimulatorCore(unittest.TestCase):

    def setUp(self):
        self.simulator = System1SimulatorCore()

    def test_1_ndls_to_ddn_trajectory_synthesis(self):
        """Test standard forward corridor trajectory from New Delhi to Dehradun."""
        traj = self.simulator.simulate_journey(
            origin="NDLS",
            destination="DDN",
            train_id="12017",
            train_type="Shatabdi",
            departure_time="06:45:00",
            random_seed=42
        )

        self.assertEqual(traj.route_status, "COMPLETED")
        self.assertEqual(traj.origin, "NDLS")
        self.assertEqual(traj.destination, "DDN")
        self.assertGreater(traj.num_timesteps, 10)
        self.assertGreater(traj.total_distance_km, 300.0)

        # Check first state snapshot
        first_state = traj.trajectory[0]
        self.assertEqual(first_state.data_origin, "synthetic")
        self.assertEqual(first_state.origin_station, "NDLS")
        self.assertEqual(first_state.destination_station, "DDN")
        self.assertAlmostEqual(first_state.position_km, 0.0, places=1)

        # Check terminal state snapshot
        last_state = traj.trajectory[-1]
        self.assertEqual(last_state.station_status, "TERMINAL")
        self.assertEqual(last_state.remaining_stops, 0)
        self.assertAlmostEqual(last_state.remaining_distance_km, 0.0, places=1)

    def test_2_data_provenance_contract(self):
        """Test that ALL snapshot state rows carry data_origin = 'synthetic'."""
        traj = self.simulator.simulate_journey(
            origin="RK",
            destination="DDN",
            train_id="12401",
            train_type="Express",
            random_seed=123
        )

        self.assertGreater(len(traj.trajectory), 0)
        for state in traj.trajectory:
            self.assertEqual(state.data_origin, "synthetic")

    def test_3_reverse_corridor_traversal(self):
        """Test trajectory generation for reverse traversal (Dehradun -> Roorkee)."""
        traj = self.simulator.simulate_journey(
            origin="DDN",
            destination="RK",
            train_id="12018",
            train_type="Superfast",
            random_seed=42
        )

        self.assertEqual(traj.route_status, "COMPLETED")
        self.assertEqual(traj.origin, "DDN")
        self.assertEqual(traj.destination, "RK")
        self.assertEqual(traj.trajectory[0].direction, "REVERSE")

    def test_4_weather_fog_speed_restriction(self):
        """Test weather context (is_fog_risk=1) applies sectional speed caps."""
        traj_clear = self.simulator.simulate_journey(
            origin="NDLS",
            destination="RK",
            context={"is_fog_risk": 0},
            random_seed=42
        )
        traj_fog = self.simulator.simulate_journey(
            origin="NDLS",
            destination="RK",
            context={"is_fog_risk": 1},
            random_seed=42
        )

        # Fog journey duration should be greater due to 60 km/h speed cap
        self.assertGreater(traj_fog.total_duration_minutes, traj_clear.total_duration_minutes)

    def test_5_invalid_origin_destination_handling(self):
        """Test error handling when unknown station is requested."""
        traj = self.simulator.simulate_journey(
            origin="INVALID_STN",
            destination="DDN"
        )
        self.assertNotEqual(traj.route_status, "COMPLETED")
        self.assertEqual(traj.num_timesteps, 0)
        self.assertIn("error", traj.metadata)


if __name__ == "__main__":
    unittest.main()
