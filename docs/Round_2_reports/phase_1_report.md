# SUPERNOVA — Phase 1: Kaggle Dataset Forensic Audit & Historical Feature Dictionary

> **Phase**: 1 — Kaggle Data Audit  
> **Status**: Completed  
> **Reference Standard**: [`phase_by_phase.md`](file:///d:/Projects/railway/phase_by_phase.md) (Lines 420–518)  
> **Audited Datasets**: [`indian-railways-predict-train-delay/ir_train.csv`](file:///d:/Projects/railway/indian-railways-predict-train-delay/ir_train.csv) (278,571 rows), [`indian-railways-predict-train-delay/ir_test.csv`](file:///d:/Projects/railway/indian-railways-predict-train-delay/ir_test.csv) (375,000 rows), [`ir_data_dictionary.csv`](file:///d:/Projects/railway/indian-railways-predict-train-delay/ir_data_dictionary.csv)

---

## 1. Executive Summary & Core Architectural Findings

### 1.1 Fundamental Dataset Characterization
The Kaggle dataset (`ir_train.csv` and `ir_test.csv`) represents a **departure-time journey-level macro dataset** spanning 2018 to 2024 across all Indian Railways zones.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        KAGGLE HISTORICAL WORLD                         │
│  - 278,571 Training Journeys | 375,000 Test Journeys                  │
│  - Unit of Observation: 1 Scheduled Journey (at Departure Time)        │
│  - Ground Truth Labels: Terminal Delay Minutes / Binary Delay (>15m)   │
│  - Intermediate In-Transit Telemetry: ❌ NONE                          │
│  - Speed / Section Telemetry: ❌ NONE                                  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Used for
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       SUPERNOVA ROLE SEPARATION                        │
│  1. System 1 (Simulator): Learns macro distributions & risk priors     │
│     (Fog risk, zone congestion, train-type delays, delay causes)       │
│  2. System 2 (ETA XGBoost): NOT trained on Kaggle directly             │
│     (System 2 requires continuous in-transit kinematic state & ETA)    │
│  3. Kaggle Test Set: Evaluates Kaggle Baseline ONLY (Phase 2)          │
└────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Summary Statistics Comparison

| Metric | Training Dataset (`ir_train.csv`) | Test Dataset (`ir_test.csv`) | Notes & Observations |
|---|---|---|---|
| **Total Rows** | 278,571 journeys | 375,000 journeys | Test set is larger than training set. |
| **Total Columns** | 45 columns | 42 columns | 3 ground truth target columns absent in test. |
| **Date Coverage** | 2018-01-01 to 2024-09-09 | 2018-01-01 to 2024-12-30 | Interleaved/random split across years (not strict chronological cutoff). |
| **Unique Trains** | 6,258 unique train numbers | 6,279 unique train numbers | 6,245 overlapping trains (99.8% overlap). |
| **Missing Values** | Exactly 1 corrupt row (index 278570) | 0 missing values (100% complete) | Clean dataset with no systemic nulls. |
| **Exact Duplicates** | 0 duplicate rows | 0 duplicate rows | 100% unique `journey_id` values. |
| **Target Distribution** | `is_delayed = 1`: 44.82%<br>`is_delayed = 0`: 55.18% | N/A (Held out) | Balanced binary classification target. |
| **Delay Minutes** | Mean: 38.6 min, Median: 12.0 min, Std: 62.4 min, Max: 780 min | N/A (Held out) | Positive skew typical of railway networks. |

---

## 2. Target Columns & Ground Truth Audit

`ir_train.csv` contains three terminal outcome columns evaluated at the journey destination:

1. **`is_delayed`** (`binary`):
   - Definition: `1` if the train arrived $> 15$ minutes late at destination, `0` otherwise.
   - Mean / Rate: $44.82\%$ delayed vs $55.18\%$ on-time.
2. **`delay_minutes`** (`int` / `float`):
   - Definition: Total cumulative minutes of delay upon reaching destination terminal.
   - Range: $0$ to $780$ minutes ($13.0$ hours). Mean: $38.63$ min, 75th percentile: $52$ min.
3. **`primary_delay_cause`** (`categorical`, 15 categories):
   - Major causes: *On Time* ($38.2\%$), *Track Congestion* ($18.4\%$), *Signalling / Interlocking Failure* ($11.2\%$), *Locomotive Breakdown* ($7.8\%$), *Flooding / Waterlogging* ($6.4\%$), *Dense Fog* ($5.9\%$), *Level Crossing Delay* ($4.1\%$), *Accident / Derailment* ($2.3\%$).

> [!IMPORTANT]
> **Supernova Ground Truth Contract**:
> These three fields represent **post-arrival outcomes**. They must **NEVER** be used as prediction features. Furthermore, Kaggle does not provide remaining in-transit travel time, so Kaggle test data cannot directly evaluate System 2.

---

## 3. Comprehensive 12-Point Feature Dictionary

All 42 shared features categorized across the 7 operational dimensions:

---

### Category 1: Train & Service Identity

#### 1.1 `train_number`
* **Semantic Meaning**: 5-digit Indian Railways official train number (e.g., `12017`, `12050`).
* **Data Type**: `string` (represented as categorical / int).
* **Missingness**: Train: 0% | Test: 0%.
* **Cardinality**: Train: 6,258 | Test: 6,279.
* **Classification**: `static` service identifier.
* **Prediction Availability**: Known at departure and pre-booking.
* **Potential Leakage**: None.
* **System Ownership**: System 1 (route/priority matching), System 2 (categorical feature / entity embedding).
* **Usability**: System 1: ✅ | System 2: ✅ | Live: ✅.
* **Transformation**: Target encoding, Frequency encoding, or high-cardinality categorical embedding.

#### 1.2 `train_type`
* **Semantic Meaning**: Commercial train classification (e.g., *Rajdhani, Vande Bharat, Shatabdi, Superfast, Mail/Express, Passenger, Special, Garib Rath*).
* **Data Type**: `string` / `categorical` (14 categories).
* **Missingness**: Train: 0% | Test: 0%.
* **Cardinality**: 14 unique types.
* **Classification**: `static` operational class.
* **Prediction Availability**: Known before departure.
* **Potential Leakage**: None. Priority proxy (higher priority trains get precedence during congestion).
* **System Ownership**: System 1 (kinematic limits & priority resolution), System 2 (key categorical).
* **Usability**: System 1: ✅ | System 2: ✅ | Live: ✅.
* **Transformation**: One-Hot Encoding or Ordinal Priority Score (Vande Bharat/Rajdhani = High, Passenger = Low).

---

### Category 2: Temporal & Calendar Context

#### 2.1 `year`, `month`, `day_of_week`, `departure_hour`
* **Semantic Meaning**: Scheduled departure timestamp components.
* **Data Type**: `int` (Year: 2018–2024, Month: 1–12, Day: 0–6, Hour: 0–23).
* **Missingness**: Train: 0% | Test: 0%.
* **Cardinality**: Discrete numerical ranges.
* **Classification**: `static` scheduled time.
* **Prediction Availability**: Known at departure.
* **Potential Leakage**: None.
* **System Ownership**: System 1 & System 2.
* **Usability**: System 1: ✅ | System 2: ✅ | Live: ✅.
* **Transformation**: Cyclical Sine/Cosine encoding for `month` ($\sin(2\pi m/12)$), `day_of_week`, `departure_hour`.

#### 2.2 `is_weekend`, `is_night_departure`, `is_peak_hour`, `is_festival_season`
* **Semantic Meaning**: Binary calendar flags for congestion, passenger surge, and maintenance windows.
* **Data Type**: `binary` ($0$ or $1$).
* **Missingness**: 0%.
* **Cardinality**: 2 ($0, 1$).
* **Classification**: `derived` temporal context.
* **Prediction Availability**: Known before departure.
* **Potential Leakage**: None.
* **System Ownership**: System 1 & System 2.
* **Usability**: System 1: ✅ | System 2: ✅ | Live: ✅.
* **Transformation**: Direct pass-through binary flag.

#### 2.3 `season`
* **Semantic Meaning**: Macro-meteorological season (*Winter/Fog, Monsoon, Summer, Pre-Monsoon, Post-Monsoon, Autumn*).
* **Data Type**: `categorical` (6 classes).
* **Missingness**: 0%.
* **Cardinality**: 6 unique values.
* **Classification**: `derived` temporal/environmental category.
* **Prediction Availability**: Known before departure.
* **Potential Leakage**: None.
* **System Ownership**: System 1 (scenario selection), System 2 (contextual feature).
* **Usability**: System 1: ✅ | System 2: ✅ | Live: ✅.
* **Transformation**: One-Hot Encoding.

---

### Category 3: Geography & Network Boundaries

#### 3.1 `zone` & `zone_abbr`
* **Semantic Meaning**: Indian Railways administrative zonal authority (e.g., Northern Railway `NR`, North Central `NCR`, Western Railway `WR`).
* **Data Type**: `categorical` (18 zones).
* **Missingness**: 0%.
* **Cardinality**: 18 zones.
* **Classification**: `static` administrative hierarchy.
* **Prediction Availability**: Known at departure.
* **Potential Leakage**: None.
* **System Ownership**: System 1 & System 2.
* **Usability**: System 1: ✅ | System 2: ✅ | Live: ✅.
* **Transformation**: One-Hot Encoding or target encoding.

#### 3.2 `source_station_category` & `destination_station_category`
* **Semantic Meaning**: Commercial footfall & throughput classification of terminal stations ($A1 > A > B > C > D > E$).
* **Data Type**: `categorical` (6 grades).
* **Missingness**: 0%.
* **Cardinality**: 6 unique categories.
* **Classification**: `static` infrastructure attribute.
* **Prediction Availability**: Known before departure.
* **Potential Leakage**: None (major junctions with $A1$ often have yard congestion delays).
* **System Ownership**: System 1 & System 2.
* **Usability**: System 1: ✅ | System 2: ✅ | Live: ✅.
* **Transformation**: Ordinal integer encoding ($A1=6, A=5, \dots, E=1$).

---

### Category 4: Route & Physical Track Infrastructure

#### 4.1 `distance_km`, `num_scheduled_stops`, `scheduled_travel_hours`
* **Semantic Meaning**: Total planned journey length (km), intermediate halt count, and timetable scheduled duration (hours).
* **Data Type**: `float` / `int`.
* **Missingness**: 0%.
* **Cardinality**: High (continuous/integer).
* **Classification**: `static` timetable parameters.
* **Prediction Availability**: Known at departure.
* **Potential Leakage**: None.
* **System Ownership**: System 1 & System 2 (crucial baseline features).
* **Usability**: System 1: ✅ | System 2: ✅ | Live: ✅.
* **Transformation**: Standard scaling; derive `scheduled_average_speed_kmph = distance_km / scheduled_travel_hours`.

#### 4.2 `track_doubled`, `is_hdn_route`, `traction_type`, `is_electrified`, `psr_count`, `is_circular_route`
* **Semantic Meaning**: Physical track infrastructure: single vs double track, High Density Network corridor flag, traction (Electric/Diesel/Dual), Permanent Speed Restriction (PSR) count, loop service flag.
* **Data Type**: `binary` ($0/1$), `int` (`psr_count`), `categorical` (`traction_type`).
* **Missingness**: 0%.
* **Cardinality**: Discrete.
* **Classification**: `static` physical line infrastructure.
* **Prediction Availability**: Known at departure.
* **Potential Leakage**: None.
* **System Ownership**: System 1 (simulation constraints), System 2 (risk multipliers).
* **Usability**: System 1: ✅ | System 2: ✅ | Live: ✅.
* **Transformation**: One-hot for `traction_type`, raw pass-through for binary and numerical.

---

### Category 5: Weather & Environmental Risk Indices

#### 5.1 `is_monsoon_season`, `is_fog_risk`
* **Semantic Meaning**: Binary flags for severe meteorological risk conditions.
* **Data Type**: `binary` ($0/1$).
* **Missingness**: 0%.
* **Cardinality**: 2.
* **Classification**: `derived` macro risk indicator.
* **Prediction Availability**: Known at departure.
* **Potential Leakage**: None.
* **System Ownership**: System 1 & System 2.
* **Usability**: System 1: ✅ | System 2: ✅ | Live: ✅.
* **Transformation**: Binary pass-through.

#### 5.2 `fog_risk_score`, `zone_fog_index`, `zone_congestion_index`, `season_severity_score`
* **Semantic Meaning**: Synthetic continuous indices ($0.0$ to $1.0$) estimating zonal congestion and weather severity.
* **Data Type**: `float` ($0.0 - 1.0$).
* **Missingness**: 0%.
* **Cardinality**: 11 to 16 discrete levels.
* **Classification**: `derived` statistical risk prior.
* **Prediction Availability**: Known at departure based on historical lookups.
* **Potential Leakage**: None.
* **System Ownership**: System 1 (probability of injecting fog/congestion events), System 2 (continuous features).
* **Usability**: System 1: ✅ | System 2: ✅ | Live: ✅.
* **Transformation**: MinMax normalized float pass-through.

---

### Category 6: Rolling Stock & Mechanical Attributes

#### 6.1 `loco_age_years`, `coach_age_years`, `has_lhb_coaches`, `is_rake_shared`, `maintenance_score`
* **Semantic Meaning**: Locomotive and coach mechanical age, modern LHB coach flag, shared rake usage, and preventive maintenance rating ($1.0 - 10.0$).
* **Data Type**: `float` / `binary`.
* **Missingness**: 0%.
* **Cardinality**: Continuous / discrete.
* **Classification**: `static` / `derived` rolling stock attributes.
* **Prediction Availability**: Known at departure when rake is assigned.
* **Potential Leakage**: None.
* **System Ownership**: System 1 (breakdown probability distribution), System 2 (mechanical feature set).
* **Usability**: System 1: ✅ | System 2: ✅ | Live: ✅.
* **Transformation**: Numeric scaling.

---

### Category 7: Operational State & Dynamic Context

#### 7.1 `seat_utilisation_pct`
* **Semantic Meaning**: Passenger load percentage ($0\% - 100\%$).
* **Data Type**: `float`.
* **Missingness**: 0%.
* **Cardinality**: 701 levels.
* **Classification**: `derived` passenger load.
* **Prediction Availability**: Known at chart preparation (~4 hours before departure).
* **Potential Leakage**: None.
* **System Ownership**: System 1 & System 2.
* **Usability**: System 1: ✅ | System 2: ✅ | Live: ✅.
* **Transformation**: Standard scaling.

#### 7.2 `is_overloaded`
* **Semantic Meaning**: Flag indicating seat utilisation $> 100\%$.
* **Data Type**: `binary` / `float`.
* **Missingness**: 0%.
* **Cardinality**: **1 unique value (`0.0`) in BOTH train and test!**
* **Classification**: `static` constant.
* **Prediction Availability**: N/A.
* **Potential Leakage**: None, but **zero variance**.
* **System Ownership**: None (Drop from ML pipeline).
* **Usability**: System 1: ❌ | System 2: ❌ (Zero variance feature).
* **Transformation**: Drop column.

#### 7.3 `late_incoming_rake`, `is_special_train`
* **Semantic Meaning**: Upstream delay propagation flag (`late_incoming_rake = 1`) and non-timetabled special service flag (`is_special_train = 1`).
* **Data Type**: `binary` ($0/1$).
* **Missingness**: 0%.
* **Cardinality**: 2.
* **Classification**: `dynamic` operational state at departure.
* **Prediction Availability**: Known at departure time.
* **Potential Leakage**: None. Strongest single departure-time predictor of initial origin delay.
* **System Ownership**: System 1 (initial delay injection), System 2 (critical initial state feature).
* **Usability**: System 1: ✅ | System 2: ✅ | Live: ✅.
* **Transformation**: Binary pass-through.

#### 7.4 `route_historical_ontime_pct`
* **Semantic Meaning**: Historical on-time arrival percentage ($0\% - 100\%$) for the specific route.
* **Data Type**: `float`.
* **Missingness**: 0%.
* **Cardinality**: 651 levels.
* **Classification**: `derived` historical baseline prior.
* **Prediction Availability**: Available via historical lookup.
* **Potential Leakage**: Low (aggregated prior).
* **System Ownership**: System 1 & System 2.
* **Usability**: System 1: ✅ | System 2: ✅ | Live: ✅.
* **Transformation**: Scale to $[0, 1]$.

---

## 4. Anomalies, Suspicious Features & Remediation

| Issue Detected | Exact Finding | Remediation & Safety Protocol |
|---|---|---|
| **Zero Variance Column** | `is_overloaded` is `0.0` for all 278k training and 375k test rows. | Exclude `is_overloaded` from feature matrices to avoid singular matrix issues. |
| **Date Format Inconsistency** | `ir_train.csv` contains mixed date formats (`1/1/2018` vs `2018-01-01`). | Parse departure date with `pd.to_datetime(format='mixed')` during preprocessing. |
| **Single Corrupted Row** | Row index `278570` in `ir_train.csv` has NaN values across all columns after `train_type`. | Drop this single corrupted row during dataset loading (`df.dropna(subset=['delay_minutes'])`). |
| **Absence of In-Transit Telemetry** | Kaggle contains zero intermediate station stops, section speeds, or real-time GPS coordinates. | Confirm Kaggle data role: Learn macro prior distributions for System 1. Do not use Kaggle for System 2 continuous trajectory training. |

---

## 5. Phase 1 Conclusion & Verification

1. **Feature Dictionary Status**: All 45 columns in `ir_train.csv` and 42 columns in `ir_test.csv` audited and codified.
2. **Leakage Safety**: 0% future-outcome leakage identified in departure-time feature set.
3. **ML Boundary Maintained**: Zero machine learning models were trained.
4. **Deliverable Ready**: [`historical_feature_dictionary.md`](file:///d:/Projects/railway/docs/Round_2_reports/phase_1_report.md) is created and ready for driver review.
