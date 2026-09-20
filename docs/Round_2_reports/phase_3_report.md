# SUPERNOVA — Phase 3: Railway Network Graph & Topology Report

> **Standard Deliverable**: `railway_network_graph.md`  
> **Phase**: 3 — Railway Network Graph  
> **Status**: Completed & 100% Verified  
> **Reference Standard**: [`phase_by_phase.md`](file:///d:/Projects/railway/phase_by_phase.md) (Lines 554–593)  
> **Primary Source Ground Truth**: [`indian-railways-predict-train-delay/NorthernRailway.pdf`](file:///d:/Projects/railway/indian-railways-predict-train-delay/NorthernRailway.pdf)  
> **Implementation**: [`src/network/builder.py`](file:///d:/Projects/railway/src/network/builder.py), [`src/network/validator.py`](file:///d:/Projects/railway/src/network/validator.py)  
> **Database & Data**: [`Data/network/`](file:///d:/Projects/railway/Data/network/) (`stations.json`, `sections.json`, `routes.json`, `route_sections.json`, `network.sqlite`)

---

## 1. Network Topology Summary

The Northern Railway topological network foundation codifies all **16 official Inset callout diagrams** ($A$ through $T$) from the official Northern Railway System Map into an interconnected, bidirectional relational graph.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   NETWORK TOPOLOGY ENTITY TOTALS                       │
│  - Total Inset Route Lines: 24 sub-routes across 16 Inset Maps         │
│  - Globally Unique Stations (Nodes): 298                               │
│  - Globally Unique Physical Sections (Edges): 287                      │
│  - Multi-Route Shared Junction Stations: 11                            │
│  - Relational Database Foreign Key Integrity: 100% (0 violations)      │
│  - Zero-Invention Integrity: 100% (All source-tagged from PDF)         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Relational Schema & Entity Models

The graph is exported to both structured JSON files and a relational SQLite database ([`Data/network/network.sqlite`](file:///d:/Projects/railway/Data/network/network.sqlite)):

### 2.1 Entity Schema Definitions

```sql
-- Stations (Nodes)
CREATE TABLE stations (
    station_id TEXT PRIMARY KEY,
    station_code TEXT,
    station_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL UNIQUE,
    latitude REAL,
    longitude REAL,
    division TEXT,
    zone TEXT DEFAULT 'NR',
    station_category TEXT,
    is_junction INTEGER DEFAULT 0,
    source_document TEXT,
    source_reference TEXT,
    needs_verification INTEGER DEFAULT 0,
    active INTEGER DEFAULT 1
);

-- Sections (Physical Track Edges)
CREATE TABLE sections (
    section_id TEXT PRIMARY KEY,
    from_station_id TEXT NOT NULL REFERENCES stations(station_id),
    to_station_id TEXT NOT NULL REFERENCES stations(station_id),
    from_station_name TEXT NOT NULL,
    to_station_name TEXT NOT NULL,
    distance_km REAL,
    scheduled_run_time_min REAL,
    division TEXT,
    zone TEXT DEFAULT 'NR',
    source_document TEXT,
    source_reference TEXT,
    needs_verification INTEGER DEFAULT 0,
    active INTEGER DEFAULT 1,
    CONSTRAINT uq_station_pair UNIQUE (from_station_id, to_station_id)
);

-- Routes (Ordered Corridor Sequences)
CREATE TABLE routes (
    route_id TEXT PRIMARY KEY,
    corridor_id TEXT,
    map_label TEXT NOT NULL,
    route_name TEXT NOT NULL,
    source_document TEXT,
    source_page INTEGER,
    start_station_name TEXT NOT NULL,
    end_station_name TEXT NOT NULL,
    station_sequence TEXT NOT NULL,
    source_reference TEXT,
    needs_verification INTEGER DEFAULT 0,
    active INTEGER DEFAULT 1
);

-- Route Sections (Ordered Junction Links)
CREATE TABLE route_sections (
    route_id TEXT NOT NULL REFERENCES routes(route_id),
    section_id TEXT NOT NULL REFERENCES sections(section_id),
    sequence_number INTEGER NOT NULL,
    direction TEXT DEFAULT 'FORWARD',
    source_reference TEXT,
    PRIMARY KEY (route_id, sequence_number)
);
```

---

## 3. Bidirectional Section Deduplication (Rule 3)

In strict accordance with **Rule 3**, physical track sections are single unique entities regardless of traversal direction:
* For example, the track between **Roorkee (`RK`)** and **Haridwar (`HW`)** or **Delhi Shahdara (`DSA`)** and **Noli (`NO`)** is stored as a single physical edge in `sections`.
* Traversal in either direction (forward journey vs return journey) is represented in `route_sections` using `direction = 'FORWARD'` or `direction = 'REVERSE'`.
* **Zero duplication** of physical track infrastructure exists across the entire 287-section graph.

---

## 4. Multi-Route Shared Junction Verification

11 major junction nodes connect multiple route branches:
* **`SAHARANPUR Jn.`** (`NR-ST-0100` / `SRE`): Connects `NR-D` (Delhi–Shamli–Saharanpur) and `NR-E` (Saharanpur Bye Pass Line).
* **`TAPRI Jn.`** (`NR-ST-0099` / `TPZ`): Connects `NR-D` and `NR-E`.
* **`DELHI Jn.`** (`NR-ST-0103` / `DLI`): Connects `NR-F1` (Delhi–Ambala), `NR-F2` (Delhi–Ghaziabad), and `NR-K1` (Delhi–Rohtak).
* **`DELHI SHAHDARA Jn.`** (`NR-ST-0064` / `DSA`): Connects `NR-D` and `NR-F2`.
* **`HAZRAT NIZAMUDDIN Jn.`** (`NR-ST-0119` / `HNZM`): Connects `NR-F3` and `NR-F4`.
* **`NAWANSHAHR DOABA Jn.`** (`NR-ST-0026` / `NSS`): Connects `NR-B1`, `NR-B2`, and `NR-B3`.

---

## 5. 18-Point Validation Results Matrix

Executing [`python -u -m src.network.validator`](file:///d:/Projects/railway/src/network/validator.py) produces a **100% pass rate** across all 18 validation gates:

| # | Check Description | Result | Details / Proof |
|---|---|---|---|
| **1** | Valid Route IDs | **PASS** | 24 route records have formatted `NR-*` IDs. |
| **2** | Inset Map Labels Registered | **PASS** | All 16 Insets ($A\dots T$) mapped. |
| **3** | Ordered Station Sequences | **PASS** | Continuous linear station orders on all routes. |
| **4** | Station Pair to Physical Section | **PASS** | Every consecutive station pair has an edge in `sections`. |
| **5** | Station Deduplication | **PASS** | 298 unique stations across all 24 sub-routes. |
| **6** | Section Deduplication | **PASS** | 287 unique physical sections with 0 duplicates. |
| **7** | Shared Junction Nodes | **PASS** | 11 shared junction stations connecting multiple lines. |
| **8** | Shared Physical Sections | **PASS** | Reused physical track sections verified. |
| **9** | Sequence Contiguity | **PASS** | Contiguous 1-indexed integers on all route sections. |
| **10** | Null Safety for Unknowns | **PASS** | Unverified attributes explicitly `NULL`. |
| **11** | Zero Invented Station Codes | **PASS** | Only official IR codes used. |
| **12** | Zero Invented Coordinates | **PASS** | 0 fabricated GPS coordinates. |
| **13** | Source-Derived Chainages | **PASS** | All 287 section distances calculated from map chainages. |
| **14** | Zero Invented Operating Rules | **PASS** | No unverified operational constraints. |
| **15** | System 1 Codebase Intact | **PASS** | Kinematic physics engine untouched. |
| **16** | System 2 Codebase Intact | **PASS** | State engine and predictors untouched. |
| **17** | Frontend Untouched | **PASS** | Frontend directory untouched. |
| **18** | Simulation Routes Valid | **PASS** | 23/23 route checks pass on pilot routes. |
| **DB** | SQLite Foreign Key Integrity | **PASS** | `PRAGMA foreign_key_check` returned 0 violations. |

---

## 6. Phase 3 Conclusion & Next Step

* ✅ **Network Graph Foundation Complete**: Verified 298 stations, 287 sections, 24 routes across 16 insets in JSON and SQLite.
* ✅ **Validation Passed**: 18/18 validation gates passed with zero errors.
* 🛑 **Ready for Driver Review**: We are prepared to proceed to **Phase 4: Dynamic Route Resolver**.
