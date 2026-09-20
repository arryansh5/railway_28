"""
Phase 5 Unit Tests: Historical Behavior Engine (unittest runner)
===============================================================

Tests compliance with all 20 Phase 5 requirements:
- No hardcoded magic constants.
- Provenance preservation for learned, derived, fallback, and unavailable states.
- Hierarchical backoff conditioning.
- Statistically reproducible stochastic sampling.
- Serialization and loading of complete profiles.
- Honest handling when data features are absent.
"""

import json
import os
import unittest
import numpy as np
import pandas as pd
import tempfile
from pathlib import Path

from src.simulator.historical_behavior_service import (
    HistoricalBehaviorService,
    BehaviorFitConfig,
    DelayDistributionParams,
    SpeedFactorParams,
    DwellDistributionParams,
    BehaviorQueryResult
)


class TestHistoricalBehaviorService(unittest.TestCase):

    def setUp(self):
        np.random.seed(42)
        n = 100
        data = {
            'train_number': np.random.choice(['12017', '12401', '14310'], size=n),
            'train_type': np.random.choice(['Superfast', 'Express'], size=n),
            'season': np.random.choice(['Monsoon', 'Winter'], size=n),
            'hour': np.random.choice([6, 12, 18], size=n),
            'is_fog_risk': np.random.choice([0, 1], size=n, p=[0.7, 0.3]),
            'late_incoming_rake': np.random.choice([0, 1], size=n, p=[0.8, 0.2]),
            'delay_minutes': np.random.exponential(scale=25.0, size=n) - 5.0
        }
        self.synthetic_kaggle_df = pd.DataFrame(data)

        n_sec = 50
        sec_data = {
            'section_id': ['SEC_NDLS_GZB'] * n_sec,
            'entry_speed_kmph': np.random.uniform(80.0, 100.0, size=n_sec),
            'max_sectional_speed_kmph': [110.0] * n_sec,
            'scheduled_dwell_min': [2.0] * n_sec,
            'actual_dwell_min': [2.0] * (n_sec - 10) + [7.0] * 10,
            'delay_minutes': np.random.normal(5.0, 3.0, size=n_sec)
        }
        self.section_logs_df = pd.DataFrame(sec_data)

    # Test 1: Global historical delay profile
    def test_1_global_historical_delay_profile(self):
        service = HistoricalBehaviorService()
        service.fit_from_dataframe(self.synthetic_kaggle_df)

        self.assertTrue(service.fitted)
        self.assertIsNotNone(service.global_historical_prior)
        self.assertEqual(service.global_historical_prior.data_origin, "learned")
        self.assertEqual(service.global_historical_prior.sample_count, 100)

    # Test 2: Train-type profile
    def test_2_train_type_profile(self):
        config = BehaviorFitConfig(min_group_samples=20)
        service = HistoricalBehaviorService(config=config)
        service.fit_from_dataframe(self.synthetic_kaggle_df)

        res = service.get_delay_distribution(train_type="Express")
        self.assertEqual(res.data_origin, "learned")
        self.assertIn("train_type", res.matched_level)
        self.assertFalse(res.fallback_occurred)

    # Test 3: Seasonal profile
    def test_3_seasonal_profile(self):
        config = BehaviorFitConfig(min_group_samples=20)
        service = HistoricalBehaviorService(config=config)
        service.fit_from_dataframe(self.synthetic_kaggle_df)

        res = service.get_delay_distribution(season="Winter")
        self.assertEqual(res.data_origin, "learned")
        self.assertIn("season", res.matched_level)

    # Test 4: Supported contextual profile
    def test_4_supported_contextual_profile(self):
        config = BehaviorFitConfig(min_group_samples=20)
        service = HistoricalBehaviorService(config=config)
        service.fit_from_dataframe(self.synthetic_kaggle_df)

        res = service.get_delay_distribution(train_type="Superfast", season="Winter")
        self.assertEqual(res.data_origin, "learned")
        self.assertIn("train_type+season", res.matched_level)

    # Test 5: Unsupported context query handling
    def test_5_unsupported_context(self):
        service = HistoricalBehaviorService()
        service.fit_from_dataframe(self.synthetic_kaggle_df)

        res = service.get_delay_distribution(unknown_feature="xyz_123")
        self.assertTrue(res.fallback_occurred)
        self.assertEqual(res.matched_level, "global_historical_prior")
        self.assertIn("unknown_feature", res.ignored_context)

    # Test 6: Insufficient sample fallback
    def test_6_insufficient_sample_fallback(self):
        config = BehaviorFitConfig(min_group_samples=200)
        service = HistoricalBehaviorService(config=config)
        service.fit_from_dataframe(self.synthetic_kaggle_df)

        res = service.get_delay_distribution(train_type="Superfast")
        self.assertTrue(res.fallback_occurred)
        self.assertEqual(res.matched_level, "global_historical_prior")

    # Test 7: Exact profile selection
    def test_7_exact_profile_selection(self):
        config = BehaviorFitConfig(min_group_samples=10)
        service = HistoricalBehaviorService(config=config)
        service.fit_from_dataframe(self.synthetic_kaggle_df)

        res = service.get_delay_distribution(train_type="Superfast", season="Winter", is_fog_risk=1)
        self.assertIsInstance(res, BehaviorQueryResult)
        self.assertIsNotNone(res.matched_key)

    # Test 8: Hierarchical fallback
    def test_8_hierarchical_fallback(self):
        config = BehaviorFitConfig(min_group_samples=20)
        service = HistoricalBehaviorService(config=config)
        service.fit_from_dataframe(self.synthetic_kaggle_df)

        res = service.get_delay_distribution(train_type="Superfast", season="NonExistentSeason")
        self.assertEqual(res.matched_level, "train_type")
        self.assertEqual(res.used_context, {"train_type": "Superfast"})

    # Test 9: Stochastic sampling
    def test_9_stochastic_sampling(self):
        service = HistoricalBehaviorService()
        service.fit_from_dataframe(self.synthetic_kaggle_df)

        delay, res = service.sample_delay(train_type="Express")
        self.assertIsInstance(delay, float)
        self.assertIsInstance(res, BehaviorQueryResult)

    # Test 10: Reproducible sampling using fixed RNG seed
    def test_10_reproducible_sampling_fixed_seed(self):
        service = HistoricalBehaviorService()
        service.fit_from_dataframe(self.synthetic_kaggle_df)

        rng1 = np.random.RandomState(42)
        delay1, _ = service.sample_delay(rng=rng1, train_type="Express")

        rng2 = np.random.RandomState(42)
        delay2, _ = service.sample_delay(rng=rng2, train_type="Express")

        self.assertAlmostEqual(delay1, delay2, places=5)

    # Test 11: Profile save and load
    def test_11_profile_save_and_load(self):
        service = HistoricalBehaviorService()
        service.fit_from_dataframe(self.synthetic_kaggle_df)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "profile.json"
            service.save_profile(filepath)
            self.assertTrue(filepath.exists())

            loaded_service = HistoricalBehaviorService(profile_filepath=filepath)
            self.assertTrue(loaded_service.fitted)
            self.assertEqual(loaded_service.metadata.source_dataset, "kaggle_train")

    # Test 12: Provenance preservation
    def test_12_provenance_preservation(self):
        service = HistoricalBehaviorService()
        service.fit_from_dataframe(self.synthetic_kaggle_df, source_name="kaggle_train_v1")

        res = service.get_delay_distribution(train_type="Express")
        self.assertIn(res.data_origin, ["learned", "fallback"])
        self.assertEqual(service.metadata.source_dataset, "kaggle_train_v1")

    # Test 13: No invented route profile when route data is unavailable
    def test_13_no_invented_route_profile(self):
        service = HistoricalBehaviorService()
        service.fit_from_dataframe(self.synthetic_kaggle_df)

        res = service.get_delay_distribution(route_id="ROUTE_NDLS_DDN_01")
        self.assertNotIn("route_id", res.used_context)
        self.assertTrue(res.fallback_occurred)

    # Test 14: No invented speed behavior when speed data is unavailable
    def test_14_no_invented_speed_behavior(self):
        service = HistoricalBehaviorService()
        service.fit_from_dataframe(self.synthetic_kaggle_df)

        sp_profile = service.get_speed_factor_distribution()
        self.assertEqual(sp_profile.data_origin, "unavailable")
        self.assertIn("unavailable", sp_profile.status_message.lower())

    # Test 15: No invented dwell behavior when dwell data is unavailable
    def test_15_no_invented_dwell_behavior(self):
        service = HistoricalBehaviorService()
        service.fit_from_dataframe(self.synthetic_kaggle_df)

        dw_profile = service.get_dwell_distribution()
        self.assertEqual(dw_profile.data_origin, "unavailable")
        self.assertIn("unavailable", dw_profile.status_message.lower())

    # Test 16: Profile fitting only on supplied training data
    def test_16_profile_fitting_only_supplied_data(self):
        train_part = self.synthetic_kaggle_df.iloc[:50]

        service = HistoricalBehaviorService()
        service.fit_from_dataframe(train_part)

        self.assertEqual(service.metadata.total_samples_fitted, 50)

    # Test 17: Correct handling of empty / invalid data
    def test_17_handling_empty_data(self):
        service = HistoricalBehaviorService()
        with self.assertRaises(ValueError):
            service.fit_from_dataframe(pd.DataFrame())

    # Test 18: Filepath save behavior without parent dir issue
    def test_18_filepath_save_behavior(self):
        service = HistoricalBehaviorService()
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "sub" / "dir" / "profile.json"
            service.save_profile(nested_path)
            self.assertTrue(nested_path.exists())

    # Test 19: Documentation and travel time calculation consistency
    def test_19_travel_time_calculation_consistency(self):
        service = HistoricalBehaviorService()
        service.fit_from_dataframe(self.synthetic_kaggle_df)

        res = service.get_travel_time_distribution(scheduled_travel_min=120.0, train_type="Express")
        self.assertEqual(res["scheduled_travel_min"], 120.0)
        self.assertGreaterEqual(res["expected_actual_travel_min"], 120.0 + res["delay_query_result"].distribution.mean_delay_min - 1e-5)

    # Test 20: No hardcoded behavioral adjustments remain
    def test_20_no_hardcoded_behavioral_constants(self):
        config = BehaviorFitConfig(min_group_samples=10)
        service = HistoricalBehaviorService(config=config)
        service.fit_from_dataframe(self.section_logs_df)

        sp_profile = service.get_speed_factor_distribution()
        dw_profile = service.get_dwell_distribution()

        self.assertEqual(sp_profile.data_origin, "learned")
        self.assertEqual(dw_profile.data_origin, "learned")
        self.assertGreater(sp_profile.mean_speed_factor, 0.0)
        self.assertGreater(dw_profile.mean_dwell_min, 0.0)


if __name__ == "__main__":
    unittest.main()
