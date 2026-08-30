# Railway ETA Prediction System — Team Handoff Document

**Project**: Indian Railways Train Delay Prediction (MVP)
**Route**: New Delhi (NDLS) → Dehradun (DDN) — Pilot Corridor
**Workspace**: `d:\Projects\railway\`
**Handoff Point**: Phase 3 partially complete → Phase 4 to be started

---

## 1. Project Overview

We are building an end-to-end **Train ETA Prediction System** for Indian Railways.
The system is fully synthetic — no real RTIS API access. All train movement data is simulated.

### 15-Phase Roadmap

| Phase | Description | Status |
|---|---|---|
| 1 | Route & Data Foundation (Delhi–Dehradun route JSON) | ✅ Done |
| 2 | Data Validation Gate (23 schema & consistency checks) | ✅ Done |
| 3 | RTIS-Like Data Simulator (Physics-based, 30s updates) | 🔄 In Progress |
| 4 | Train State Engine | ⬅ Your Phase |
| 5 | Baseline ETA Engine (schedule + delay math) | Upcoming |
| 6 | Historical/Synthetic Dataset Generator | Upcoming |
| 7 | Feature Engineering | Upcoming |
| 8 | ML ETA Model (XGBoost) | Upcoming |
| 9–15 | Evaluation, API, Dashboard, Disruption Sim, Integration | Future |

---

## 2. What Has Been Built (Completed Work)

### Phase 1 — Route JSON
**File**: `d:\Projects\railway\Data\routes\delhi_dehradun_route.json`

Route structure (do NOT modify the schema):
- `route_id`: `"ROUTE_NDLS_DDN_01"`
- `total_distance_km`: `314.0`
- `total_scheduled_duration_min`: `337`
- `origin_station_id`: `"NDLS"`, `destination_station_id`: `"DDN"`
- `stations`: 8 stations in sequence (NDLS → GZB → MTC → MOZ → SRE → RK → HW → DDN)
  - Each station has: `station_id`, `station_name`, `latitude`, `longitude`, `sequence`, `distance_from_origin_km`, `scheduled_arrival_offset_min`, `scheduled_departure_offset_min`, `scheduled_dwell_min`, `is_origin`, `is_terminal`, `previous_station_id`, `next_station_id`
- `sections`: 7 sections in sequence (`SEC_NDLS_GZB` through `SEC_HW_DDN`)
  - Each section has: `section_id`, `from_station_id`, `to_station_id`, `distance_km`, `max_sectional_speed_kmph`, `scheduled_running_time_min`, `track_type`, `sequence`

### Phase 2 — Route Validation
**File**: `d:\Projects\railway\src\routes\validate_route.py`

23 validation checks across 3 functions:
- `validate_route_metadata(route)` — 7 checks (null fields, station/section list integrity, origin/destination sync)
- `validate_stations(stations)` — 9 checks (uniqueness, sequence gaps, origin/terminal counts, distance monotonicity, dwell times, linked-list integrity)
- `validate_sections(sections, stations)` — 6 checks (station refs exist, section connectivity, distance vs station distances, sum of sections == total route)

Run validation:
```bash
python -u -m src.routes.validate_route
```
Expected: All 23 checks pass, exit code 0.

### Phase 3 (Old Prototype) — Simple Simulator
**File**: `d:\Projects\railway\src\simulator\train_simulator.py`

This is the **OLD prototype**. It was a simple speed-based simulator without proper physics.
It has been superseded by the new physics-based simulator architecture below.
**Do NOT extend this file.** It is kept for reference only.

It did generate:
- `d:\Projects\railway\Data\simulations\journey_01_30s.json` (491 observations)
- `d:\Projects\railway\Data\simulations\journey_01_30s.csv` (491 rows)

### Phase 3 (New Architecture — In Progress) — Physics-Based Simulator

The new simulator follows a modular architecture. The following files have been created:

#### Configuration (Complete)
**File**: `d:\Projects\railway\src\simulator\config\simulator_config.json`
```json
{
    "simulation_timestep_seconds": 30.0,
    "random_seed": 42,
    "physics": {
        "max_acceleration_mps2": 0.5,
        "max_braking_deceleration_mps2": 0.6,
        "braking_safety_margin_m": 150.0,
        "station_stop_tolerance_m": 10.0,
        "cruising_speed_factor": 0.95
    },
    "signal_speed_mapping_kmph": { "GREEN": 999.0, "YELLOW": 45.0, "RED": 0.0 },
    "congestion_speed_mapping_kmph": { "LOW": 999.0, "MEDIUM": 60.0, "HIGH": 25.0 },
    "fog_speed_mapping_kmph": { "DEFAULT_FOG_RESTRICTION": 40.0 },
    "output": {
        "csv_filepath": "Data/simulations/simulation_output.csv",
        "json_filepath": "Data/simulations/simulation_output.json"
    }
}
```

#### Event Scenarios (Complete — 10 Scenarios)
**Folder**: `d:\Projects\railway\src\simulator\events\`

10 test scenario files:
| File | Scenario |
|---|---|
| `scenario_01_normal.json` | Zero disruptions (baseline) |
| `scenario_02_speed_restriction.json` | TSR 50 km/h |
| `scenario_03_signal_events.json` | RED + YELLOW signals |
| `scenario_04_fog_and_halt.json` | Fog + unscheduled halt |
| `scenario_05_heavy_disruption.json` | All event types combined |
| `scenario_06_station_dwell_test.json` | Station braking/dwell lifecycle |
| `scenario_07_origin_delay.json` | RED at origin (delay propagation) |
| `scenario_08_double_red_signal.json` | Back-to-back RED signals |
| `scenario_09_congestion_cascade.json` | HIGH → MEDIUM → LOW congestion |
| `scenario_10_hill_worst_case.json` | Hill section fog + halt + congestion |

Each event file uses this schema:
```json
{
    "event_id": "EVT_001",
    "event_type": "SPEED_RESTRICTION | SIGNAL_CHANGE | UNSCHEDULED_HALT | FOG | CONGESTION",
    "route_id": "ROUTE_NDLS_DDN_01",
    "section_id": "SEC_GZB_MTC",
    "position_km": 45.0,
    "start_time": "07:15:00",
    "end_time": "07:45:00",
    "signal_state": null,
    "restriction_speed_kmph": 50.0,
    "halt_duration_min": null,
    "fog_visibility_km": null,
    "congestion_level": null,
    "severity": "MEDIUM",
    "enabled": true,
    "description": "..."
}
```

---

## 3. Phase 3 Remaining Work (Your Task — Simulator Completion)

Build these modules inside `d:\Projects\railway\src\simulator\`:

### 3.1 Required File Structure to Build
```
src/simulator/
├── __init__.py
├── simulation_engine.py          ← Main 30s loop coordinator
├── config/
│   └── simulator_config.json    ✅ Done
├── route/
│   └── route_loader.py          ← Loads route JSON, returns typed structure
├── events/
│   ├── scenario_XX.json         ✅ Done (10 scenarios)
│   └── event_manager.py         ← Evaluates active events at timestamp & position
├── train/
│   └── train_state.py           ← Internal physics state dataclass
├── physics/
│   ├── speed_controller.py      ← Computes V_target = min(...all speed caps...)
│   └── physics_engine.py        ← v_new, d_new, d_brake calculations
├── geo/
│   └── coordinate_interpolator.py ← Lat/lon interpolation between stations
├── output/
│   ├── observation_generator.py ← Formats RTIS live-state JSON dict
│   └── csv_writer.py            ← Appends every 30s row to CSV
└── validation/
    └── observation_validator.py ← 17-point validation before passing downstream
```

### 3.2 Physics Rules (Non-Negotiable)

**Speed update (SI units — m/s internally):**
```
v_new = max(0.0, v_old + a * Δt)
```

**Position update:**
```
d_new = d_old + v_old * Δt + 0.5 * a * (Δt)^2
```

**Braking distance:**
```
d_brake = v² / (2 * a_brake)
```

**Target speed (NEVER set speed directly):**
```
V_target = min(V_section, V_restriction, V_signal, V_approach, V_weather, V_congestion)
```

**Movement states:**
`ACCELERATING`, `CRUISING`, `DECELERATING`, `STOPPED`, `DWELLING`, `DEPARTING`, `COMPLETED`

### 3.3 Event Activation Rule
An event is active when ALL of:
- `enabled == true`
- `current_simulation_time >= start_time`
- `current_simulation_time <= end_time`
- `section_id` matches current section OR `position_km` is within the train's current position range

### 3.4 GPS Coordinate Interpolation
Stations have `latitude` and `longitude`. Between stations:
```python
fraction = (current_km - from_station_km) / section_distance_km
lat = from_lat + fraction * (to_lat - from_lat)
lon = from_lon + fraction * (to_lon - from_lon)
```
Label all coordinates as `data_source: "SYNTHETIC_SIMULATOR"`.

### 3.5 Required CSV Output Columns
```
observation_id, timestamp, train_id, route_id,
latitude, longitude,
current_speed_kmph, current_speed_mps, current_position_km,
current_section_id, current_station_id, previous_station_id, next_station_id,
distance_to_next_station_km, distance_to_destination_km,
target_speed_kmph, section_speed_limit_kmph, restriction_speed_kmph,
signal_state, approach_speed_kmph, acceleration_mps2, braking_distance_m,
movement_state, station_event,
actual_arrival_time, actual_departure_time, actual_dwell_min,
arrival_delay_min, departure_delay_min, current_delay_min,
congestion_level, fog_active, fog_visibility_km,
active_event_ids, data_quality_status
```

### 3.6 Observation Validator (17 Rules)
1. Required fields exist
2. `observation_id` is unique
3. Timestamp increases monotonically
4. `speed >= 0`
5. `distance >= 0`
6. Position does not move backward
7. Current section exists in route
8. Station relationships are valid
9. `next_station_id` is null only at terminal
10. `previous_station_id` is null only at origin
11. Exactly one origin and terminal exist in route
12. Arrival occurs before departure at any station
13. Dwell time is consistent with arrival/departure delta
14. Train cannot be simultaneously MOVING and STOPPED
15. Speed does not exceed active target constraints (beyond tolerance)
16. `latitude`/`longitude` are valid numeric coordinates (not null, not 0,0)
17. Destination completion state is valid

### 3.7 Important Design Rule
**Never write:**
```python
if section_id == "SEC_GZB_MTC":  # ← WRONG, hardcoded
```
**Always write:**
```python
for event in active_events:      # ← CORRECT, data-driven
    if event["event_type"] == "SPEED_RESTRICTION":
        v_restriction = event["restriction_speed_kmph"]
```

---

## 4. Phase 4 — Train State Engine (Start Here If Simulator Delegated)

### Purpose
Consumes raw 30s observations (from Phase 3 simulator CSV/JSON) one by one.
Maintains a **canonical, clean, real-time train state** that downstream components (ETA engine, dashboard) can query at any moment.

### What it maintains
```python
@dataclass
class TrainState:
    train_id: str
    route_id: str
    timestamp: str

    # Position
    current_position_km: float
    current_section_id: str
    current_station_id: Optional[str]   # None when moving between stations
    previous_station_id: str
    next_station_id: str

    # Kinematics
    current_speed_kmph: float
    movement_state: str

    # Distances
    distance_to_next_station_km: float
    distance_to_destination_km: float
    percent_journey_complete: float

    # Delay Profile
    current_delay_min: float
    delay_trend: str           # "IMPROVING", "WORSENING", "STABLE"
    last_arrival_delay_min: Optional[float]
    last_departure_delay_min: Optional[float]

    # Journey Timeline
    station_history: List[dict]    # Actual arrival/departure times per station visited
    active_events: List[str]

    # GPS
    latitude: float
    longitude: float
```

### Architecture
```
src/state_engine/
├── __init__.py
├── train_state.py       ← TrainState dataclass
└── state_engine.py      ← StateEngine class: ingest(observation) → updates TrainState
```

### StateEngine Core Method
```python
class StateEngine:
    def __init__(self, route: dict):
        self.state = None          # Initialized on first observation
        self.route = route
        self.station_lookup = {s["station_id"]: s for s in route["stations"]}

    def ingest(self, observation: dict) -> TrainState:
        """
        Consumes one 30s observation dict.
        Updates internal TrainState.
        Returns updated TrainState.
        """
        # 1. Update position, speed, section
        # 2. Update station context (arriving / departing / moving)
        # 3. Record actual arrival/departure timestamps
        # 4. Compute delay against schedule
        # 5. Calculate delay trend (compare last 3 delay values)
        # 6. Update station_history if a station event occurred
        # 7. Update distance metrics
        # 8. Return new state snapshot
```

### Delay Trend Logic
```python
# If last 3 delays are: -5, -3, -1 → trend = "WORSENING" (becoming less early)
# If last 3 delays are: 5, 3, 1   → trend = "IMPROVING" (recovering)
# If delta < 0.5 min change       → trend = "STABLE"
```

### Verification Test
Run StateEngine on `journey_01_30s.json` (491 observations) and verify:
- First state: position `0.0 km`, section `None`, station `NDLS`
- After 491 ingestions: position `314.0 km`, station `DDN`, `movement_state = COMPLETED`
- `station_history` contains 8 entries (one per station)
- `percent_journey_complete = 100.0`

---

## 5. Key Files Reference

| File | Purpose |
|---|---|
| `Data/routes/delhi_dehradun_route.json` | Source of truth for route structure |
| `src/routes/validate_route.py` | 23 validation checks for route integrity |
| `src/simulator/config/simulator_config.json` | Physics config (do not hardcode values) |
| `src/simulator/events/scenario_XX.json` | 10 test event scenarios |
| `src/simulator/train_simulator.py` | OLD prototype (reference only, do not extend) |
| `Data/simulations/journey_01_30s.csv` | 491-row sample simulation output |
| `Data/simulations/journey_01_30s.json` | 491-observation sample simulation output |

---

## 6. Running Existing Code

```bash
# From workspace root: d:\Projects\railway

# Run route validation (should exit 0 with 23 checks)
python -u -m src.routes.validate_route

# (OLD) Run prototype simulator
python -u -m src.simulator.train_simulator
```

---

## 7. Conventions & Rules

1. **Never hardcode station or section names** in Python logic. Always read from route JSON.
2. **Physics in SI units** (m, m/s, m/s²) internally. Convert to km/h, km for output.
3. **Speed never set directly** — always computed via V_target and approached via acceleration.
4. **Random seed = 42** for deterministic reproducibility.
5. **All simulation data is synthetic** — label with `"data_source": "SYNTHETIC_SIMULATOR"`.
6. **Validate every observation** before passing downstream.
7. **Delay can be negative** (train running early) — do NOT clamp to 0.
