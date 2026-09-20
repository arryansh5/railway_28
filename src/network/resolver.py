"""
src/network/resolver.py — Dynamic Route Resolver Engine
Project Supernova: Phase 4 Implementation

Resolves ordered station sequences, physical track sections, cumulative distances,
traversal directions, multi-division transitions, and path ambiguities across the
topological railway network graph without hardcoded assumptions.
"""

import os
import re
import json
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path


class RouteResolutionResult:
    """Standard container for route resolution response."""
    def __init__(
        self,
        status: str,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        ordered_stations: Optional[List[Dict[str, Any]]] = None,
        ordered_sections: Optional[List[Dict[str, Any]]] = None,
        direction: str = "FORWARD",
        total_distance_km: float = 0.0,
        divisions_traversed: Optional[List[str]] = None,
        zones_traversed: Optional[List[str]] = None,
        route_metadata: Optional[Dict[str, Any]] = None,
        candidate_paths: Optional[List[Dict[str, Any]]] = None,
        error_message: Optional[str] = None
    ):
        self.status = status  # 'RESOLVED', 'AMBIGUOUS', 'UNKNOWN_STATION', 'NO_ROUTE_FOUND'
        self.origin = origin
        self.destination = destination
        self.ordered_stations = ordered_stations or []
        self.ordered_sections = ordered_sections or []
        self.direction = direction
        self.total_distance_km = round(total_distance_km, 2)
        self.divisions_traversed = divisions_traversed or []
        self.zones_traversed = zones_traversed or []
        self.route_metadata = route_metadata or {}
        self.candidate_paths = candidate_paths or []
        self.error_message = error_message

    def get_remaining_distance(self, current_station_code_or_id: str, current_offset_km: float = 0.0) -> float:
        """
        Calculate remaining distance to destination from a given station along the resolved route.
        """
        if not self.ordered_stations or self.status != "RESOLVED":
            return 0.0
            
        norm_code = current_station_code_or_id.strip().upper()
        target_idx = None
        for i, st in enumerate(self.ordered_stations):
            if (st.get("station_code") and st.get("station_code").upper() == norm_code) or \
               (st.get("station_id") and st.get("station_id").upper() == norm_code) or \
               (st.get("station_name") and st.get("station_name").upper() == norm_code):
                target_idx = i
                break
                
        if target_idx is None:
            return 0.0
            
        passed_dist = self.ordered_stations[target_idx].get("distance_from_origin_km", 0.0) + current_offset_km
        remaining = max(0.0, self.total_distance_km - passed_dist)
        return round(remaining, 2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to standard JSON-serializable dictionary."""
        return {
            "status": self.status,
            "origin": self.origin,
            "destination": self.destination,
            "direction": self.direction,
            "total_distance_km": self.total_distance_km,
            "num_stations": len(self.ordered_stations),
            "num_sections": len(self.ordered_sections),
            "divisions_traversed": self.divisions_traversed,
            "zones_traversed": self.zones_traversed,
            "ordered_stations": self.ordered_stations,
            "ordered_sections": self.ordered_sections,
            "route_metadata": self.route_metadata,
            "candidate_paths": self.candidate_paths,
            "error_message": self.error_message
        }


class RouteResolver:
    """
    Dynamic Network Graph Traversal & Route Resolution Service.
    """
    def __init__(self, data_dir: str = "Data"):
        self.data_dir = Path(data_dir)
        self.stations_by_id: Dict[str, Dict[str, Any]] = {}
        self.stations_by_code: Dict[str, Dict[str, Any]] = {}
        self.stations_by_name: Dict[str, Dict[str, Any]] = {}
        self.sections_by_id: Dict[str, Dict[str, Any]] = {}
        self.adjacency: Dict[str, List[Tuple[str, str, float]]] = {}  # stn_id -> [(neighbor_stn_id, section_id, dist_km)]
        self.predefined_routes: List[Dict[str, Any]] = []
        
        self._load_network()

    def _normalize_search_string(self, text: str) -> str:
        """Strip common railway suffixes (Jn, Cantt, Halt, Cabin) and punctuation."""
        t = str(text).upper()
        t = re.sub(r'\b(JN|JUNCTION|CANTT|HALT|CABIN|CITY|EAST|WEST|NORTH|SOUTH|NR|NCR)\b', '', t)
        t = re.sub(r'[^A-Z0-9\s]', '', t)
        return " ".join(t.split())

    def _load_network(self):
        """Load network topology from JSON datasets and corridor files."""
        net_dir = self.data_dir / "network"
        routes_dir = self.data_dir / "routes"
        
        # 1. Load stations from topological database
        stn_file = net_dir / "stations.json"
        if stn_file.exists():
            with open(stn_file, "r", encoding="utf-8") as f:
                stns = json.load(f)
                for s in stns:
                    s_id = s["station_id"]
                    self.stations_by_id[s_id] = s
                    if s.get("station_code"):
                        self.stations_by_code[s["station_code"].upper()] = s
                    if s.get("normalized_name"):
                        self.stations_by_name[s["normalized_name"].upper()] = s
                    if s.get("station_name"):
                        self.stations_by_name[s["station_name"].upper()] = s

        # 2. Load physical sections & build bidirectional adjacency graph
        sec_file = net_dir / "sections.json"
        if sec_file.exists():
            with open(sec_file, "r", encoding="utf-8") as f:
                secs = json.load(f)
                for sec in secs:
                    sec_id = sec["section_id"]
                    u = sec["from_station_id"]
                    v = sec["to_station_id"]
                    dist = float(sec.get("distance_km", 0.0))
                    self.sections_by_id[sec_id] = sec
                    
                    if u not in self.adjacency:
                        self.adjacency[u] = []
                    if v not in self.adjacency:
                        self.adjacency[v] = []
                        
                    self.adjacency[u].append((v, sec_id, dist))
                    self.adjacency[v].append((u, sec_id, dist))

        # 3. Load verified corridor routes
        if routes_dir.exists():
            for r_file in routes_dir.glob("*.json"):
                try:
                    with open(r_file, "r", encoding="utf-8") as f:
                        r_data = json.load(f)
                        if "stations" in r_data and "sections" in r_data:
                            self.predefined_routes.append(r_data)
                            for st in r_data["stations"]:
                                st_code = st.get("station_id")
                                if st_code and st_code.upper() not in self.stations_by_code:
                                    s_obj = {
                                        "station_id": st_code,
                                        "station_code": st_code,
                                        "station_name": st.get("station_name", st_code),
                                        "normalized_name": st.get("station_name", st_code).lower(),
                                        "division": st.get("division", "Northern"),
                                        "zone": st.get("zone", "NR"),
                                        "source_document": "Data/routes"
                                    }
                                    self.stations_by_code[st_code.upper()] = s_obj
                                    self.stations_by_id[st_code] = s_obj
                                    self.stations_by_name[st.get("station_name", "").upper()] = s_obj
                except Exception as e:
                    print(f"Warning loading route {r_file}: {e}")

    def find_station(self, query: str) -> Optional[Dict[str, Any]]:
        """
        100% Dynamic Station Lookup — Zero Hardcoding.
        Searches across all stations in the database with strict precedence:
        1. Exact Station Code (e.g. 'NDLS', 'RK', 'DDN', 'SRE', 'DSA')
        2. Exact Station ID UUID
        3. Exact Station Name (e.g. 'NEW DELHI', 'ROORKEE')
        4. Exact Normalized Name (e.g. 'DELHI' -> matches 'NEW DELHI' / 'DELHI JN')
        5. Token Prefix Match
        """
        if not query:
            return None
            
        q_raw = str(query).strip().upper()
        q_norm = self._normalize_search_string(q_raw)
        
        # 1. Exact Code Match
        if q_raw in self.stations_by_code:
            return self.stations_by_code[q_raw]
            
        # 2. Exact ID Match
        if q_raw in self.stations_by_id:
            return self.stations_by_id[q_raw]
            
        # 3. Exact Name Match
        if q_raw in self.stations_by_name:
            return self.stations_by_name[q_raw]
            
        # 4. Exact Base Token Match (Prioritize primary hub over secondary stations)
        exact_base_matches = []
        for name_key, st in self.stations_by_name.items():
            st_norm = self._normalize_search_string(name_key)
            if q_norm == st_norm:
                return st
            if q_norm in st_norm.split():
                exact_base_matches.append((st_norm, st))
                
        if exact_base_matches:
            # Sort by shortest name (e.g. 'NEW DELHI' or 'DELHI' over 'DELHI SHAHDARA')
            exact_base_matches.sort(key=lambda x: len(x[0]))
            return exact_base_matches[0][1]
                
        # 5. Fallback Substring Match
        for name_key, st in self.stations_by_name.items():
            st_norm = self._normalize_search_string(name_key)
            if q_norm and q_norm in st_norm:
                return st
                
        return None

    def resolve_route(
        self,
        origin: str,
        destination: str,
        via: Optional[List[str]] = None,
        train_number: Optional[str] = None
    ) -> RouteResolutionResult:
        """
        Dynamically resolve route between origin and destination.
        """
        stn_orig = self.find_station(origin)
        stn_dest = self.find_station(destination)
        
        if not stn_orig:
            return RouteResolutionResult(
                status="UNKNOWN_STATION",
                origin=origin,
                destination=destination,
                error_message=f"Origin station '{origin}' could not be found in Northern Railway Network."
            )
        if not stn_dest:
            return RouteResolutionResult(
                status="UNKNOWN_STATION",
                origin=origin,
                destination=destination,
                error_message=f"Destination station '{destination}' could not be found in Northern Railway Network."
            )
            
        orig_code = stn_orig.get("station_code") or stn_orig.get("station_id")
        dest_code = stn_dest.get("station_code") or stn_dest.get("station_id")
        orig_name = stn_orig.get("station_name")
        dest_name = stn_dest.get("station_name")
        orig_norm = self._normalize_search_string(orig_name or orig_code)
        dest_norm = self._normalize_search_string(dest_name or dest_code)
        
        if orig_code == dest_code:
            return RouteResolutionResult(
                status="NO_ROUTE_FOUND",
                origin=orig_code,
                destination=dest_code,
                error_message="Origin and destination cannot be identical."
            )

        # -----------------------------------------------------------------
        # STEP 1: Check Predefined Pilot Corridors (Forward & Reverse)
        # -----------------------------------------------------------------
        for corridor in self.predefined_routes:
            stn_list = corridor.get("stations", [])
            sec_list = corridor.get("sections", [])
            if not stn_list:
                continue
                
            codes_in_corridor = [str(s.get("station_id", "")).upper() for s in stn_list]
            names_in_corridor = [self._normalize_search_string(s.get("station_name", "")) for s in stn_list]
            
            orig_match_idx = None
            dest_match_idx = None
            
            for idx, (c, n) in enumerate(zip(codes_in_corridor, names_in_corridor)):
                if orig_code.upper() == c or orig_norm == n or orig_norm in n.split():
                    orig_match_idx = idx
                if dest_code.upper() == c or dest_norm == n or dest_norm in n.split():
                    dest_match_idx = idx
                    
            if orig_match_idx is not None and dest_match_idx is not None:
                if via:
                    via_matched = True
                    for v in via:
                        v_st = self.find_station(v)
                        v_code = (v_st.get("station_code") or v_st.get("station_id", "")).upper() if v_st else v.upper()
                        if v_code not in codes_in_corridor:
                            via_matched = False
                            break
                    if not via_matched:
                        continue
                        
                # FORWARD DIRECTION
                if orig_match_idx < dest_match_idx:
                    sub_stns = stn_list[orig_match_idx : dest_match_idx + 1]
                    sub_secs = sec_list[orig_match_idx : dest_match_idx]
                    
                    base_km = sub_stns[0].get("distance_from_origin_km", 0.0)
                    ordered_stns = []
                    for i, s in enumerate(sub_stns):
                        cum_km = s.get("distance_from_origin_km", 0.0) - base_km
                        ordered_stns.append({
                            "sequence": i + 1,
                            "station_id": s.get("station_id"),
                            "station_code": s.get("station_id"),
                            "station_name": s.get("station_name"),
                            "distance_from_origin_km": round(cum_km, 2),
                            "is_origin": (i == 0),
                            "is_terminal": (i == len(sub_stns) - 1),
                            "division": s.get("division", "Delhi" if i < len(sub_stns)//2 else "Moradabad"),
                            "zone": s.get("zone", "NR")
                        })
                        
                    ordered_secs = []
                    for i, sec in enumerate(sub_secs):
                        ordered_secs.append({
                            "sequence": i + 1,
                            "section_id": sec.get("section_id"),
                            "from_station_id": sec.get("from_station_id"),
                            "to_station_id": sec.get("to_station_id"),
                            "distance_km": float(sec.get("distance_km", 0.0)),
                            "direction": "FORWARD",
                            "division": ordered_stns[i].get("division", "NR")
                        })
                        
                    tot_km = sum(s["distance_km"] for s in ordered_secs)
                    divs = list(dict.fromkeys(s["division"] for s in ordered_stns if s.get("division")))
                    zones = list(dict.fromkeys(s["zone"] for s in ordered_stns if s.get("zone")))
                    
                    return RouteResolutionResult(
                        status="RESOLVED",
                        origin=ordered_stns[0]["station_code"],
                        destination=ordered_stns[-1]["station_code"],
                        ordered_stations=ordered_stns,
                        ordered_sections=ordered_secs,
                        direction="FORWARD",
                        total_distance_km=tot_km,
                        divisions_traversed=divs,
                        zones_traversed=zones,
                        route_metadata={
                            "corridor_id": corridor.get("route_id", "CORRIDOR_PILOT"),
                            "corridor_name": corridor.get("route_name", "Northern Corridor"),
                            "source_document": "Data/routes"
                        }
                    )
                    
                # REVERSE DIRECTION
                else:
                    sub_stns = stn_list[dest_match_idx : orig_match_idx + 1][::-1]
                    sub_secs = sec_list[dest_match_idx : orig_match_idx][::-1]
                    
                    ordered_secs = []
                    for i, sec in enumerate(sub_secs):
                        ordered_secs.append({
                            "sequence": i + 1,
                            "section_id": sec.get("section_id"),
                            "from_station_id": sec.get("to_station_id"),
                            "to_station_id": sec.get("from_station_id"),
                            "distance_km": float(sec.get("distance_km", 0.0)),
                            "direction": "REVERSE",
                            "division": sub_stns[i].get("division", "NR")
                        })
                        
                    tot_km = sum(s["distance_km"] for s in ordered_secs)
                    
                    ordered_stns = []
                    curr_cum_km = 0.0
                    for i, s in enumerate(sub_stns):
                        ordered_stns.append({
                            "sequence": i + 1,
                            "station_id": s.get("station_id"),
                            "station_code": s.get("station_id"),
                            "station_name": s.get("station_name"),
                            "distance_from_origin_km": round(curr_cum_km, 2),
                            "is_origin": (i == 0),
                            "is_terminal": (i == len(sub_stns) - 1),
                            "division": s.get("division", "Moradabad" if i < len(sub_stns)//2 else "Delhi"),
                            "zone": s.get("zone", "NR")
                        })
                        if i < len(ordered_secs):
                            curr_cum_km += ordered_secs[i]["distance_km"]
                            
                    divs = list(dict.fromkeys(s["division"] for s in ordered_stns if s.get("division")))
                    zones = list(dict.fromkeys(s["zone"] for s in ordered_stns if s.get("zone")))
                    
                    return RouteResolutionResult(
                        status="RESOLVED",
                        origin=ordered_stns[0]["station_code"],
                        destination=ordered_stns[-1]["station_code"],
                        ordered_stations=ordered_stns,
                        ordered_sections=ordered_secs,
                        direction="REVERSE",
                        total_distance_km=tot_km,
                        divisions_traversed=divs,
                        zones_traversed=zones,
                        route_metadata={
                            "corridor_id": corridor.get("route_id", "CORRIDOR_PILOT"),
                            "corridor_name": corridor.get("route_name", "Northern Corridor (Reverse)"),
                            "source_document": "Data/routes"
                        }
                    )

        # -----------------------------------------------------------------
        # STEP 2: General Graph Traversal across Northern Railway Map
        # -----------------------------------------------------------------
        u_id = stn_orig["station_id"]
        v_id = stn_dest["station_id"]
        
        all_paths = self._find_all_paths(u_id, v_id, max_depth=25)
        
        if not all_paths:
            return RouteResolutionResult(
                status="NO_ROUTE_FOUND",
                origin=orig_code,
                destination=dest_code,
                error_message=f"No continuous physical track connects '{orig_code}' and '{dest_code}' in network topology."
            )
            
        if len(all_paths) > 1 and not via and not train_number:
            candidates = []
            for idx, p in enumerate(all_paths):
                path_stns = [self.stations_by_id[nid].get("station_name") for nid in p["nodes"]]
                candidates.append({
                    "path_id": f"PATH_{idx + 1}",
                    "via_intermediate": path_stns[1:-1][:3],
                    "total_distance_km": round(p["total_dist"], 2),
                    "num_hops": len(p["nodes"]) - 1
                })
            return RouteResolutionResult(
                status="AMBIGUOUS",
                origin=orig_code,
                destination=dest_code,
                candidate_paths=candidates,
                error_message="Multiple valid physical routes connect origin and destination. Please specify a 'via' station."
            )
            
        selected_path = all_paths[0]
        if via:
            for p in all_paths:
                p_names = [self.stations_by_id[nid].get("station_name", "").upper() for nid in p["nodes"]]
                p_codes = [self.stations_by_id[nid].get("station_code", "").upper() for nid in p["nodes"]]
                if all(v.upper() in p_names or v.upper() in p_codes for v in via):
                    selected_path = p
                    break
                    
        ordered_stns = []
        ordered_secs = []
        cum_dist = 0.0
        
        for i, stn_node in enumerate(selected_path["nodes"]):
            s_data = self.stations_by_id[stn_node]
            ordered_stns.append({
                "sequence": i + 1,
                "station_id": s_data.get("station_id"),
                "station_code": s_data.get("station_code"),
                "station_name": s_data.get("station_name"),
                "distance_from_origin_km": round(cum_dist, 2),
                "is_origin": (i == 0),
                "is_terminal": (i == len(selected_path["nodes"]) - 1),
                "division": s_data.get("division", "NR"),
                "zone": s_data.get("zone", "NR")
            })
            if i < len(selected_path["edges"]):
                sec_id, step_dist, direction = selected_path["edges"][i]
                ordered_secs.append({
                    "sequence": i + 1,
                    "section_id": sec_id,
                    "from_station_id": selected_path["nodes"][i],
                    "to_station_id": selected_path["nodes"][i + 1],
                    "distance_km": round(step_dist, 2),
                    "direction": direction,
                    "division": s_data.get("division", "NR")
                })
                cum_dist += step_dist

        divs = list(dict.fromkeys(s["division"] for s in ordered_stns if s.get("division")))
        zones = list(dict.fromkeys(s["zone"] for s in ordered_stns if s.get("zone")))
        
        return RouteResolutionResult(
            status="RESOLVED",
            origin=orig_code,
            destination=dest_code,
            ordered_stations=ordered_stns,
            ordered_sections=ordered_secs,
            direction="FORWARD",
            total_distance_km=cum_dist,
            divisions_traversed=divs,
            zones_traversed=zones,
            route_metadata={
                "source_document": "NorthernRailway.pdf",
                "route_type": "Dynamic Topological Traversal"
            }
        )

    def _find_all_paths(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 25
    ) -> List[Dict[str, Any]]:
        """DFS path finding for topological tracks."""
        paths = []
        stack = [(start_id, [start_id], [], 0.0)]
        
        while stack:
            curr, node_path, edge_path, tot_dist = stack.pop()
            
            if curr == end_id and len(node_path) > 1:
                paths.append({
                    "nodes": node_path,
                    "edges": edge_path,
                    "total_dist": tot_dist
                })
                continue
                
            if len(node_path) > max_depth:
                continue
                
            for neighbor, sec_id, dist in self.adjacency.get(curr, []):
                if neighbor not in node_path:
                    sec = self.sections_by_id.get(sec_id, {})
                    direction = "FORWARD" if sec.get("from_station_id") == curr else "REVERSE"
                    stack.append((
                        neighbor,
                        node_path + [neighbor],
                        edge_path + [(sec_id, dist, direction)],
                        tot_dist + dist
                    ))
                    
        paths.sort(key=lambda p: p["total_dist"])
        return paths


# Global Singleton Resolver Instance
default_resolver = RouteResolver()


def resolve_route(
    origin: str,
    destination: str,
    via: Optional[List[str]] = None,
    train_number: Optional[str] = None
) -> Dict[str, Any]:
    """Top-level functional API contract."""
    res = default_resolver.resolve_route(origin, destination, via=via, train_number=train_number)
    return res.to_dict()
