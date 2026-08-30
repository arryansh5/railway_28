"""
Historical & Synthetic Dataset Generator.
Generates realistic section-level train transit observations with causal operational dynamics,
weather disruptions, TSRs, congestion, and recovery behaviors.
"""

import csv
import json
import math
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Tuple


class DatasetGenerator:
    """
    Simulates multi-day historical railway journeys across a route
    to produce structured tabular datasets for ML model training.
    """

    TRAIN_PROFILES = [
        {"train_id": "12017", "train_name": "Dehradun Shatabdi", "train_type": "SHATABDI", "priority": 1.0, "dep_hour": 6, "dep_min": 45},
        {"train_id": "12055", "train_name": "DDN Jan Shatabdi", "train_type": "SUPERFAST", "priority": 0.9, "dep_hour": 15, "dep_min": 20},
        {"train_id": "14041", "train_name": "Mussoorie Express", "train_type": "EXPRESS", "priority": 0.75, "dep_hour": 22, "dep_min": 25},
        {"train_id": "14309", "train_name": "Ujjaini Express", "train_type": "PASSENGER", "priority": 0.6, "dep_hour": 11, "dep_min": 15},
    ]

    def __init__(self, route: Dict[str, Any], seed: int = 42):
        """
        Initialize the generator.

        Args:
            route: Generic route dictionary.
            seed: Random seed for deterministic reproducibility.
        """
        self.route = route
        self.route_id = route.get("route_id", "ROUTE_01")
        self.stations = sorted(route.get("stations", []), key=lambda s: s.get("sequence", 0))
        self.sections = sorted(route.get("sections", []), key=lambda sec: sec.get("sequence", 0))
        self.seed = seed
        self.rng = random.Random(seed)

        # Precompute section baseline statistics
        self.section_baselines = self._compute_section_baselines()

    def _compute_section_baselines(self) -> Dict[str, Dict[str, float]]:
        """Compute expected baseline median and P90 running times per section."""
        baselines = {}
        for sec in self.sections:
            sec_id = sec["section_id"]
            sched_time = float(sec.get("scheduled_running_time_min", 30.0))
            # In typical historical operations, median is slightly higher (+3%) and P90 is (+25%)
            baselines[sec_id] = {
                "median_min": round(sched_time * 1.03, 2),
                "p90_min": round(sched_time * 1.25, 2)
            }
        return baselines

    def generate_journey_data(self, num_days: int = 45, start_date: str = "2026-07-01") -> List[Dict[str, Any]]:
        """
        Generate section-level observations across multiple days.

        Args:
            num_days: Total number of days to simulate.
            start_date: Start date string (YYYY-MM-DD).

        Returns:
            List of dictionary rows.
        """
        records: List[Dict[str, Any]] = []
        base_dt = datetime.fromisoformat(start_date)

        for day in range(num_days):
            current_date = base_dt + timedelta(days=day)
            day_of_week = current_date.weekday()
            is_weekend = 1 if day_of_week >= 5 else 0

            for train in self.TRAIN_PROFILES:
                journey_id = f"JRN_{current_date.strftime('%Y%m%d')}_{train['train_id']}"
                journey_start_dt = current_date.replace(hour=train["dep_hour"], minute=train["dep_min"], second=0)

                # Initial departure delay at origin (mostly on time, occasional minor delay)
                if self.rng.random() < 0.25:
                    current_delay = round(self.rng.expovariate(1.0 / 5.0), 2)
                else:
                    current_delay = round(self.rng.uniform(-2.0, 1.0), 2)  # sometimes 1-2 min early

                previous_section_delay = 0.0
                current_time = journey_start_dt

                for sec_idx, sec in enumerate(self.sections):
                    sec_id = sec["section_id"]
                    from_st = sec["from_station_id"]
                    to_st = sec["to_station_id"]
                    dist_km = float(sec.get("distance_km", 30.0))
                    sched_time = float(sec.get("scheduled_running_time_min", 30.0))
                    max_speed = float(sec.get("max_sectional_speed_kmph", 110.0))

                    # 1. Congestion simulation
                    cong_roll = self.rng.random()
                    if is_weekend and (16 <= current_time.hour <= 20):
                        cong_level = "HIGH" if cong_roll < 0.35 else ("MEDIUM" if cong_roll < 0.75 else "LOW")
                    elif 8 <= current_time.hour <= 11 or 17 <= current_time.hour <= 20:
                        cong_level = "HIGH" if cong_roll < 0.20 else ("MEDIUM" if cong_roll < 0.60 else "LOW")
                    else:
                        cong_level = "HIGH" if cong_roll < 0.05 else ("MEDIUM" if cong_roll < 0.25 else "LOW")

                    # 2. Weather simulation
                    weather_roll = self.rng.random()
                    if current_time.month in [11, 12, 1, 2] and (current_time.hour <= 8 or current_time.hour >= 21):
                        weather = "FOG" if weather_roll < 0.40 else "CLEAR"
                        visibility_km = round(self.rng.uniform(0.3, 1.2), 2) if weather == "FOG" else 10.0
                    else:
                        weather = "RAIN" if weather_roll < 0.08 else "CLEAR"
                        visibility_km = round(self.rng.uniform(2.0, 5.0), 2) if weather == "RAIN" else 10.0

                    # 3. Temporary Speed Restriction (TSR)
                    tsr_active = 1 if self.rng.random() < 0.12 else 0
                    tsr_speed = round(self.rng.choice([30.0, 45.0, 50.0]), 1) if tsr_active else max_speed

                    # 4. Unscheduled Halt
                    halt_prob = 0.04 if cong_level == "LOW" else (0.12 if cong_level == "MEDIUM" else 0.25)
                    unscheduled_halt = 1 if self.rng.random() < halt_prob else 0
                    unscheduled_halt_min = round(self.rng.uniform(2.0, 12.0), 2) if unscheduled_halt else 0.0

                    # 5. Physics & Transit Time Calculation
                    effective_max_speed = min(max_speed, tsr_speed)
                    if weather == "FOG":
                        effective_max_speed = min(effective_max_speed, 45.0)
                    elif weather == "RAIN":
                        effective_max_speed = min(effective_max_speed, max_speed * 0.9)

                    # Congestion speed penalty factor
                    cong_factor = 1.0 if cong_level == "LOW" else (1.22 if cong_level == "MEDIUM" else 1.55)

                    # Base transit time calculated from physics
                    nominal_speed = effective_max_speed * 0.90
                    transit_time_min = (dist_km / nominal_speed) * 60.0 * cong_factor

                    # Entry speed
                    entry_speed_kmph = round(min(nominal_speed, self.rng.uniform(0.85 * nominal_speed, nominal_speed)), 2)

                    # 6. Recovery potential (if delayed, high priority, clear weather & low congestion)
                    recovery_applied_min = 0.0
                    if current_delay > 2.0 and cong_level == "LOW" and weather == "CLEAR" and not tsr_active:
                        recovery_margin = max(0.0, (sched_time * 1.05) - transit_time_min)
                        recovery_applied_min = round(min(recovery_margin * train["priority"], current_delay * 0.4), 2)

                    # Final actual running time
                    actual_time_min = max(
                        sched_time * 0.85,
                        round(transit_time_min + unscheduled_halt_min - recovery_applied_min + self.rng.gauss(0, 0.5), 2)
                    )

                    section_delay_delta = round(actual_time_min - sched_time, 2)
                    exit_delay = round(current_delay + section_delay_delta, 2)

                    # Base statistics for this section
                    base_stats = self.section_baselines.get(sec_id, {"median_min": sched_time, "p90_min": sched_time * 1.2})

                    record = {
                        "journey_id": journey_id,
                        "train_id": train["train_id"],
                        "train_type": train["train_type"],
                        "timestamp": current_time.strftime("%Y-%m-%dT%H:%M:%S"),
                        "date": current_date.strftime("%Y-%m-%d"),
                        "hour": current_time.hour,
                        "day_of_week": day_of_week,
                        "is_weekend": is_weekend,
                        "section_id": sec_id,
                        "from_station_id": from_st,
                        "to_station_id": to_st,
                        "section_distance_km": dist_km,
                        "scheduled_running_time_min": sched_time,
                        "max_sectional_speed_kmph": max_speed,
                        "entry_speed_kmph": entry_speed_kmph,
                        "entry_delay_min": current_delay,
                        "previous_section_delay_min": previous_section_delay,
                        "congestion_level": cong_level,
                        "weather_condition": weather,
                        "visibility_km": visibility_km,
                        "speed_restriction_active": tsr_active,
                        "restriction_speed_kmph": tsr_speed if tsr_active else None,
                        "unscheduled_halt_active": unscheduled_halt,
                        "unscheduled_halt_min": unscheduled_halt_min,
                        "recovery_applied_min": recovery_applied_min,
                        "historical_section_median_min": base_stats["median_min"],
                        "historical_section_p90_min": base_stats["p90_min"],
                        "actual_section_running_time_min": actual_time_min,
                        "section_delay_delta_min": section_delay_delta,
                        "exit_delay_min": exit_delay,
                        "data_source": "SYNTHETIC_DATASET"
                    }
                    records.append(record)

                    # Update for next section
                    previous_section_delay = section_delay_delta
                    current_delay = exit_delay
                    current_time += timedelta(minutes=actual_time_min + 3.0)  # plus dwell time

        return records

    def export_split_datasets(
        self,
        output_dir: str,
        num_days: int = 45,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15
    ) -> Tuple[str, str, str]:
        """
        Generates data and splits strictly chronologically into train, validation, and test CSVs.

        Args:
            output_dir: Target directory path to save CSVs.
            num_days: Total number of days.
            train_ratio: Percentage of days for training.
            val_ratio: Percentage of days for validation.

        Returns:
            Tuple of (train_csv_path, val_csv_path, test_csv_path).
        """
        os.makedirs(output_dir, exist_ok=True)
        all_data = self.generate_journey_data(num_days=num_days)

        # Unique sorted dates for clean temporal split
        unique_dates = sorted(list(set(row["date"] for row in all_data)))
        total_dates = len(unique_dates)

        train_cutoff_idx = int(total_dates * train_ratio)
        val_cutoff_idx = int(total_dates * (train_ratio + val_ratio))

        train_dates = set(unique_dates[:train_cutoff_idx])
        val_dates = set(unique_dates[train_cutoff_idx:val_cutoff_idx])
        test_dates = set(unique_dates[val_cutoff_idx:])

        train_rows = [r for r in all_data if r["date"] in train_dates]
        val_rows = [r for r in all_data if r["date"] in val_dates]
        test_rows = [r for r in all_data if r["date"] in test_dates]

        fieldnames = list(all_data[0].keys())

        train_path = os.path.join(output_dir, "train.csv")
        val_path = os.path.join(output_dir, "val.csv")
        test_path = os.path.join(output_dir, "test.csv")

        for path, rows in [(train_path, train_rows), (val_path, val_rows), (test_path, test_rows)]:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

        return train_path, val_path, test_path
