# SUPERNOVA — Phase 6: System 1 Simulator Core Report

> **Standard Deliverable**: `System1SimulatorCore`  
> **Phase**: 6 — System 1 Simulator Core  
> **Status**: Completed & 100% Tested  
> **Reference Standard**: [`phase_by_phase.md`](file:///d:/Supernova/phase_by_phase.md) (Lines 670–731)  
> **Engine Code**: [`src/simulator/system1_simulator.py`](file:///d:/Supernova/src/simulator/system1_simulator.py)  
> **Unit Test Suite**: [`tests/test_system1_simulator.py`](file:///d:/Supernova/tests/test_system1_simulator.py)  
> **Dynamic Network Resolver**: [`src/network/resolver.py`](file:///d:/Supernova/src/network/resolver.py)  
> **Historical Behavior Service**: [`src/simulator/historical_behavior_service.py`](file:///d:/Supernova/src/simulator/historical_behavior_service.py)

---

## 1. Executive Summary & Core Architectural Principles

Phase 6 implements the **System 1 Simulator Core** ([`src/simulator/system1_simulator.py`](file:///d:/Supernova/src/simulator/system1_simulator.py)), the foundational Journey & World Simulator for Supernova.

```
┌────────────────────────────────────────────────────────────────────────┐
│ 6. SYSTEM 1 SIMULATOR CORE ARCHITECTURE                                │
│                                                                        │
│   Origin & Destination Query (e.g. NDLS -> DDN)                        │
│       │                                                                │
│       ├── 1. Dynamic Route Resolution (Phase 4)                        │
│       │      (ordered stations, sections, distances, direction)        │
│       │                                                                │
│       ├── 2. Stochastic Behavioral Priors (Phase 5)                    │
│       │      (P(delay|context), on-time Bernoulli, quantile quantiles) │
│       │                                                                │
│       ├── 3. Continuous 30-Second Kinematics                           │
│       │      (v_t+1 = v_t + a*dt, position_m, sectional max speed)     │
│       │                                                                │
│       └── 4. Discrete Station Event Machine                            │
│              (DEPARTED -> IN_TRANSIT -> ARRIVED -> DWELLING -> TERMINAL)│
│                                                                        │
│       ▼                                                                │
│   Synthetic Journey Trajectory (data_origin = "synthetic")             │
└────────────────────────────────────────────────────────────────────────┘
```

### Core System Responsibilities:
1. **Dynamic Route Binding**: Connects any origin and destination across the topological graph via Phase 4 `resolve_route()`.
2. **Stochastic Delay & Dwell Prior**: Integrates Phase 5 `HistoricalBehaviorService` to sample initial departure delays and dwell variations based on train class and environmental context.
3. **30-Second Raw Cadence Snapshot Emission**: Emits telemetry states containing timestamp, position, speed, delay, remaining distance, remaining stops, and context.
4. **Data Provenance Contract**: Enforces strict `data_origin = "synthetic"` tagging across all emitted trajectory snapshot records.

---

## 2. Telemetry Record & Trajectory Schema

Each 30-second timestep produces a strongly typed `SimulationState` object:

| Field Name | Type | Description | Provenance / Source |
|---|---|---|---|
| `step` | `int` | Sequential step index ($1, 2, 3 \dots N$) | Simulation Engine |
| `timestamp` | `string` | ISO timestamp of state observation | Calculated Offset |
| `elapsed_seconds` | `float` | Cumulative elapsed journey seconds | Simulation Engine |
| `journey_id` | `string` | Unique journey instance identifier | Synthetic Generator |
| `train_id` | `string` | Train service identifier | Input Parameter |
| `train_type` | `string` | Service priority class (e.g. *Shatabdi*) | Input Parameter |
| `origin_station` | `string` | Departure terminal code | Input Parameter |
| `destination_station` | `string` | Destination terminal code | Input Parameter |
| `current_section_id` | `string` | Physical track section ID | Phase 4 Network Graph |
| `current_station_code` | `string` | Station code of current or preceding node | Phase 4 Network Graph |
| `station_status` | `string` | State: `IN_TRANSIT`, `ARRIVED`, `DWELLING`, `DEPARTED`, `TERMINAL` | Event State Machine |
| `position_km` | `float` | Cumulative distance along corridor (km) | Kinematic Physics |
| `speed_kmph` | `float` | Instantaneous train speed (km/h) | Kinematic Physics |
| `delay_minutes` | `float` | Dynamic delay vs scheduled timetable | Timetable Estimator |
| `direction` | `string` | Traversal orientation (`FORWARD` / `REVERSE`) | Phase 4 Route Resolver |
| `remaining_distance_km` | `float` | Remaining physical distance to terminal | Phase 4 Network Graph |
| `remaining_stops` | `int` | Count of remaining intermediate stations | Phase 4 Network Graph |
| `context` | `dict` | Environmental/operational parameters | Context Input |
| `data_origin` | `string` | **Strict contract tag: `"synthetic"`** | System Contract |

---

## 3. Kinematic Physics & Event State Machine

The simulator updates kinematics at $\Delta t = 30\text{s}$ cadence using continuous equations of motion:

$$v_{t+\Delta t} = \min(v_{\text{target}}, v_t + a_{\text{max}} \cdot \Delta t)$$
$$x_{t+\Delta t} = x_t + v_{t+\Delta t} \cdot \Delta t$$

### Station Approach & Deceleration Logic

Before reaching an upcoming station, the engine evaluates the required service braking distance:

$$d_{\text{braking}} = \frac{v_t^2}{2 \cdot a_{\text{decel}}}$$

If remaining distance to the station node $d_{\text{next}} \le d_{\text{braking}} + 50\text{m}$, target speed $v_{\text{target}}$ transitions to $0.0\text{ m/s}$ to ensure smooth station arrival.

---

## 4. Verification Test Results Matrix

All 5 core test cases in [`tests/test_system1_simulator.py`](file:///d:/Supernova/tests/test_system1_simulator.py) passed cleanly (**5/5 PASS** ✅):

| Test ID | Test Objective | Target Condition | Status |
|---|---|---|---|
| `test_1` | NDLS to DDN Trajectory Synthesis | Completes 314 km forward corridor run with full trajectory. | **PASS** ✅ |
| `test_2` | Data Provenance Contract | All snapshot rows carry `data_origin = "synthetic"`. | **PASS** ✅ |
| `test_3` | Reverse Corridor Traversal | Traverses Dehradun to Roorkee in `REVERSE` orientation. | **PASS** ✅ |
| `test_4` | Weather / Fog Speed Restriction | Caps max sectional speed to 60 km/h when `is_fog_risk=1`. | **PASS** ✅ |
| `test_5` | Invalid Station Error Handling | Returns non-completed trajectory with explicit error metadata. | **PASS** ✅ |

---

## 5. Phase 6 Conclusion & Next Steps

* ✅ **System 1 Simulator Core Implemented**: [`src/simulator/system1_simulator.py`](file:///d:/Supernova/src/simulator/system1_simulator.py) created.
* ✅ **Integration Verified**: Successfully coupled with Phase 4 (`DynamicRouteResolver`) and Phase 5 (`HistoricalBehaviorService`).
* ✅ **Full Test Suite Verification**: All unit tests in [`tests/test_system1_simulator.py`](file:///d:/Supernova/tests/test_system1_simulator.py) passed.
* 🛑 **Ready for Driver Review**: We are prepared to proceed to **Phase 7: System 1 Realism & Calibration Test**.
