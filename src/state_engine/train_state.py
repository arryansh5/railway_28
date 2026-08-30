"""
TrainState Dataclass.
Represents the canonical real-time state of a train on a railway route.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class TrainState:
    """Canonical real-time train state snapshot."""
    train_id: str
    route_id: str
    timestamp: str

    # Position
    current_position_km: float
    current_section_id: Optional[str] = None
    current_station_id: Optional[str] = None
    previous_station_id: Optional[str] = None
    next_station_id: Optional[str] = None

    # Kinematics
    current_speed_kmph: float = 0.0
    movement_state: str = "STOPPED"

    # Distances
    distance_to_next_station_km: float = 0.0
    distance_to_destination_km: float = 0.0
    percent_journey_complete: float = 0.0

    # Delay Profile
    current_delay_min: float = 0.0
    delay_trend: str = "STABLE"  # "IMPROVING", "WORSENING", "STABLE"
    last_arrival_delay_min: Optional[float] = None
    last_departure_delay_min: Optional[float] = None

    # Journey Timeline & Events
    station_history: List[Dict[str, Any]] = field(default_factory=list)
    active_events: List[str] = field(default_factory=list)

    # GPS Coordinates
    latitude: float = 0.0
    longitude: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to a plain dictionary."""
        return asdict(self)
