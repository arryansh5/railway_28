"""
Prediction Data Schemas.
Defines StationETA and ETAPrediction dataclasses for output standardization.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class StationETA:
    """Predicted arrival and departure details for an individual station."""
    station_id: str
    station_name: str
    sequence: int
    distance_from_origin_km: float
    scheduled_arrival_time: str
    scheduled_departure_time: str
    predicted_arrival_time: str
    predicted_departure_time: str
    predicted_arrival_offset_min: float
    predicted_delay_min: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ETAPrediction:
    """Full route-level ETA prediction forecast."""
    train_id: str
    route_id: str
    model_name: str  # "SCHEDULED", "SCHEDULE_PLUS_DELAY", "SECTION_RUNNING_TIME"
    prediction_timestamp: str
    current_delay_min: float
    current_position_km: float
    upcoming_stations: List[StationETA] = field(default_factory=list)
    destination_eta: Optional[StationETA] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
