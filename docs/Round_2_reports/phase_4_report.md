# SUPERNOVA — Phase 4: Dynamic Route Resolver Engine Report

> **Standard Deliverable**: `dynamic_route_resolver.md`  
> **Phase**: 4 — Dynamic Route Resolver  
> **Status**: Completed & 100% Tested  
> **Reference Standard**: [`phase_by_phase.md`](file:///d:/Projects/railway/phase_by_phase.md) (Lines 595–629)  
> **Engine Code**: [`src/network/resolver.py`](file:///d:/Projects/railway/src/network/resolver.py)  
> **Unit Test Suite**: [`tests/test_route_resolver.py`](file:///d:/Projects/railway/tests/test_route_resolver.py)

---

## 1. Engine Overview & Capabilities

The **Dynamic Route Resolver Engine** ([`src/network/resolver.py`](file:///d:/Projects/railway/src/network/resolver.py)) resolves physical paths, station sequences, physical track sections, cumulative distances, traversal directions, and inter-divisional transitions across the entire topological railway network.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   DYNAMIC ROUTE RESOLVER CORE FLOW                     │
│                                                                        │
│   resolve_route(origin, destination, via=None, train_number=None)      │
│       │                                                                │
│       ├── 1. Dynamic Station Matching (Zero Hardcoding)                │
│       │      (By Code 'NDLS', ID, Exact Name, or Normalized Token)     │
│       │                                                                │
│       ├── 2. Directional Traversal (Forward & Reverse)                 │
│       │      (Reuses single physical sections with direction tag)      │
│       │                                                                │
│       ├── 3. Explicit Ambiguity Handling                               │
│       │      (Returns AMBIGUOUS + candidates instead of guessing)      │
│       │                                                                │
│       └── 4. Multi-Division & Remaining Distance Engine                │
│              (Tracks Delhi -> Moradabad handoffs, computes rem. km)    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. API Contract & Output Structure

Calling `resolve_route("NDLS", "DDN")` returns a structured dictionary adhering to the Supernova contract:

```json
{
  "status": "RESOLVED",
  "origin": "NDLS",
  "destination": "DDN",
  "direction": "FORWARD",
  "total_distance_km": 314.0,
  "num_stations": 8,
  "num_sections": 7,
  "divisions_traversed": ["Delhi", "Moradabad"],
  "zones_traversed": ["NR"],
  "ordered_stations": [
    { "sequence": 1, "station_code": "NDLS", "station_name": "New Delhi", "distance_from_origin_km": 0.0, "is_origin": true },
    { "sequence": 2, "station_code": "GZB", "station_name": "Ghaziabad", "distance_from_origin_km": 25.0 },
    { "sequence": 3, "station_code": "MTC", "station_name": "Meerut City", "distance_from_origin_km": 72.0 },
    { "sequence": 4, "station_code": "MOZ", "station_name": "Muzaffarnagar", "distance_from_origin_km": 128.0 },
    { "sequence": 5, "station_code": "SRE", "station_name": "Saharanpur Jn", "distance_from_origin_km": 187.0 },
    { "sequence": 6, "station_code": "RK", "station_name": "Roorkee", "distance_from_origin_km": 221.0 },
    { "sequence": 7, "station_code": "HW", "station_name": "Haridwar Jn", "distance_from_origin_km": 262.0 },
    { "sequence": 8, "station_code": "DDN", "station_name": "Dehradun", "distance_from_origin_km": 314.0, "is_terminal": true }
  ],
  "ordered_sections": [
    { "sequence": 1, "section_id": "SEC_NDLS_GZB", "distance_km": 25.0, "direction": "FORWARD" },
    { "sequence": 2, "section_id": "SEC_GZB_MTC", "distance_km": 47.0, "direction": "FORWARD" },
    { "sequence": 3, "section_id": "SEC_MTC_MOZ", "distance_km": 56.0, "direction": "FORWARD" },
    { "sequence": 4, "section_id": "SEC_MOZ_SRE", "distance_km": 59.0, "direction": "FORWARD" },
    { "sequence": 5, "section_id": "SEC_SRE_RK", "distance_km": 34.0, "direction": "FORWARD" },
    { "sequence": 6, "section_id": "SEC_RK_HW", "distance_km": 41.0, "direction": "FORWARD" },
    { "sequence": 7, "section_id": "SEC_HW_DDN", "distance_km": 52.0, "direction": "FORWARD" }
  ],
  "route_metadata": {
    "corridor_id": "ROUTE_NDLS_DDN_01",
    "corridor_name": "New Delhi to Dehradun Pilot Corridor",
    "source_document": "Data/routes"
  }
}
```

---

## 3. Test Verification Matrix (Phase 4 Specification)

All mandatory route combinations from `phase_by_phase.md` were executed and verified:

| Test Case | Origin $\to$ Destination | Resolved Distance | Direction | Result |
|---|---|---|---|---|
| **Test 1** | `NDLS` $\to$ `RK` (Delhi to Roorkee) | $221.0\text{ km}$ ($6$ stations) | `FORWARD` | **PASS** ✅ |
| **Test 2** | `RK` $\to$ `DDN` (Roorkee to Dehradun) | $93.0\text{ km}$ ($3$ stations) | `FORWARD` | **PASS** ✅ |
| **Test 3** | `DDN` $\to$ `RK` (Dehradun to Roorkee) | $93.0\text{ km}$ ($3$ stations) | `REVERSE` | **PASS** ✅ |
| **Test 4** | `Delhi` $\to$ `Dehradun` (Full Corridor) | $314.0\text{ km}$ ($8$ stations) | `FORWARD` | **PASS** ✅ |
| **Test 5** | Remaining Distance (`NDLS` = 314 km, `SRE` = 127 km, `DDN` = 0 km) | Accurate monotonic countdown | Dynamic | **PASS** ✅ |
| **Test 6** | Unknown Station (`INVALID_STN` $\to$ `DDN`) | Status: `UNKNOWN_STATION` | Error Handled | **PASS** ✅ |
| **Test 7** | Same Station (`NDLS` $\to$ `NDLS`) | Status: `NO_ROUTE_FOUND` | Error Handled | **PASS** ✅ |

---

## 4. Phase 4 Conclusion & Next Step

* ✅ **Dynamic Resolver Implemented**: [`src/network/resolver.py`](file:///d:/Projects/railway/src/network/resolver.py) handles arbitrary forward/reverse lookups with zero hardcoding.
* ✅ **All Tests Passing**: 100% test pass rate across all specified corridors.
* 🛑 **Ready for Driver Review**: Ready to proceed to **Phase 5: Historical Behavior Engine**.
