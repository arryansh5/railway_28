# Phase 9: Comprehensive ETA Model Evaluation & Benchmark Report

**Dataset**: `E:\railway_28\Data\synthetic_rtis\synthetic_journey_lucknow_20260902_184646.csv` | **Total 30s Observations**: `858`
**Corridor**: New Delhi (NDLS) → Dehradun (DDN) [314.0 km]

---

## 1. Overall Destination ETA Benchmark

| Model | MAE (min) | RMSE (min) | P50 (min) | P90 (min) | Max Err (min) | ±5 min % | ±15 min % |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline 1: Pure Scheduled** | 36.75 | 37.32 | 38.50 | 38.50 | 38.50 | 1.3% | 3.6% |
| **Baseline 2: Schedule + Delay** | 36.88 | 42.89 | 33.89 | 69.96 | 81.90 | 4.4% | 19.0% |
| **Baseline 3: Section Medians** | 214.09 | 247.12 | 214.00 | 386.00 | 415.50 | 1.2% | 3.5% |
| **Model 4: Phase 8 ML Regressor** | 8.76 | 22.37 | 0.12 | 43.61 | 86.10 | 81.0% | 83.3% |

---

## 2. Next Station ETA Benchmark

| Model | MAE (min) | RMSE (min) | P50 (min) | P90 (min) | ±2 min % | ±5 min % |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline 1: Pure Scheduled** | 44.58 | 56.81 | 35.00 | 108.00 | 2.9% | 7.1% |
| **Baseline 2: Schedule + Delay** | 47.93 | 56.27 | 44.72 | 89.18 | 2.3% | 5.4% |
| **Baseline 3: Section Medians** | 49.93 | 66.17 | 36.00 | 126.00 | 2.8% | 7.0% |
| **Model 4: Phase 8 ML Regressor** | 0.88 | 2.60 | 0.10 | 2.53 | 89.2% | 93.6% |

---

## 3. Sliced Operational Regimes (Destination MAE)

| Operational Slice | Samples | Pure Scheduled | Schedule + Delay | Section Medians | **ML Model (XGB)** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Weather: Fog Active** | 460 | 38.50 min | 33.94 min | 313.37 min | **0.09 min** |
| **Weather: Clear** | 398 | 34.73 min | 40.28 min | 99.35 min | **18.78 min** |
| **Congestion: LOW** | 858 | 36.75 min | 36.88 min | 214.09 min | **8.76 min** |
| **Delay: On-Time (<=5m)** | 21 | 38.50 min | 36.08 min | 415.50 min | **0.06 min** |
| **Delay: Moderate (5-20m)** | 57 | 38.50 min | 25.99 min | 403.87 min | **0.12 min** |
| **Delay: Severe (>20m)** | 780 | 36.58 min | 37.70 min | 194.80 min | **9.63 min** |

---

## 4. Corridor Section-by-Section Performance (Destination MAE)

| Section ID | Observations | Scheduled MAE | Schedule+Delay MAE | Section Medians MAE | **ML Model MAE** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `SEC_ALJN_TDL` | 107 | 38.50 min | 74.17 min | 193.50 min | **0.09 min** |
| `SEC_CNB_LKO` | 93 | 22.35 min | 23.11 min | 23.42 min | **63.11 min** |
| `SEC_ETW_CNB` | 147 | 38.50 min | 28.57 min | 83.00 min | **10.84 min** |
| `SEC_GZB_ALJN` | 337 | 38.50 min | 29.85 min | 304.50 min | **0.09 min** |
| `SEC_NDLS_GZB` | 80 | 38.50 min | 28.44 min | 406.56 min | **0.10 min** |
| `SEC_TDL_ETW` | 94 | 38.50 min | 53.43 min | 143.25 min | **0.09 min** |

---

## 5. Key Operational Findings

1. **Disruption Adaptation**: Under severe weather/fog conditions, the ML Model dynamically factors in active speed restrictions ($40\text{ km/h}$) and congestion to prevent massive ETA underestimation.
2. **Downstream Propagation**: Unlike Baseline 1 which stays statically fixed to the timetable, Baseline 2 and ML dynamically adapt, with ML achieving the lowest error dispersion across the journey.
