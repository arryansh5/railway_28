# Phase 6: Historical Calibration & 30-Second Closed-Loop Orchestration — Comprehensive Guide

---

## 1. Executive Summary & Objective

**Phase 6** is the operational bridge between **1M+ historical Indian Railways records** and the **real-time physics-based RTIS simulation** on the **New Delhi (NDLS) → Dehradun (DDN)** corridor (314 km).

### Core Goals:
1. **Empirical Data Foundation**: Eliminate guesswork, arbitrary multipliers, and hardcoded probabilities by mining exact frequentist priors ($N, P(\text{risk}), \text{reliability}$) from historical records.
2. **3-System Closed Loop**: Establish a strict 30-second feedback loop:
   $$\text{System 1 (Physics State at } t) \longrightarrow \text{System 2 (Risk Prediction)} \longrightarrow \text{System 3 (Restriction Decision)} \longrightarrow \text{System 1 (Kinematics } \Delta t = 30\text{s})$$
3. **ML-Ready Synthetic Telemetry**: Generate high-fidelity 51-column datasets with **guaranteed zero future data leakage** and post-simulation target label back-population.

```
       1M+ Indian Railways Records (ir_train.csv)
                          │
                          ▼
            STEP 1 — Dataset Factor Audit
           (reports/dataset_audit_report.json)
                          │
                          ▼
        STEP 2 — Empirical Pattern Mining
        (reports/historical_pattern_analysis.json)
                          │
                          ▼
        STEP 3 — Historical Calibration Layer
         (config/historical_calibration.json)
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│             30-SECOND CLOSED-LOOP ARCHITECTURE              │
│                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐ │
│  │   SYSTEM 1   │────►│   SYSTEM 2   │────►│   SYSTEM 3   │ │
│  │ Physics State│     │Risk Predictor│     │Decision Engine││
│  │ (Kinematics) │◄────│ (Risk Only)  │     │(Restrictions)│ │
│  └──────────────┘     └──────────────┘     └──────────────┘ │
│         ▲                                         │         │
│         └─────────── 30s Kinematic Step ──────────┘         │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
        STEP 6 — Multi-Journey Dataset Generator
          • Data/synthetic_rtis/synthetic_journey_01.csv
          • Data/synthetic_rtis/synthetic_journey_01.json
          • Data/ml/ml_ready_dataset.csv
```

---

## 2. Six-Step Phase Pipeline Breakdown

### Step 1: Dataset Factor Audit
- **Purpose**: Audited all 45 columns across 1,043,531 records in `ir_train.csv` for data types, missing values, duplicates, and physical ranges.
- **Classification Matrix**:
  - `USE DIRECTLY`: Features available in real-time at timestamp $t$ (position, speed, delay, section, hour, weather observation).
  - `USE AS CALIBRATION`: Historical priors ($P(\text{fog} \mid s, h)$, $P(\text{congestion} \mid h)$, delay cause distributions).
  - `DO NOT USE`: Static/irrelevant attributes (`is_circular_route`, `traction_type`, `coach_age_years`).
  - `FUTURE / LEAKAGE`: Ground-truth outcomes forbidden from live simulation inputs (`delay_minutes`, `target_eta`).
- **Artifacts**: [`reports/dataset_audit_report.json`](file:///d:/Projects/railway/reports/dataset_audit_report.json), [`reports/factor_audit_summary.md`](file:///d:/Projects/railway/reports/factor_audit_summary.md).

---

### Step 2: Empirical Pattern Mining
- **Purpose**: Discovered *when, where, and under what conditions* disruptions occur using pure empirical counting ($P(A \mid B) = \frac{\text{Count}(A \land B)}{\text{Count}(B)}$) with zero artificial multipliers.
- **Key Empirical Discoveries ($N=130,233$ Northern Railway NR/NCR records)**:
  1. **Winter Fog Timing**: Concentrated between **00:00 (Midnight) and 09:00 AM** ($N=12,234$, $100\%$ fog rate). Drops to **0.0%** at 10:00 AM ($N=18,803$ daytime records).
  2. **Active Congestion Rate**: True operational track congestion delay rate is **$16.14\% - 20.93\%$** (peaking at $\sim 25\% - 35\%$ during commute peaks), NOT 100%.
  3. **Baseline Delay**: Clean baseline (on-time incoming rake, no fog, normal capacity) has a mean delay of **$58.63\text{ min}$** ($45.41\%$ delay rate). Late incoming rakes jump delay to **$130.39\text{ min}$** ($87.04\%$ delay rate).
- **Artifacts**: [`reports/historical_pattern_analysis.json`](file:///d:/Projects/railway/reports/historical_pattern_analysis.json), [`reports/historical_pattern_summary.md`](file:///d:/Projects/railway/reports/historical_pattern_summary.md).

---

### Step 3: Historical Calibration Layer
- **Purpose**: Converted mined patterns into a high-performance in-memory lookup configuration (`config/historical_calibration.json`, ~62 KB).
- **Hierarchical Lookup & Reliability Tiers**:
  $$\text{Level 1: Zone} \times \text{Season} \times \text{Hour} \xrightarrow{N < 30} \text{Level 2: National} \times \text{Season} \times \text{Hour} \xrightarrow{N < 30} \text{Level 3: Global Baseline}$$
  - **HIGH**: $N \ge 1000$ (Weight: $1.00$)
  - **MEDIUM**: $100 \le N < 1000$ (Weight: $0.75$)
  - **LOW**: $30 \le N < 100$ (Weight: $0.40$)
  - **INSUFFICIENT**: $N < 30$ (Weight: $0.10$)
- **Artifacts**: [`config/historical_calibration.json`](file:///d:/Projects/railway/config/historical_calibration.json), [`src/data_generator/calibration_builder.py`](file:///d:/Projects/railway/src/data_generator/calibration_builder.py).

---

### Step 4: System 2 Predictive Engine
- **Engine**: `BaselinePredictiveEngine` implementing the abstract `BasePredictor` interface.
- **Strict Rule**: **Predicts RISK ONLY** in $[0.0, 1.0]$. It contains **zero speed limits ($40\text{ km/h}$), zero physical restrictions, and zero kinematics**.
- **Output Schema (`ConditionPrediction`)**:
  ```python
  {
      "prediction_timestamp": "06:45:00",
      "fog_risk": 1.0,               # Empirical probability
      "congestion_risk": 0.2093,     # Empirical probability
      "operational_risk": 0.4541,    # Disruption probability
      "delay_risk": 1.0,             # Overall destination delay probability
      "confidence": 1.0,             # Evidence strength based on sample size N
      "expected_speed_impact": "MEDIUM",
      "predicted_condition_summary": "MODERATE CONGESTION / FOG RISK",
      "evidence": {
          "fog_evidence": {"probability": 1.0, "sample_count": 1915, "source_level": "NR_NCR_hour_season"},
          "congestion_evidence": {"probability": 0.2093, "source_level": "NR_NCR_hour_congestion_cause"}
      }
  }
  ```
- **Artifacts**: [`src/data_generator/prediction_engine.py`](file:///d:/Projects/railway/src/data_generator/prediction_engine.py), [`tests/test_system2_prediction_engine.py`](file:///d:/Projects/railway/tests/test_system2_prediction_engine.py).

---

### Step 5: System 2 → System 3 Dynamic Integration
- **Engine**: `RestrictionEngine` acting as the dynamic decision state machine.
- **Responsibilities**:
  1. Evaluates System 2 risk against calibrated thresholds (`HIGH_CONGESTION` $\ge 0.70 \rightarrow 25\text{ km/h}$, `MEDIUM_CONGESTION` $\ge 0.45 \rightarrow 60\text{ km/h}$, `FOG` $\ge 0.40 \rightarrow 40\text{ km/h}$).
  2. **Lifecycle Management**: `ACTIVE` $\rightarrow$ `UPDATED` (escalation) $\rightarrow$ `DOWNGRADED` (easing) $\rightarrow$ `EXPIRED` (cleared).
  3. **Anti-Duplicate Guarantee**: Updates existing active restrictions in place (`PRED_CONG_01`, `PRED_FOG_01`) rather than generating new event IDs every 30 seconds.
  4. **Multi-Risk Prioritization**: Resolves effective constraint as $\min(\text{constraints})$ (e.g. $\min(40, 25) = 25\text{ km/h}$).
  5. **Stale Prediction Protection**: Rejects out-of-order predictions.
- **Artifacts**: [`src/data_generator/restriction_engine.py`](file:///d:/Projects/railway/src/data_generator/restriction_engine.py), [`tests/test_system2_system3_integration.py`](file:///d:/Projects/railway/tests/test_system2_system3_integration.py).

---

### Step 6: 30-Second Closed-Loop Orchestrator
- **Engine**: `dataset_builder.py` orchestrating System 1, System 2, and System 3.
- **Execution Lifecycle**:
  1. Read System 1 state at $t$.
  2. System 2 predicts risk from safe features at $t$.
  3. System 3 evaluates risk and updates restrictions.
  4. System 1 resolves effective target speed ($V_{\text{target}} = \min(V_{\text{section}}, V_{\text{signal}}, V_{\text{synthetic}})$) and integrates 30 seconds of physical kinematics.
  5. Re-compute dynamic ETA and interpolate continuous GPS coordinates.
  6. Log observation record.
  7. Loop until terminal arrival (DDN, 314 km).
  8. **Post-Simulation**: Back-populate ground truth target labels (`target_eta_to_destination_min`, `target_eta_to_next_station_min`).
- **Artifacts**: [`src/data_generator/dataset_builder.py`](file:///d:/Projects/railway/src/data_generator/dataset_builder.py), [`tests/test_closed_loop_orchestrator.py`](file:///d:/Projects/railway/tests/test_closed_loop_orchestrator.py).

---

## 3. Strict 3-System Separation of Concerns

| System | Role | Consumes | Produces | Strict Prohibition |
| :--- | :--- | :--- | :--- | :--- |
| **System 1 (RTIS / Physics)** | Kinematic Simulator | Effective speed constraints, track topology | Position, speed, acceleration, dwell state, GPS, dynamic ETA | Cannot predict future risk; cannot decide whether restrictions activate |
| **System 2 (Risk Predictor)** | Operational Risk Engine | Current state at timestamp $t$ + `historical_calibration.json` | `fog_risk`, `congestion_risk`, `operational_risk`, `delay_risk`, `evidence` | **Cannot set speed limits ($40\text{ km/h}$)**; cannot simulate movement; cannot see future states |
| **System 3 (Decision Engine)** | Scenario State Machine | System 2 predictions + threshold config | Active synthetic restrictions (`SyntheticRestriction`), effective speed cap | Cannot simulate kinematics; cannot alter prediction risk values |

---

## 4. Root-Cause Analysis & Fix of the 12-Hour Journey (18:44:30)

### The Bug:
Initial simulations of the 12017 Shatabdi departed NDLS at 06:45 and arrived at 18:44:30 (hitting the 12-hour timeout!).
- **Math**: Running $314\text{ km} @ 23.75\text{ km/h} + \text{dwells} = 13.2\text{ hours}$.
- **Root Cause**: `zone_congestion_index` in the historical dataset for Northern Railway is a static average ($\sim 0.77$). The query evaluated `0.77 >= 0.70 -> True (100%)`, falsely treating every single kilometer of track as an active $25\text{ km/h}$ bottleneck!

### The Solution:
1. **True Empirical Congestion Probability**: Switched query to `p_congestion_delay_cause` ($\sim 20\% - 30\%$), which reflects actual operational delays and allows open-track cruising at $110\text{ km/h}$.
2. **Realistic Daytime Fog Dissipation**: Early morning winter fog ($06:45 - 08:30\text{ AM}$) restricts speed to $40\text{ km/h}$ through Delhi–Meerut. At 09:00 AM, fog clears to $0.0$, System 3 expires the restriction, and the train accelerates to $110\text{ km/h}$ through Saharanpur and Roorkee.
- **Result**: Train arrives at Dehradun (DDN) at **$\sim 12:55\text{ PM} - 01:10\text{ PM}$**, perfectly matching real-world Shatabdi operational timing!

---

## 5. Test Suite & Validation Matrix

All test suites pass 100% across the repository:

```powershell
# 1. Step 3 Historical Calibration Tests
python -m unittest tests/test_historical_calibration.py
# (7 tests: Metadata, absence of flat fog, risk-only schema, hierarchical fallback, determinism) -> OK

# 2. Step 4 System 2 Predictive Engine Tests
python -m unittest tests/test_system2_prediction_engine.py
# (7 tests: BasePredictor compliance, anti-leakage isolation, 30s progression, evidence tracing) -> OK

# 3. Step 5 System 2 -> System 3 Integration Tests
python -m unittest tests/test_system2_system3_integration.py
# (9 tests: Create, update, downgrade, expire, multi-risk resolution, section shift, stale rejection, 4-cycle micro test) -> OK

# 4. Step 6 Closed-Loop Orchestrator Tests
python -m unittest tests/test_closed_loop_orchestrator.py
# (2 tests: 15-step micro simulation, CSV/JSON schema integrity, post-simulation target back-population) -> OK
```

---

## 6. Output Deliverables & File Landmarks

```
railway/
├── config/
│   └── historical_calibration.json       # Compact data-derived empirical lookup matrix (~62 KB)
├── Data/
│   ├── routes/
│   │   └── delhi_dehradun_route.json     # Official 314 km corridor topology (8 stations, 7 sections)
│   ├── synthetic_rtis/
│   │   ├── synthetic_journey_01.csv      # 30-second RTIS telemetry CSV
│   │   └── synthetic_journey_01.json     # Complete structured simulation trace JSON
│   └── ml/
│       └── ml_ready_dataset.csv          # 51-column ML-ready dataset with ground truth targets
├── reports/
│   ├── dataset_audit_report.json         # Step 1 dataset schema & baseline audit
│   ├── factor_audit_summary.md           # Step 1 factor classification summary
│   ├── historical_pattern_analysis.json  # Step 2 pure empirical pattern discovery JSON
│   └── historical_pattern_summary.md     # Step 2 empirical pattern summary markdown
├── src/
│   ├── data_generator/
│   │   ├── audit_historical_factors.py   # Step 1 factor audit engine
│   │   ├── historical_pattern_analyzer.py# Step 2 pattern discovery engine
│   │   ├── calibration_builder.py        # Step 3 calibration builder
│   │   ├── prediction_engine.py          # Step 4 System 2 BaselinePredictiveEngine
│   │   ├── restriction_engine.py         # Step 5 System 3 RestrictionEngine
│   │   └── dataset_builder.py            # Step 6 Full 30s Closed-Loop Orchestrator
└── tests/
    ├── test_historical_calibration.py
    ├── test_system2_prediction_engine.py
    ├── test_system2_system3_integration.py
    └── test_closed_loop_orchestrator.py
```

---

## 7. Future Transition to Phase 8 ML Engine

Because System 2 strictly adheres to the `BasePredictor` interface:
```python
class BasePredictor(ABC):
    @abstractmethod
    def predict(self, current_state: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ConditionPrediction:
        pass
```
In **Phase 8**, the trained `XGBoostPredictor` / `LightGBMPredictor` will plug directly into `dataset_builder.py` and the live runtime **without requiring any changes** to System 1 (Physics), System 3 (Decision Engine), or the 30-second closed-loop orchestrator.
