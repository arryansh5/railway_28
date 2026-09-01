# Phase 6 Step 2 — Historical Pattern Analysis Summary

**Dataset**: `D:\Projects\railway\indian-railways-predict-train-delay\ir_train.csv` | **Records Analyzed**: `1,043,531`
**Geographic Proxy**: Northern Corridors (NR + NCR) [`130,233` records]
**Upstream Reference**: [`reports/dataset_audit_report.json`](file:///d:/Projects/railway/reports/dataset_audit_report.json)

---

## 1. Key Discovered Operational Patterns

### A. When & Where Fog Actually Occurs
- **Seasonality**: Fog is strictly concentrated in `Winter/Fog` season. Summer fog rate is near zero (**0.0%**).
- **Peak Fog Hours (NR/NCR Winter)**: `00:00` (100.0%, N=481), `01:00` (100.0%, N=303), `02:00` (100.0%, N=196).
- **Midday Clearing**: In NR/NCR winter, fog probability drops sharply after 09:00 AM (e.g. 12:00 PM is **0.0%**, N=1,217).
- **Delay Impact**: When fog is active, mean delay is **128.49 min** (vs 96.57 min clear).

### B. When & Where Track Congestion Occurs
- **Peak Congestion Hours (NR/NCR)**: `00:00` (100.0%, N=2,027), `01:00` (100.0%, N=1,177), `02:00` (100.0%, N=800).
- **HDN & Track Impact**: High Density Network (`is_hdn_route=1`) trains experience **74.54% delay rate** (mean: 100.68 min).
- **Single Track Bottlenecks**: Single track sections increase mean delay to **109.36 min** (vs 91.48 min on double track).

### C. Operational Delay Drivers
- **Late Incoming Rake**: Increases delay rate to **87.04%** with mean delay of **130.39 min** (vs 80.23 min normal).
- **Compound Disruption (Late Rake + Fog)**: Severe delay rate (>45m) reaches **99.34%** (mean delay: 151.73 min, N=13,398).
- **Clean Baseline**: Under normal clear conditions with on-time incoming rakes, mean delay is **58.63 min** with **45.41% delay rate**.

---

## 2. Primary Delay Causes Breakdown (Empirical Slices)

| Primary Delay Cause | Sample Count (N) | Delayed (>15m) % | Heavy Delayed (>45m) % | Mean Delay (min) | Median Delay (min) | P90 Delay (min) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **On Time** | 293,533 | 0.0% | 0.0% | 7.01 min | 7.0 min | 13.0 min |
| **Track Congestion** | 168,440 | 100.0% | 99.99% | 134.74 min | 128.0 min | 186.0 min |
| **Flooding / Waterlogging** | 145,269 | 100.0% | 100.0% | 135.8 min | 129.0 min | 187.0 min |
| **Late Incoming Rake** | 112,555 | 100.0% | 100.0% | 145.04 min | 137.0 min | 193.0 min |
| **Track Maintenance / PSR** | 97,108 | 100.0% | 100.0% | 136.1 min | 129.0 min | 188.0 min |
| **Station Congestion** | 49,995 | 100.0% | 99.98% | 133.84 min | 127.0 min | 184.0 min |
| **Signal Failure** | 28,276 | 100.0% | 99.96% | 122.28 min | 114.0 min | 172.0 min |
| **Passenger Emergency** | 21,895 | 100.0% | 99.95% | 119.02 min | 110.0 min | 166.0 min |
| **Freight Priority** | 21,879 | 100.0% | 99.93% | 118.95 min | 110.0 min | 167.0 min |
| **Level Crossing Delay** | 21,825 | 100.0% | 99.95% | 118.63 min | 110.0 min | 166.0 min |
| **Unscheduled Halt** | 21,709 | 100.0% | 99.95% | 118.97 min | 110.0 min | 167.0 min |
| **Crew Availability** | 21,547 | 100.0% | 99.98% | 118.94 min | 110.0 min | 167.0 min |
| **Loco / Engine Failure** | 17,230 | 100.0% | 99.92% | 117.44 min | 109.0 min | 166.0 min |
| **Fog / Low Visibility** | 14,569 | 100.0% | 100.0% | 134.16 min | 128.0 min | 186.0 min |
| **Technical Inspection** | 7,700 | 100.0% | 99.92% | 117.24 min | 109.0 min | 163.0 min |

---

## 3. NR/NCR Winter Fog Matrix (Hour × Season Empirical Counts)

| Hour | Winter/Fog Sample (N) | Fog Count | Empirical Fog Rate (%) | Mean Delay Fog Active | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `00:00` | 481 | 481 | **100.0%** | 135.4 min | VALID_SAMPLE |
| `01:00` | 303 | 303 | **100.0%** | 134.7 min | VALID_SAMPLE |
| `02:00` | 196 | 196 | **100.0%** | 135.6 min | VALID_SAMPLE |
| `03:00` | 177 | 177 | **100.0%** | 130.4 min | VALID_SAMPLE |
| `04:00` | 411 | 411 | **100.0%** | 132.7 min | VALID_SAMPLE |
| `05:00` | 1,439 | 1,439 | **100.0%** | 131.8 min | VALID_SAMPLE |
| `06:00` | 1,915 | 1,915 | **100.0%** | 132.3 min | VALID_SAMPLE |
| `07:00` | 2,447 | 2,447 | **100.0%** | 133.3 min | VALID_SAMPLE |
| `08:00` | 1,910 | 1,910 | **100.0%** | 132.5 min | VALID_SAMPLE |
| `09:00` | 1,495 | 1,495 | **100.0%** | 132.8 min | VALID_SAMPLE |
| `10:00` | 1,161 | 0 | **0.0%** | 0.0 min | VALID_SAMPLE |
| `11:00` | 983 | 0 | **0.0%** | 0.0 min | VALID_SAMPLE |
| `12:00` | 1,217 | 0 | **0.0%** | 0.0 min | VALID_SAMPLE |
| `13:00` | 1,276 | 0 | **0.0%** | 0.0 min | VALID_SAMPLE |
| `14:00` | 1,383 | 0 | **0.0%** | 0.0 min | VALID_SAMPLE |
| `15:00` | 1,501 | 0 | **0.0%** | 0.0 min | VALID_SAMPLE |
| `16:00` | 1,988 | 0 | **0.0%** | 0.0 min | VALID_SAMPLE |
| `17:00` | 2,423 | 0 | **0.0%** | 0.0 min | VALID_SAMPLE |
| `18:00` | 2,473 | 0 | **0.0%** | 0.0 min | VALID_SAMPLE |
| `19:00` | 2,119 | 0 | **0.0%** | 0.0 min | VALID_SAMPLE |
| `20:00` | 1,784 | 0 | **0.0%** | 0.0 min | VALID_SAMPLE |
| `21:00` | 1,504 | 0 | **0.0%** | 0.0 min | VALID_SAMPLE |
| `22:00` | 998 | 0 | **0.0%** | 0.0 min | VALID_SAMPLE |
| `23:00` | 691 | 0 | **0.0%** | 0.0 min | VALID_SAMPLE |
