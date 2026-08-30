"""
train_state.py — Phase 3: Physics-Based RTIS Simulator
Internal state of the train at any given simulation tick.
Pure data container — no physics logic here.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TrainState:
    # --- Identity ---
    train_id: str
    route_id: str

    # --- Simulation Clock ---
    simulation_time_sec: float      # Elapsed seconds from start of journey
    timestamp: str                  # Formatted HH:MM:SS clock time

    # --- Position (in km along route) ---
    current_position_km: float
    current_position_m: float       # Same position in metres (used by physics engine internally)

    # --- Speed & Acceleration (SI units internally) ---
    current_speed_mps: float        # m/s
    current_speed_kmph: float       # km/h (for output)
    target_speed_kmph: float        # What speed the controller is aiming for
    current_acceleration_mps2: float

    # --- Section & Station Context ---
    current_section_id: Optional[str]   # None when stopped at origin/terminal
    current_station_id: Optional[str]   # Non-null only when at a platform
    previous_station_id: Optional[str]  # Last station the train passed through
    next_station_id: Optional[str]      # Next upcoming station (null at terminal)

    # --- Distances ---
    distance_to_next_station_km: float
    distance_to_destination_km: float
    braking_distance_m: float           # Computed braking distance at current speed

    # --- Movement State ---
    movement_state: str                 # ACCELERATING | CRUISING | DECELERATING | STOPPED | DWELLING | DEPARTING | COMPLETED

    # --- Station Events ---
    station_event: Optional[str]        # ARRIVED | DEPARTED | None
    actual_arrival_time: Optional[str]  # Set when train arrives at a station
    actual_departure_time: Optional[str]
    actual_dwell_min: Optional[float]

    # --- Delay ---
    current_delay_min: float
    arrival_delay_min: Optional[float]
    departure_delay_min: Optional[float]

    # --- Active Events ---
    signal_state: Optional[str]         # GREEN | YELLOW | RED | None
    speed_restriction_kmph: Optional[float]
    congestion_level: Optional[str]     # LOW | MEDIUM | HIGH | None
    fog_active: bool
    fog_visibility_km: Optional[float]
    unscheduled_halt: bool
    active_event_ids: list = field(default_factory=list)

    # --- GPS (Synthetic interpolated coordinates) ---
    latitude: float = 0.0
    longitude: float = 0.0

    # --- Data Quality ---
    data_quality_status: str = "OK"
