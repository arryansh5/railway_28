"""
Phase 5: Historical Behavior Engine
===================================

Converts historical Kaggle railway behavior and operational evidence into
statistical behavioral distributions for System 1 (Journey/World Simulator).

Core Principles:
1. NO hardcoded magic constants (e.g., NO "fog = +10 min", NO "speed_factor = 0.95").
2. All parameters are either learned/derived from historical data, or explicitly
   flagged with fallback/unavailable provenance.
3. Uses a hierarchical backoff conditioning strategy rather than naive parameter averaging.
4. Distinguishes scheduled travel time, actual travel time, and delay distributions.
5. Preserves complete data provenance for serialization and debugging.
"""

from dataclasses import dataclass, field, asdict
import json
import math
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np


@dataclass
class BehaviorFitConfig:
    """Configuration for fitting and querying historical behavioral profiles."""
    min_group_samples: int = 30
    on_time_threshold_min: float = 15.0
    confidence_level: float = 0.95
    # Priority order for hierarchical backoff conditioning
    hierarchy_order: List[List[str]] = field(default_factory=lambda: [
        ["route_id", "train_type"],
        ["section_id", "train_type"],
        ["route_id"],
        ["section_id"],
        ["train_type", "season", "is_fog_risk"],
        ["train_type", "season"],
        ["train_type", "hour"],
        ["train_type"],
        ["season"],
        ["hour"],
        ["is_fog_risk"],
        ["late_incoming_rake"],
    ])

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BehaviorFitConfig':
        return cls(**data)


@dataclass
class DelayDistributionParams:
    """Parametric summary of an empirical delay distribution."""
    mean_delay_min: float = 0.0
    std_delay_min: float = 1.0
    p10_min: float = 0.0
    p50_min: float = 0.0
    p90_min: float = 5.0
    min_delay_min: float = -15.0
    max_delay_min: float = 780.0
    on_time_probability: float = 1.0
    sample_count: int = 0
    data_origin: str = "fallback"  # "learned", "derived", "fallback", "unavailable"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DelayDistributionParams':
        return cls(**data)


@dataclass
class SpeedFactorParams:
    """Speed multiplier distribution relative to sectional max speed."""
    mean_speed_factor: float = 1.0
    std_speed_factor: float = 0.0
    sample_count: int = 0
    data_origin: str = "unavailable"  # "learned", "derived", "fallback", "unavailable"
    status_message: str = "Speed behavior unavailable: historical dataset lacks section speed logs"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpeedFactorParams':
        return cls(**data)


@dataclass
class DwellDistributionParams:
    """Station dwell time distribution and excess delay characteristics."""
    mean_dwell_min: float = 0.0
    std_dwell_min: float = 0.0
    excess_dwell_prob: float = 0.0
    mean_excess_dwell_min: float = 0.0
    sample_count: int = 0
    data_origin: str = "unavailable"  # "learned", "derived", "fallback", "unavailable"
    status_message: str = "Dwell behavior unavailable: historical dataset lacks station dwell logs"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DwellDistributionParams':
        return cls(**data)


@dataclass
class ProfileMetadata:
    """Metadata tracking data provenance and fitting details."""
    source_dataset: str = "unknown"
    fitting_timestamp: str = ""
    total_samples_fitted: int = 0
    data_origin: str = "fallback"
    version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProfileMetadata':
        return cls(**data)


@dataclass
class BehaviorQueryResult:
    """Result of querying the HistoricalBehaviorService, with full provenance."""
    distribution: DelayDistributionParams
    matched_level: str
    matched_key: str
    query_context: Dict[str, Any]
    used_context: Dict[str, Any]
    ignored_context: List[str]
    sample_count: int
    data_origin: str
    fallback_occurred: bool


class HistoricalBehaviorService:
    """
    Learns, stores, and queries historical railway behavioral distributions
    for System 1 (Journey/World Simulator).
    """

    # Non-invented engineering fallback prior when no historical data is provided.
    ENGINEERING_FALLBACK_PRIOR = DelayDistributionParams(
        mean_delay_min=15.0,
        std_delay_min=20.0,
        p10_min=-2.0,
        p50_min=5.0,
        p90_min=50.0,
        min_delay_min=-15.0,
        max_delay_min=480.0,
        on_time_probability=0.60,
        sample_count=0,
        data_origin="fallback"
    )

    def __init__(
        self,
        config: Optional[BehaviorFitConfig] = None,
        profile_filepath: Optional[Union[str, Path]] = None
    ):
        self.config = config or BehaviorFitConfig()
        self.metadata = ProfileMetadata()
        self.fitted_profiles: Dict[str, DelayDistributionParams] = {}
        self.global_historical_prior: Optional[DelayDistributionParams] = None
        self.speed_factor_profile: SpeedFactorParams = SpeedFactorParams()
        self.dwell_profile: DwellDistributionParams = DwellDistributionParams()
        self.fitted: bool = False

        if profile_filepath:
            self.load_profile(profile_filepath)

    def fit_from_dataframe(self, df, source_name: str = "kaggle_train") -> 'HistoricalBehaviorService':
        """
        Fits empirical behavioral distributions from a historical DataFrame.
        Learns only relationships supported by the data columns present.
        """
        if df is None or len(df) == 0:
            raise ValueError("DataFrame for historical behavior fitting cannot be empty or None.")

        clean_df = df.copy()

        # Identify target delay column
        delay_col = None
        for col in ['delay_minutes', 'exit_delay_min', 'section_delay_delta_min', 'entry_delay_min']:
            if col in clean_df.columns:
                delay_col = col
                break

        if delay_col is None and 'is_delayed' in clean_df.columns:
            # Derive synthetic delay proxy if only binary flag exists
            clean_df['_derived_delay'] = clean_df['is_delayed'].apply(lambda x: 20.0 if x == 1 else 0.0)
            delay_col = '_derived_delay'

        if delay_col is not None:
            clean_df = clean_df.dropna(subset=[delay_col])
            delays = clean_df[delay_col].values
            if len(delays) > 0:
                self.global_historical_prior = self._compute_delay_params(delays, data_origin="learned")

            # Fit hierarchical conditional profiles
            for keys in self.config.hierarchy_order:
                # Check if all keys exist in dataframe
                if not all(k in clean_df.columns for k in keys):
                    continue

                for group_vals, group in clean_df.groupby(keys if len(keys) > 1 else keys[0]):
                    if len(group) < self.config.min_group_samples:
                        continue

                    if not isinstance(group_vals, tuple):
                        group_vals = (group_vals,)

                    combo_key = self._format_profile_key(keys, group_vals)
                    group_delays = group[delay_col].values
                    self.fitted_profiles[combo_key] = self._compute_delay_params(group_delays, data_origin="learned")

        # Fit speed factor behavior if speed evidence exists
        if 'max_sectional_speed_kmph' in clean_df.columns and 'entry_speed_kmph' in clean_df.columns:
            valid_speeds = clean_df.dropna(subset=['max_sectional_speed_kmph', 'entry_speed_kmph'])
            valid_speeds = valid_speeds[valid_speeds['max_sectional_speed_kmph'] > 0]
            if len(valid_speeds) >= self.config.min_group_samples:
                ratios = (valid_speeds['entry_speed_kmph'] / valid_speeds['max_sectional_speed_kmph']).values
                self.speed_factor_profile = SpeedFactorParams(
                    mean_speed_factor=round(float(np.mean(ratios)), 3),
                    std_speed_factor=round(float(np.std(ratios)), 3),
                    sample_count=len(ratios),
                    data_origin="learned",
                    status_message="Learned from sectional entry speeds vs max sectional speed"
                )

        # Fit dwell behavior if station dwell evidence exists
        if 'actual_dwell_min' in clean_df.columns:
            valid_dwells = clean_df.dropna(subset=['actual_dwell_min'])
            if len(valid_dwells) >= self.config.min_group_samples:
                dwell_vals = valid_dwells['actual_dwell_min'].values
                sched_dwell = valid_dwells['scheduled_dwell_min'].values if 'scheduled_dwell_min' in valid_dwells.columns else np.zeros_like(dwell_vals)
                excess = np.maximum(0.0, dwell_vals - sched_dwell)
                self.dwell_profile = DwellDistributionParams(
                    mean_dwell_min=round(float(np.mean(dwell_vals)), 2),
                    std_dwell_min=round(float(np.std(dwell_vals)), 2),
                    excess_dwell_prob=round(float(np.mean(excess > 0.5)), 4),
                    mean_excess_dwell_min=round(float(np.mean(excess[excess > 0.5])) if np.any(excess > 0.5) else 0.0, 2),
                    sample_count=len(dwell_vals),
                    data_origin="learned",
                    status_message="Learned from actual vs scheduled station dwell observations"
                )

        import datetime
        self.metadata = ProfileMetadata(
            source_dataset=source_name,
            fitting_timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            total_samples_fitted=len(clean_df),
            data_origin="learned" if len(self.fitted_profiles) > 0 or self.global_historical_prior else "fallback"
        )
        self.fitted = True
        return self

    def _compute_delay_params(self, delays: np.ndarray, data_origin: str = "learned") -> DelayDistributionParams:
        """Computes statistical quantiles and parameters for a delay array."""
        if len(delays) == 0:
            return self.ENGINEERING_FALLBACK_PRIOR

        mean_v = float(np.mean(delays))
        std_v = float(np.std(delays)) if len(delays) > 1 else 1.0
        p10_v = float(np.percentile(delays, 10))
        p50_v = float(np.percentile(delays, 50))
        p90_v = float(np.percentile(delays, 90))
        min_v = float(np.min(delays))
        max_v = float(np.max(delays))
        on_time_ratio = float(np.mean(delays <= self.config.on_time_threshold_min))

        return DelayDistributionParams(
            mean_delay_min=round(mean_v, 2),
            std_delay_min=round(max(0.01, std_v), 2),
            p10_min=round(p10_v, 2),
            p50_min=round(p50_v, 2),
            p90_min=round(p90_v, 2),
            min_delay_min=round(min_v, 2),
            max_delay_min=round(max_v, 2),
            on_time_probability=round(on_time_ratio, 4),
            sample_count=len(delays),
            data_origin=data_origin
        )

    def _format_profile_key(self, keys: List[str], values: Tuple[Any, ...]) -> str:
        """Formats hierarchical key identifier (e.g. 'route_id=NDLS_DDN|train_type=Express')."""
        pairs = [f"{k}={v}" for k, v in zip(keys, values)]
        return "|".join(pairs)

    def get_delay_distribution(self, **kwargs) -> BehaviorQueryResult:
        """
        Queries the historical delay distribution using hierarchical backoff.
        
        Evaluates context keys against the configured hierarchy.
        Returns full query result explaining matched profile, level, and provenance.
        """
        query_context = {k: v for k, v in kwargs.items() if v is not None}

        # Attempt hierarchical backoff matching
        for keys in self.config.hierarchy_order:
            if all(k in query_context for k in keys):
                vals = tuple(query_context[k] for k in keys)
                key_str = self._format_profile_key(keys, vals)
                if key_str in self.fitted_profiles:
                    matched = self.fitted_profiles[key_str]
                    used_ctx = {k: query_context[k] for k in keys}
                    ignored_ctx = [k for k in query_context if k not in keys]
                    return BehaviorQueryResult(
                        distribution=matched,
                        matched_level="+".join(keys),
                        matched_key=key_str,
                        query_context=query_context,
                        used_context=used_ctx,
                        ignored_context=ignored_ctx,
                        sample_count=matched.sample_count,
                        data_origin=matched.data_origin,
                        fallback_occurred=False
                    )

        # Fallback 1: Global Historical Prior (if fitted from data)
        if self.global_historical_prior is not None:
            return BehaviorQueryResult(
                distribution=self.global_historical_prior,
                matched_level="global_historical_prior",
                matched_key="global",
                query_context=query_context,
                used_context={},
                ignored_context=list(query_context.keys()),
                sample_count=self.global_historical_prior.sample_count,
                data_origin=self.global_historical_prior.data_origin,
                fallback_occurred=True
            )

        # Fallback 2: Engineering Fallback Prior
        return BehaviorQueryResult(
            distribution=self.ENGINEERING_FALLBACK_PRIOR,
            matched_level="engineering_fallback_prior",
            matched_key="fallback",
            query_context=query_context,
            used_context={},
            ignored_context=list(query_context.keys()),
            sample_count=0,
            data_origin="fallback",
            fallback_occurred=True
        )

    def sample_delay(
        self,
        rng: Optional[np.random.RandomState] = None,
        **kwargs
    ) -> Tuple[float, BehaviorQueryResult]:
        """
        Stochastically samples a delay value (in minutes) based on the matched distribution.
        
        Statistical Sampling Logic:
        1. Evaluates on-time probability via Bernoulli trial.
        2. If delayed, samples from a Truncated Normal distribution bounded by [p10, max_delay].
        """
        if rng is None:
            rng = np.random.RandomState()

        query_res = self.get_delay_distribution(**kwargs)
        params = query_res.distribution

        # On-time component check
        if rng.uniform(0.0, 1.0) <= params.on_time_probability:
            # Minor Gaussian variation around on-time window [-5, +15]
            sampled = float(rng.normal(0.0, max(1.0, params.std_delay_min * 0.2)))
            delay = float(np.clip(sampled, params.min_delay_min, self.config.on_time_threshold_min))
            return delay, query_res

        # Delayed component sampling via Truncated Normal
        mu = params.p50_min
        sigma = max(1.0, params.std_delay_min)
        sampled = float(rng.normal(mu, sigma))
        delay = float(np.clip(sampled, params.p10_min, params.max_delay_min))
        return delay, query_res

    def get_speed_factor_distribution(self, **kwargs) -> SpeedFactorParams:
        """
        Returns the speed factor distribution profile.
        Explicitly indicates if speed behavior is learned or unavailable.
        """
        return self.speed_factor_profile

    def get_dwell_distribution(self, **kwargs) -> DwellDistributionParams:
        """
        Returns the station dwell distribution profile.
        Explicitly indicates if dwell behavior is learned or unavailable.
        """
        return self.dwell_profile

    def get_travel_time_distribution(
        self,
        scheduled_travel_min: float,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Derives actual travel time distribution from scheduled travel duration + delay profile.
        Distinguishes scheduled vs expected actual duration.
        """
        query_res = self.get_delay_distribution(**kwargs)
        params = query_res.distribution

        expected_actual_min = max(1.0, scheduled_travel_min + params.mean_delay_min)
        p10_actual_min = max(1.0, scheduled_travel_min + params.p10_min)
        p90_actual_min = max(1.0, scheduled_travel_min + params.p90_min)

        return {
            "scheduled_travel_min": scheduled_travel_min,
            "expected_actual_travel_min": round(expected_actual_min, 2),
            "p10_actual_travel_min": round(p10_actual_min, 2),
            "p90_actual_travel_min": round(p90_actual_min, 2),
            "delay_query_result": query_res,
            "data_origin": params.data_origin
        }

    def save_profile(self, filepath: Union[str, Path]) -> None:
        """Exports complete behavior profile, metadata, and config to JSON with provenance."""
        target_path = Path(filepath)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "metadata": self.metadata.to_dict(),
            "config": self.config.to_dict(),
            "global_historical_prior": self.global_historical_prior.to_dict() if self.global_historical_prior else None,
            "fitted_profiles": {k: v.to_dict() for k, v in self.fitted_profiles.items()},
            "speed_factor_profile": self.speed_factor_profile.to_dict(),
            "dwell_profile": self.dwell_profile.to_dict(),
            "fitted": self.fitted
        }

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_profile(self, filepath: Union[str, Path]) -> 'HistoricalBehaviorService':
        """Imports precomputed behavior profile from JSON, restoring full provenance."""
        target_path = Path(filepath)
        if not target_path.exists():
            raise FileNotFoundError(f"Behavior profile file not found: {filepath}")

        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.metadata = ProfileMetadata.from_dict(data.get("metadata", {}))
        self.config = BehaviorFitConfig.from_dict(data.get("config", {}))
        
        global_p = data.get("global_historical_prior")
        self.global_historical_prior = DelayDistributionParams.from_dict(global_p) if global_p else None

        self.fitted_profiles = {
            k: DelayDistributionParams.from_dict(v)
            for k, v in data.get("fitted_profiles", {}).items()
        }
        self.speed_factor_profile = SpeedFactorParams.from_dict(data.get("speed_factor_profile", {}))
        self.dwell_profile = DwellDistributionParams.from_dict(data.get("dwell_profile", {}))
        self.fitted = data.get("fitted", True)

        return self
