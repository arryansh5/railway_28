# Phase 9: Comprehensive ETA Model Evaluation & Benchmark Report

**Dataset**: `Data\ml\ml_ready_dataset.csv` | **Total 30s Observations**: `1136`
**Corridor**: New Delhi (NDLS) → Dehradun (DDN) [314.0 km]

---

## 1. Overall Destination ETA Benchmark

| Model | MAE (min) | RMSE (min) | P50 (min) | P90 (min) | Max Err (min) | ±5 min % | ±15 min % |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline 1: Pure Scheduled** | 183.63 | 196.81 | 230.50 | 230.50 | 230.50 | 1.0% | 2.7% |
| **Baseline 2: Schedule + Delay** | 137.70 | 151.57 | 144.99 | 214.63 | 230.71 | 1.3% | 4.0% |
| **Baseline 3: Section Medians** | 213.92 | 234.11 | 243.50 | 303.50 | 350.50 | 0.9% | 2.6% |
| **Model 4: Phase 8 ML Regressor** | 13.29 | 32.46 | 0.16 | 68.46 | 114.64 | 80.7% | 81.1% |

---

## 2. Next Station ETA Benchmark

| Model | MAE (min) | RMSE (min) | P50 (min) | P90 (min) | ±2 min % | ±5 min % |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline 1: Pure Scheduled** | 43.17 | 52.17 | 41.00 | 88.50 | 2.6% | 6.2% |
| **Baseline 2: Schedule + Delay** | 74.61 | 94.84 | 65.73 | 157.35 | 2.0% | 6.1% |
| **Baseline 3: Section Medians** | 44.21 | 53.50 | 41.00 | 89.00 | 2.5% | 6.2% |
| **Model 4: Phase 8 ML Regressor** | 3.22 | 8.21 | 0.09 | 16.70 | 82.7% | 84.1% |

---

## 3. Sliced Operational Regimes (Destination MAE)

| Operational Slice | Samples | Pure Scheduled | Schedule + Delay | Section Medians | **ML Model (XGB)** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Weather: Fog Active** | 1136 | 183.63 min | 137.70 min | 213.92 min | **13.29 min** |
| **Congestion: HIGH** | 266 | 123.88 min | 162.01 min | 167.17 min | **46.71 min** |
| **Congestion: MEDIUM** | 870 | 201.90 min | 130.27 min | 228.22 min | **3.08 min** |
| **Delay: On-Time (<=5m)** | 33 | 230.50 min | 228.17 min | 230.50 min | **0.13 min** |
| **Delay: Moderate (5-20m)** | 85 | 230.50 min | 218.12 min | 243.91 min | **0.14 min** |
| **Delay: Severe (>20m)** | 1018 | 178.20 min | 128.05 min | 210.88 min | **14.82 min** |

---

## 4. Corridor Section-by-Section Performance (Destination MAE)

| Section ID | Observations | Scheduled MAE | Schedule+Delay MAE | Section Medians MAE | **ML Model MAE** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `SEC_GZB_MTC` | 151 | 230.50 min | 204.55 min | 260.50 min | **0.14 min** |
| `SEC_HW_DDN` | 230 | 57.25 min | 142.37 min | 58.25 min | **65.11 min** |
| `SEC_MOZ_SRE` | 219 | 230.50 min | 128.55 min | 299.92 min | **0.14 min** |
| `SEC_MTC_MOZ` | 195 | 230.50 min | 174.89 min | 303.50 min | **0.14 min** |
| `SEC_NDLS_GZB` | 80 | 230.50 min | 224.41 min | 230.50 min | **0.13 min** |
| `SEC_RK_HW` | 135 | 148.50 min | 23.73 min | 148.50 min | **0.14 min** |
| `SEC_SRE_RK` | 126 | 212.02 min | 74.47 min | 213.75 min | **0.14 min** |

---

## 5. Key Operational Findings

1. **Disruption Adaptation**: Under severe weather/fog conditions, the ML Model dynamically factors in active speed restrictions ($40\text{ km/h}$) and congestion to prevent massive ETA underestimation.
2. **Downstream Propagation**: Unlike Baseline 1 which stays statically fixed to the timetable, Baseline 2 and ML dynamically adapt, with ML achieving the lowest error dispersion across the journey.
