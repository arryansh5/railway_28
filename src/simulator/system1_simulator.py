"""
SUPERNOVA — Phase 6: System 1 Simulator Core
=============================================

System 1 is the Journey & World Simulator for Supernova.
It generates statistically plausible, continuous 30-second synthetic railway
journey trajectories by coupling:
  1. Topological Network Graph & Route Resolver (Phase 4)
  2. Historical Behavioral Distributions & Stochastic Priors (Phase 5)
  3. Continuous Kinematic Acceleration/Braking Physics Engine
  4. Station Dwell & State Transition Discrete Event Machine

Outputs:
  - Synthetic Trajectory (Sequence of 30-second state dictionaries)
  - Provenance: Guaranteed data_origin = "synthetic" on all emission records
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
import math
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np

# Integration with Phase 4: Dynamic Route Resolver Engine
from src.network.resolver import RouteResolver, RouteResolutionResult

# Integration with Phase 5: Historical Behavior Engine
from src.simulator.historical_behavior_service import (
    HistoricalBehaviorService,
    BehaviorQueryResult,
    DelayDistributionParams
)


@dataclass
class SimulatorConfig:
    """Configuration settings for the System 1 Journey Simulator."""
    timestep_seconds: float = 30.0               # Raw simulation cadence (default 30s)
    max_acceleration_mps2: float = 0.5          # Standard acceleration (m/s^2)
    max_braking_deceleration_mps2: float = 0.8  # Service deceleration (m/s^2)
    default_max_speed_kmph: float = 110.0       # Max sectional speed limit (km/h)
    station_approach_speed_kmph: float = 30.0    # Speed limit on station approach (km/h)
    station_dwell_min_default: float = 2.0      # Default station dwell time (minutes)
    max_journey_hours: float = 24.0             # Safety cutoff for long runs (hours)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SimulationState:
    """State snapshot emitted at each 30-second simulation timestep."""
    step: int
    timestamp: str
    elapsed_seconds: float
    journey_id: str
    train_id: str
    train_type: str
    origin_station: str
    destination_station: str
    current_section_id: str
    current_station_code: str
    station_status: str                          # "IN_TRANSIT", "ARRIVED", "DWELLING", "DEPARTED", "TERMINAL"
    position_km: float
    speed_kmph: float
    delay_minutes: float
    direction: str
    remaining_distance_km: float
    remaining_stops: int
    context: Dict[str, Any]
    data_origin: str = "synthetic"              # Strict provenance contract tag

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SimulationTrajectory:
    """Container for the full trajectory output of a simulated journey."""
    journey_id: str
    train_id: str
    train_type: str
    origin: str
    destination: str
    total_distance_km: float
    total_duration_minutes: float
    terminal_delay_minutes: float
    num_timesteps: int
    route_status: str
    trajectory: List[SimulationState] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["trajectory"] = [st.to_dict() for st in self.trajectory]
        return res


class System1SimulatorCore:
    """
    System 1 — Journey / World Simulator Core.
    Orchestrates continuous kinematics and stochastic state transitions over resolved routes.
    """

    def __init__(
        self,
        config: Optional[SimulatorConfig] = None,
        behavior_service: Optional[HistoricalBehaviorService] = None,
        route_resolver: Optional[RouteResolver] = None,
        database_path: Optional[Union[str, Path]] = None
    ):
        self.config = config or SimulatorConfig()
        self.behavior_service = behavior_service or HistoricalBehaviorService()
        self.route_resolver = route_resolver or RouteResolver(data_dir=database_path or "Data")

    def simulate_journey(
        self,
        origin: str,
        destination: str,
        train_id: str = "12017",
        train_type: str = "Superfast",
        departure_time: str = "06:45:00",
        context: Optional[Dict[str, Any]] = None,
        random_seed: Optional[int] = None
    ) -> SimulationTrajectory:
        """
        Simulates a complete plausible railway journey from origin to destination.

        Parameters:
            origin: Station code/ID (e.g. 'NDLS')
            destination: Station code/ID (e.g. 'DDN')
            train_id: Service ID or Train Number
            train_type: Priority class ('Rajdhani', 'Shatabdi', 'Superfast', 'Express', 'Passenger')
            departure_time: HH:MM:SS format string or ISO timestamp
            context: Environmental/operational context (season, is_fog_risk, late_incoming_rake, etc.)
            random_seed: Optional seed for reproducible Monte Carlo simulation

        Returns:
            SimulationTrajectory with raw 30-second trajectory records.
        """
        rng = np.random.RandomState(random_seed) if random_seed is not None else np.random.RandomState()
        context = context or {}
        context.setdefault("train_type", train_type)

        # 1. Resolve Route dynamically using Phase 4 Dynamic Route Resolver
        route_res: RouteResolutionResult = self.route_resolver.resolve_route(
            origin=origin,
            destination=destination,
            train_number=train_id
        )

        if route_res.status != "RESOLVED":
            return SimulationTrajectory(
                journey_id=f"J_{train_id}_{origin}_{destination}",
                train_id=train_id,
                train_type=train_type,
                origin=origin,
                destination=destination,
                total_distance_km=0.0,
                total_duration_minutes=0.0,
                terminal_delay_minutes=0.0,
                num_timesteps=0,
                route_status=route_res.status,
                metadata={"error": route_res.error_message}
            )

        query_ctx = dict(context)
        query_ctx.setdefault("train_type", train_type)
        corridor_id = route_res.route_metadata.get("corridor_id")
        if corridor_id:
            query_ctx.setdefault("route_id", corridor_id)

        # 2. Query Phase 5 Historical Behavior Prior for initial delay & stochastic speed factor
        behavior_query = self.behavior_service.get_delay_distribution(**query_ctx)
        
        # Initial departure delay sampling
        initial_delay_min, _ = self.behavior_service.sample_delay(rng=rng, **query_ctx)

        # 3. Setup Journey Telemetry & Tracking Data
        journey_id = f"J_{train_id}_{origin}_{destination}_{int(rng.randint(1000, 9999))}"
        ordered_stations = route_res.ordered_stations
        ordered_sections = route_res.ordered_sections
        total_distance_km = route_res.total_distance_km

        # Build timetable offsets (assumes nominal 60 km/h average schedule speed if unspecified)
        scheduled_offsets_sec = self._build_scheduled_offsets(ordered_stations, total_distance_km)

        # Kinematic State Variables
        elapsed_sec = 0.0
        position_m = 0.0
        speed_mps = 0.0
        step = 1

        station_idx = 0
        section_idx = 0
        current_station = ordered_stations[0]
        next_station = ordered_stations[1] if len(ordered_stations) > 1 else current_station
        current_section = ordered_sections[0] if len(ordered_sections) > 0 else {}

        station_status = "DEPARTED" if initial_delay_min <= 0 else "DWELLING"
        dwell_remaining_sec = max(0.0, initial_delay_min * 60.0)

        dt = self.config.timestep_seconds
        max_accel = self.config.max_acceleration_mps2
        max_decel = self.config.max_braking_deceleration_mps2

        trajectory_records: List[SimulationState] = []
        max_elapsed_sec = self.config.max_journey_hours * 3600.0

        # Parse base time
        base_datetime = self._parse_base_datetime(departure_time)

        # 4. Simulation Execution Loop (30-second cadence)
        while elapsed_sec < max_elapsed_sec:
            current_time_str = (base_datetime + timedelta(seconds=elapsed_sec)).isoformat()
            pos_km = position_m / 1000.0
            rem_km = max(0.0, total_distance_km - pos_km)
            rem_stops = max(0, len(ordered_stations) - 1 - station_idx)

            # Scheduled offset for current progress
            sched_offset_sec = scheduled_offsets_sec.get(station_idx, elapsed_sec)
            delay_min = (elapsed_sec - sched_offset_sec) / 60.0

            # Record snapshot state (Provenance data_origin = "synthetic")
            state = SimulationState(
                step=step,
                timestamp=current_time_str,
                elapsed_seconds=round(elapsed_sec, 2),
                journey_id=journey_id,
                train_id=train_id,
                train_type=train_type,
                origin_station=origin,
                destination_station=destination,
                current_section_id=current_section.get("section_id", "SEC_IN_STATION"),
                current_station_code=current_station.get("station_code", origin),
                station_status=station_status,
                position_km=round(pos_km, 3),
                speed_kmph=round(speed_mps * 3.6, 2),
                delay_minutes=round(delay_min, 2),
                direction=route_res.direction,
                remaining_distance_km=round(rem_km, 3),
                remaining_stops=rem_stops,
                context=context,
                data_origin="synthetic"
            )
            trajectory_records.append(state)

            # Terminal Reached Check
            if station_idx >= len(ordered_stations) - 1 and position_m >= total_distance_km * 1000.0:
                station_status = "TERMINAL"
                break

            # 5. Physics & State Machine Update
            if station_status == "DWELLING":
                speed_mps = 0.0
                dwell_remaining_sec -= dt
                if dwell_remaining_sec <= 0.0:
                    station_status = "DEPARTED"
                    dwell_remaining_sec = 0.0
            else:
                # Target Sectional Speed (km/h -> m/s)
                sec_max_kmph = current_section.get("max_speed_kmph", self.config.default_max_speed_kmph)
                
                # Apply weather/fog speed restriction prior if active
                if context.get("is_fog_risk") == 1:
                    sec_max_kmph = min(sec_max_kmph, 60.0)

                target_speed_mps = (sec_max_kmph * 1000.0) / 3600.0

                # Check station approach deceleration
                next_stn_pos_m = next_station.get("distance_from_origin_km", total_distance_km) * 1000.0
                dist_to_next_stn_m = max(0.0, next_stn_pos_m - position_m)
                braking_dist_m = (speed_mps ** 2) / (2.0 * max_decel)

                if dist_to_next_stn_m <= braking_dist_m + 50.0:
                    # Decelerate for station arrival
                    target_speed_mps = 0.0

                # Kinematic Update (v_t+1 = v_t + a*dt, x_t+1 = x_t + v*dt)
                if speed_mps < target_speed_mps:
                    accel = min(max_accel, (target_speed_mps - speed_mps) / dt)
                    speed_mps = speed_mps + accel * dt
                elif speed_mps > target_speed_mps:
                    decel = min(max_decel, (speed_mps - target_speed_mps) / dt)
                    speed_mps = max(0.0, speed_mps - decel * dt)

                position_m += speed_mps * dt

                # Station Arrival Event Check
                if position_m >= next_stn_pos_m:
                    position_m = next_stn_pos_m
                    station_idx += 1
                    current_station = ordered_stations[station_idx]
                    
                    if station_idx < len(ordered_stations) - 1:
                        next_station = ordered_stations[station_idx + 1]
                        if section_idx < len(ordered_sections) - 1:
                            section_idx += 1
                            current_section = ordered_sections[section_idx]
                        
                        station_status = "DWELLING"
                        # Sample stochastic station dwell extension
                        base_dwell_min = self.config.station_dwell_min_default
                        excess_dwell_min = rng.exponential(scale=1.5) if rng.uniform() < 0.25 else 0.0
                        dwell_remaining_sec = (base_dwell_min + excess_dwell_min) * 60.0
                    else:
                        station_status = "TERMINAL"
                        state.station_status = "TERMINAL"
                        state.speed_kmph = 0.0
                        state.remaining_distance_km = 0.0
                        state.remaining_stops = 0
                        break

            elapsed_sec += dt
            step += 1

        total_duration_min = elapsed_sec / 60.0
        final_delay_min = trajectory_records[-1].delay_minutes if trajectory_records else 0.0

        return SimulationTrajectory(
            journey_id=journey_id,
            train_id=train_id,
            train_type=train_type,
            origin=origin,
            destination=destination,
            total_distance_km=total_distance_km,
            total_duration_minutes=round(total_duration_min, 2),
            terminal_delay_minutes=round(final_delay_min, 2),
            num_timesteps=len(trajectory_records),
            route_status="COMPLETED",
            trajectory=trajectory_records,
            metadata={
                "matched_behavior_level": behavior_query.matched_level,
                "behavior_data_origin": behavior_query.data_origin,
                "initial_delay_sampled_min": round(initial_delay_min, 2)
            }
        )

    def _build_scheduled_offsets(
        self,
        stations: List[Dict[str, Any]],
        total_dist_km: float
    ) -> Dict[int, float]:
        """Calculates nominal scheduled arrival time offsets (in seconds) for each station."""
        offsets = {}
        # Nominal commercial travel speed of 60 km/h (1 km per minute)
        for i, st in enumerate(stations):
            dist_km = st.get("distance_from_origin_km", 0.0)
            offsets[i] = (dist_km / 60.0) * 3600.0
        return offsets

    def _parse_base_datetime(self, time_str: str) -> datetime:
        """Parses ISO string or HH:MM:SS time string into datetime."""
        try:
            return datetime.fromisoformat(time_str)
        except ValueError:
            pass

        try:
            t = datetime.strptime(time_str, "%H:%M:%S").time()
            now = datetime.now()
            return datetime.combine(now.date(), t)
        except ValueError:
            return datetime.now()
