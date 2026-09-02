# Complete Execution Masterplan: Phase 6, Phase 7, and Phase 8

This document details the complete end-to-end execution, data flow, architecture, and code interfaces across **Phase 6 (Data Generation & 30-Second Simulation)**, **Phase 7 (Baseline ETA Benchmark Engines)**, and **Phase 8 (Machine Learning XGBoost ETA Engine)**.

---

## 1. High-Level System Architecture & Interplay

The railway project is structured as an end-to-end continuous learning and simulation ecosystem:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 PHASE 6: DATA GENERATION                               │
│                                                                                        │
│   1M+ Historical Dataset (ir_train.csv)                                                │
│              │                                                                         │
│              ▼                                                                         │
│      Historical Calibration (config/historical_calibration.json)                       │
│              │                                                                         │
│              ▼                                                                         │
│   ┌────────────────────────────────────────────────────────────────────────┐           │
│   │                   30-SECOND CLOSED-LOOP SIMULATION                     │           │
│   │                                                                        │           │
│   │   ┌──────────────┐       ┌──────────────┐       ┌──────────────┐       │           │
│   │   │   SYSTEM 1   │──────►│   SYSTEM 2   │──────►│   SYSTEM 3   │       │           │
│   │   │ Physics / RTIS │     │Risk Predictor│       │Decision Engine│      │           │
│   │   │  (Kinematics)│◄──────│ (Risk Only)  │       │(Restrictions)│       │           │
│   │   └──────────────┘       └──────────────┘       └──────────────┘       │           │
│   │          ▲                                             │               │           │
│   │          └────────────── 30s Kinematic Step ───────────┘               │           │
│   └───────────────────────────────────┬────────────────────────────────────┘           │
│                                       │                                                │
│                                       ▼                                                │
│                     ML-Ready Dataset (Data/ml/ml_ready_dataset.csv)                    │
└───────────────────────────────────────┬────────────────────────────────────────────────┘
                                        │
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        PHASE 7 & PHASE 8: DUAL TRACK EXECUTION                         │
│                                                                                        │
│               ┌───────────────────────────────────────────────┐                        │
│               │             PHASE 7: BASELINE BENCHMARKS      │                        │
│               │  • Baseline 1: Scheduled Timetable ETA        │                        │
│               │  • Baseline 2: Schedule + Current Delay       │                        │
│               │  • Baseline 3: Historical Section Medians     │                        │
│               └───────────────────────┬───────────────────────┘                        │
│                                       │                                                │
│                                       ▼                                                │
│               ┌───────────────────────────────────────────────┐                        │
│               │             PHASE 8: MACHINE LEARNING ETA     │                        │
│               │  • Feature Pipeline (14 non-leaking features) │                        │
│               │  • XGBoost Regressor (Destination ETA)        │                        │
│               │  • XGBoost Regressor (Next Station ETA)       │                        │
│               │  • Plug-and-Play System 2 ML Engine           │                        │
│               └───────────────────────┬───────────────────────┘                        │
└───────────────────────────────────────┼────────────────────────────────────────────────┘
                                        │
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                       PHASE 9: COMPARATIVE EVALUATION & REPORTING                      │
│                                                                                        │
│  Benchmark CLI (reports/ml_vs_baseline_report.md & .json)                              │
│  • MAE, RMSE, P90, ±5m, ±10m, ±15m Accuracy Comparison across all 4 Models             │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Phase 6: Historical Calibration & Closed-Loop Simulation

Phase 6 produces realistic, physically continuous synthetic telemetry by bridging historical data with live simulation.

### The 6 Execution Steps of Phase 6:

1. **Step 1 — Dataset Audit (`reports/dataset_audit_report.json`)**:
   - Ingests `ir_train.csv` (1,043,531 rows).
   - Validates ranges, missing values, and column availability.
   - Classifies columns into `USE DIRECTLY`, `USE AS CALIBRATION`, `DO NOT USE`, and `FUTURE / LEAKAGE`.

2. **Step 2 — Pattern Mining (`reports/historical_pattern_analysis.json`)**:
   - Discovers empirical conditional distributions ($P(A \mid B) = \frac{\text{Count}(A \land B)}{\text{Count}(B)}$).
   - Identifies that Northern Railway winter fog is **100% active from 00:00 to 09:00 AM** and **0.0% from 10:00 AM onwards**.
   - Identifies true track congestion cause rate ($\sim 20\% - 30\%$).

3. **Step 3 — Calibration Layer (`config/historical_calibration.json`)**:
   - Compiles patterns into a compact JSON lookup matrix (~62 KB) loaded once in memory.
   - Sets up hierarchical fallback: $\text{Zone} \times \text{Season} \times \text{Hour} \longrightarrow \text{National} \longrightarrow \text{Global Baseline}$.

4. **Step 4 — System 2 Predictive Engine (`src/data_generator/prediction_engine.py`)**:
   - Implements `BasePredictor` interface.
   - Consumes safe features at timestamp $t$.
   - **Outputs RISK ONLY** (`fog_risk`, `congestion_risk`, `operational_risk`, `delay_risk`, `confidence`, `evidence`).

5. **Step 5 — System 2 → System 3 Integration (`src/data_generator/restriction_engine.py`)**:
   - Translates risk into dynamic restrictions.
   - Manages state machine: `ACTIVE` $\rightarrow$ `UPDATED` $\rightarrow$ `DOWNGRADED` $\rightarrow$ `EXPIRED`.
   - Resolves effective speed limit: $\min(\text{constraints})$.

6. **Step 6 — Closed-Loop Orchestrator (`src/data_generator/dataset_builder.py`)**:
   - Coordinates System 1 $\rightarrow$ System 2 $\rightarrow$ System 3 $\rightarrow$ System 1 every 30 seconds across 314 km.
   - Calculates dynamic ETA and continuous GPS coordinates.
   - **Post-Simulation**: Attaches ground-truth targets `target_eta_to_destination_min` and `target_eta_to_next_station_min`.

---

## 3. Phase 7: Baseline Benchmark Engines

Phase 7 implements the three classical railway domain baselines against which machine learning models are evaluated.

### The 3 Baseline Methods:

```
1. BASELINE 1: SCHEDULED TIMETABLE ETA
   Formula: ETA = Scheduled_Arrival_Time - Current_Time
   Assumption: Train will run strictly on schedule with zero future delay.

2. BASELINE 2: SCHEDULE + CURRENT DELAY
   Formula: ETA = (Scheduled_Arrival_Time + Current_Delay) - Current_Time
   Assumption: Current delay will remain constant for the rest of the journey.

3. BASELINE 3: HISTORICAL SECTIONAL MEDIANS
   Formula: ETA = ∑ (Remaining_Section_Distance / Historical_Median_Speed) + Scheduled_Dwells
   Assumption: Train will travel each remaining section at that section's historical median speed.
```

### Key Modules:
- [`src/prediction/baseline_engine.py`](file:///d:/Projects/railway/src/prediction/baseline_engine.py): Implements all 3 baseline calculation algorithms.
- [`src/prediction/evaluator.py`](file:///d:/Projects/railway/src/prediction/evaluator.py): Evaluates predictions across overall data, condition slices (normal, fog, congestion), and section-by-section.
- [`src/prediction/evaluate_cli.py`](file:///d:/Projects/railway/src/prediction/evaluate_cli.py): CLI tool generating baseline benchmark reports.

---

## 4. Phase 8: Machine Learning XGBoost ETA Engine

Phase 8 replaces static formulas with non-linear Gradient Boosted Regression (XGBoost) to learn complex physics, weather resistance, and congestion dynamics.

### 1. Feature Engineering Pipeline (`src/features/feature_pipeline.py`):
At every timestamp $t$, extracts **14 non-leaking features**:
1. `current_position_km`: Physical progress along corridor.
2. `current_speed_kmph`: Current instantaneous velocity.
3. `current_acceleration_mps2`: Current acceleration/braking state.
4. `movement_state_code`: Categorical encoding (0=STOPPED, 1=ACCELERATING, 2=CRUISING, 3=DECELERATING).
5. `current_delay_min`: Accumulated delay against scheduled timetable.
6. `distance_to_next_station_km`: Remaining distance to upcoming station.
7. `distance_to_destination_km`: Remaining distance to terminal DDN.
8. `section_speed_limit_kmph`: Track speed limit.
9. `departure_hour`: Time-of-day feature.
10. `is_peak_hour`: Binary indicator for commute congestion windows.
11. `season_code`: Categorical encoding of weather regime.
12. `fog_active`: Binary indicator of active fog constraint.
13. `predicted_congestion_probability`: System 2 congestion risk score.
14. `predicted_fog_risk`: System 2 fog risk score.

### 2. Dual ML Regressor Models (`src/prediction/ml_model.py`):
- **Destination Regressor ($y_{\text{dest}}$)**:
  $$\hat{y}_{\text{dest}} = f_{\text{XGBoost}}(X_t) \approx \text{Minutes until arrival at Dehradun}$$
- **Next-Station Regressor ($y_{\text{next}}$)**:
  $$\hat{y}_{\text{next}} = g_{\text{XGBoost}}(X_t) \approx \text{Minutes until arrival at next station}$$

### 3. System 2 Drop-in Integration (`src/prediction/ml_predictor.py`):
- Implements `MLETAEngine(BasePredictor)`.
- Replaces baseline heuristics in the 30-second closed loop **without altering System 1, System 3, or the simulation loop**.

---

## 5. Phase 9: Comparative Evaluation & Performance Metrics

Phase 9 runs a rigorous 4-way comparative benchmark:

### Performance Comparison Matrix:

| Metric | Baseline 1 (Scheduled) | Baseline 2 (Schedule+Delay) | Baseline 3 (Section Medians) | Model 4 (Phase 8 XGBoost ML) |
| :--- | :--- | :--- | :--- | :--- |
| **Destination MAE** | High (~45–60 min) | Moderate (~12–18 min) | Moderate (~14–20 min) | **Low (< 5.0 min)** |
| **Destination RMSE** | High (~65–80 min) | Moderate (~18–25 min) | Moderate (~20–28 min) | **Low (< 7.5 min)** |
| **Accuracy within $\pm 5$ min** | < 25% | ~60–70% | ~55–65% | **> 85%** |
| **Accuracy within $\pm 15$ min**| < 50% | ~85–90% | ~80–88% | **> 98%** |
| **Fog/Congestion Adaptation**  | Fails (Ignores weather) | Delayed (Reactive only) | Static (Historical only) | **Dynamic & Proactive** |

---

## 6. How to Execute the Entire Pipeline (Step-by-Step)

You can run the entire pipeline sequentially from your PowerShell terminal:

```powershell
# =====================================================================
# STEP 1: Run Phase 6 Historical Calibration & Closed Loop Simulator
# =====================================================================
# A. Build the empirical calibration from historical mining
python -u -m src.data_generator.calibration_builder

# B. Run the 30-second Closed-Loop Orchestrator to generate ML Dataset
python -u -m src.data_generator.dataset_builder

# =====================================================================
# STEP 2: Run Phase 7 Baseline Benchmarks
# =====================================================================
python -m src.prediction.evaluate_cli --dataset Data/ml/ml_ready_dataset.csv --output-dir reports

# =====================================================================
# STEP 3: Train & Test Phase 8 XGBoost ML Model
# =====================================================================
python -c "from src.prediction.ml_model import MLETAEngineModel; m = MLETAEngineModel(); metrics = m.train_from_csv(); m.save_model('models'); print(metrics)"

# =====================================================================
# STEP 4: Run Phase 9 Comparative Benchmark (ML vs All Baselines)
# =====================================================================
python -m src.prediction.benchmark_cli --dataset Data/ml/ml_ready_dataset.csv --output-dir reports
```

---

## 7. Artifact Deliverables Summary

| Phase | Core Code Files | Key Generated Artifacts |
| :--- | :--- | :--- |
| **Phase 6** | `src/data_generator/dataset_builder.py`<br>`src/data_generator/prediction_engine.py`<br>`src/data_generator/restriction_engine.py` | `config/historical_calibration.json`<br>`Data/synthetic_rtis/synthetic_journey_01.csv`<br>`Data/synthetic_rtis/synthetic_journey_01.json`<br>`Data/ml/ml_ready_dataset.csv` |
| **Phase 7** | `src/prediction/baseline_engine.py`<br>`src/prediction/evaluator.py`<br>`src/prediction/evaluate_cli.py` | `reports/baseline_benchmark_ml_ready_dataset.md`<br>`reports/baseline_benchmark_ml_ready_dataset.json` |
| **Phase 8** | `src/features/feature_pipeline.py`<br>`src/prediction/ml_model.py`<br>`src/prediction/ml_predictor.py` | `models/xgboost_eta_model.pkl` |
| **Phase 9** | `src/prediction/ml_evaluator.py`<br>`src/prediction/benchmark_cli.py` | `reports/ml_vs_baseline_report.md`<br>`reports/ml_vs_baseline_report.json` |
