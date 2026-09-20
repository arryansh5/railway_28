# SUPERNOVA — Phase 1: Historical Feature Dictionary

> **Standard Deliverable**: `historical_feature_dictionary.md`  
> **Source Datasets**: [`indian-railways-predict-train-delay/ir_train.csv`](file:///d:/Projects/railway/indian-railways-predict-train-delay/ir_train.csv) (278,571 rows), [`indian-railways-predict-train-delay/ir_test.csv`](file:///d:/Projects/railway/indian-railways-predict-train-delay/ir_test.csv) (375,000 rows)  
> **Full Forensic Report**: [`docs/Round_2_reports/phase_1_report.md`](file:///d:/Projects/railway/docs/Round_2_reports/phase_1_report.md)

---

## 1. Ground Truth Target Columns (Train Set Only)

| Column Name | Data Type | Missing % | Definition / Range | Leakage Status & System Usage |
|---|---|---|---|---|
| **`is_delayed`** | `binary` (0/1) | 0.00% (1 row) | 1 if arrival delay > 15 mins at destination (44.82% delayed) | **POST-OUTCOME TARGET**. Never use as feature. Evaluated in Phase 2 Baseline. |
| **`delay_minutes`** | `float` / `int` | 0.00% (1 row) | Destination terminal delay in minutes (Mean: 38.6m, Max: 780m) | **POST-OUTCOME TARGET**. Never use as feature. Evaluated in Phase 2 Baseline. |
| **`primary_delay_cause`**| `categorical` | 0.00% (1 row) | 15 categories (On Time, Congestion, Fog, Signalling, Locomotive, etc.) | **POST-OUTCOME CAUSE**. Used to calibrate System 1 failure probabilities. |

---

## 2. 12-Point Feature Dictionary Matrix

| Feature Name | Category | Dtype | Train Uniq | Test Uniq | Class | Prediction Availability | Leakage Risk | System Owner | S1 Usable | S2 Usable | Live Usable | Recommended Transformation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `train_number` | Service | `string` | 6,258 | 6,279 | `static` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Categorical embedding / Frequency encoding |
| `train_type` | Service | `category` | 14 | 14 | `static` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | One-hot / Ordinal priority rank |
| `departure_date` | Time | `date` | 2,444 | 2,556 | `static` | At Departure | None | Context | ✅ | ✅ | ✅ | Parse mixed formats; extract time parts |
| `year` | Time | `int` | 7 | 7 | `static` | At Departure | None | Context | ✅ | ✅ | ✅ | Numeric / Trend feature |
| `month` | Time | `int` | 12 | 12 | `static` | At Departure | None | Context | ✅ | ✅ | ✅ | Cyclical Sine/Cosine ($\sin(2\pi m/12)$) |
| `day_of_week` | Time | `int` | 7 | 7 | `static` | At Departure | None | Context | ✅ | ✅ | ✅ | Cyclical Sine/Cosine ($\sin(2\pi d/7)$) |
| `departure_hour` | Time | `int` | 24 | 24 | `static` | At Departure | None | Context | ✅ | ✅ | ✅ | Cyclical Sine/Cosine ($\sin(2\pi h/24)$) |
| `is_weekend` | Time | `binary` | 2 | 2 | `derived` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Pass-through binary |
| `is_night_departure` | Time | `binary` | 2 | 2 | `derived` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Pass-through binary |
| `is_peak_hour` | Time | `binary` | 2 | 2 | `derived` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Pass-through binary |
| `is_festival_season` | Time | `binary` | 2 | 2 | `derived` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Pass-through binary |
| `season` | Time | `category` | 6 | 6 | `derived` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | One-hot encoding |
| `zone` | Geography | `category` | 18 | 18 | `static` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Target encoding / One-hot |
| `zone_abbr` | Geography | `category` | 18 | 18 | `static` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Redundant with `zone` (drop one) |
| `source_station_category` | Geography | `category` | 6 | 6 | `static` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Ordinal encoding ($A1=6 \dots E=1$) |
| `destination_station_category`| Geography | `category` | 6 | 6 | `static` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Ordinal encoding ($A1=6 \dots E=1$) |
| `distance_km` | Route | `float` | 2,538 | 2,622 | `static` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Standard scale; derive avg speed |
| `num_scheduled_stops` | Route | `float` | 31 | 33 | `static` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Standard scale; halt density |
| `scheduled_travel_hours` | Route | `float` | 3,216 | 3,316 | `static` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Standard scale; timetable duration |
| `track_doubled` | Route | `binary` | 2 | 2 | `static` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Pass-through binary |
| `is_hdn_route` | Route | `binary` | 2 | 2 | `static` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Pass-through binary |
| `traction_type` | Route | `category` | 3 | 3 | `static` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | One-hot encoding |
| `is_electrified` | Route | `binary` | 2 | 2 | `static` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Pass-through binary |
| `psr_count` | Route | `float` | 14 | 15 | `static` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Numeric scaling |
| `is_circular_route` | Route | `binary` | 2 | 2 | `static` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Pass-through binary |
| `is_monsoon_season` | Weather | `binary` | 2 | 2 | `derived` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Pass-through binary |
| `is_fog_risk` | Weather | `binary` | 2 | 2 | `derived` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Pass-through binary |
| `fog_risk_score` | Weather | `float` | 14 | 14 | `derived` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | MinMax normalized $[0, 1]$ |
| `zone_fog_index` | Weather | `float` | 13 | 13 | `derived` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | MinMax normalized $[0, 1]$ |
| `zone_congestion_index` | Weather | `float` | 16 | 16 | `derived` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | MinMax normalized $[0, 1]$ |
| `season_severity_score` | Weather | `float` | 11 | 11 | `derived` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | MinMax normalized $[0, 1]$ |
| `loco_age_years` | Rolling Stock| `float` | 401 | 401 | `static` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Robust standard scale |
| `coach_age_years` | Rolling Stock| `float` | 449 | 448 | `static` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Robust standard scale |
| `has_lhb_coaches` | Rolling Stock| `binary` | 2 | 2 | `static` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Pass-through binary |
| `is_rake_shared` | Rolling Stock| `binary` | 2 | 2 | `static` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Pass-through binary |
| `maintenance_score` | Rolling Stock| `float` | 91 | 91 | `derived` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | MinMax scale $[0.1, 1.0]$ |
| `seat_utilisation_pct` | Operations | `float` | 701 | 701 | `derived` | Chart Prep | None | S1 / S2 | ✅ | ✅ | ✅ | Scale to $[0, 1]$ |
| `is_overloaded` | Operations | `binary` | **1** | **1** | `static` | N/A | None | **None** | ❌ | ❌ | ❌ | **DROP** (Zero variance = 0.0) |
| `late_incoming_rake` | Operations | `binary` | 2 | 2 | `dynamic` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Primary origin delay indicator |
| `is_special_train` | Operations | `binary` | 2 | 2 | `static` | At Departure | None | S1 / S2 | ✅ | ✅ | ✅ | Pass-through binary |
| `route_historical_ontime_pct`| Operations | `float` | 651 | 651 | `derived` | Historical Prior| None | S1 / S2 | ✅ | ✅ | ✅ | Scale to $[0, 1]$ |

---

## 3. Train vs Test Distribution & Anomaly Audit

1. **Train/Test Split Mechanism**:
   - The test set covers the identical date range (2018–2024) and shares $99.8\%$ of train numbers with the training set. This confirms a **random stratified journey split** rather than an out-of-time chronological cutoff.
2. **Missing Values**:
   - Exactly $1$ corrupt row at index `278570` in `ir_train.csv` (drop on read).
   - $0$ missing values across all 375,000 test rows.
3. **Zero Variance Feature**:
   - `is_overloaded` is constant `0.0` in both datasets and must be dropped.
4. **Target Absence in Test**:
   - `is_delayed`, `delay_minutes`, and `primary_delay_cause` are strictly absent in `ir_test.csv`.
