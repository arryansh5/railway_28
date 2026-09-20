"""
Kaggle Baseline Evaluation Script — Project Supernova (Phase 2)

Evaluates multi-tier baseline models on the historical Kaggle dataset:
1. Target 1: delay_minutes (Continuous Regression)
2. Target 2: is_delayed (Binary Classification)

Validation strategies:
- 80/20 Stratified Random Split
- Chronological Out-of-Time Split (Train: 2018-2023, Test: 2024)
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    median_absolute_error,
    r2_score,
    accuracy_score,
    roc_auc_score,
    f1_score,
    precision_score,
    recall_score
)
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.preprocessing import OrdinalEncoder, StandardScaler


def load_and_preprocess_data(csv_path: str = "indian-railways-predict-train-delay/ir_train.csv"):
    print(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Drop single corrupted null row
    df = df.dropna(subset=["delay_minutes", "is_delayed"]).reset_index(drop=True)
    
    # Parse dates
    df["departure_date"] = pd.to_datetime(df["departure_date"], format="mixed")
    df["year"] = df["departure_date"].dt.year
    df["month"] = df["departure_date"].dt.month
    df["day_of_week"] = df["departure_date"].dt.dayofweek
    
    # Drop non-feature and target leakage columns
    drop_cols = [
        "journey_id",
        "departure_date",
        "primary_delay_cause",   # Post-outcome target leakage
        "is_overloaded",          # Zero variance
        "delay_minutes",         # Target
        "is_delayed"             # Target
    ]
    
    feature_cols = [c for c in df.columns if c not in drop_cols]
    
    # Identify categorical vs numeric
    cat_cols = [
        "train_number", "train_type", "season", "zone", "zone_abbr",
        "source_station_category", "destination_station_category",
        "traction_type"
    ]
    
    num_cols = [c for c in feature_cols if c not in cat_cols]
    
    X = df[feature_cols].copy()
    
    # Encode categorical columns with OrdinalEncoder (handles high cardinality)
    for col in cat_cols:
        X[col] = X[col].astype(str)
        encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
        X[col] = encoder.fit_transform(X[[col]])
        
    y_reg = df["delay_minutes"].values
    y_clf = df["is_delayed"].values
    years = df["year"].values
    
    return X, y_reg, y_clf, years, feature_cols


def evaluate_baselines():
    X, y_reg, y_clf, years, feature_cols = load_and_preprocess_data()
    print(f"Processed dataset: {X.shape[0]} rows, {X.shape[1]} features.")
    
    results = {
        "random_split_80_20": {},
        "chronological_split_2024": {}
    }
    
    # =========================================================================
    # 1. 80/20 STRATIFIED RANDOM SPLIT
    # =========================================================================
    print("\n" + "=" * 60)
    print("RUNNING 80/20 STRATIFIED SPLIT BENCHMARK")
    print("=" * 60)
    
    X_train, X_val, y_reg_train, y_reg_val, y_clf_train, y_clf_val = train_test_split(
        X, y_reg, y_clf, test_size=0.20, random_state=42, stratify=y_clf
    )
    
    print(f"Train size: {len(X_train)} | Val size: {len(X_val)}")
    
    # Scale for linear models
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    
    # --- Regression Baseline 0: Naive Zero / Schedule (Timetable on-time) ---
    pred_naive_reg = np.zeros_like(y_reg_val)
    pred_mean_reg = np.full_like(y_reg_val, fill_value=np.mean(y_reg_train))
    
    results["random_split_80_20"]["naive_zero_delay"] = {
        "mae": float(mean_absolute_error(y_reg_val, pred_naive_reg)),
        "rmse": float(np.sqrt(mean_squared_error(y_reg_val, pred_naive_reg))),
        "medae": float(median_absolute_error(y_reg_val, pred_naive_reg)),
        "r2": float(r2_score(y_reg_val, pred_naive_reg))
    }
    
    results["random_split_80_20"]["naive_mean_delay"] = {
        "mae": float(mean_absolute_error(y_reg_val, pred_mean_reg)),
        "rmse": float(np.sqrt(mean_squared_error(y_reg_val, pred_mean_reg))),
        "medae": float(median_absolute_error(y_reg_val, pred_mean_reg)),
        "r2": float(r2_score(y_reg_val, pred_mean_reg))
    }
    
    # --- Classification Baseline 0: Majority Class (All On-Time = 0) ---
    pred_naive_clf = np.zeros_like(y_clf_val)
    results["random_split_80_20"]["naive_majority_class"] = {
        "accuracy": float(accuracy_score(y_clf_val, pred_naive_clf)),
        "roc_auc": 0.5,
        "f1": 0.0,
        "precision": 0.0,
        "recall": 0.0
    }
    
    # --- Regression Baseline 1: Ridge Linear Model ---
    print("Training Ridge Regressor...")
    ridge = Ridge(alpha=10.0)
    ridge.fit(X_train_scaled, y_reg_train)
    pred_ridge = np.clip(ridge.predict(X_val_scaled), 0, None)
    
    results["random_split_80_20"]["ridge_regression"] = {
        "mae": float(mean_absolute_error(y_reg_val, pred_ridge)),
        "rmse": float(np.sqrt(mean_squared_error(y_reg_val, pred_ridge))),
        "medae": float(median_absolute_error(y_reg_val, pred_ridge)),
        "r2": float(r2_score(y_reg_val, pred_ridge))
    }
    
    # --- Classification Baseline 1: Logistic Regression ---
    print("Training Logistic Classifier...")
    logreg = LogisticRegression(max_iter=500, random_state=42)
    logreg.fit(X_train_scaled, y_clf_train)
    pred_logreg = logreg.predict(X_val_scaled)
    prob_logreg = logreg.predict_proba(X_val_scaled)[:, 1]
    
    results["random_split_80_20"]["logistic_regression"] = {
        "accuracy": float(accuracy_score(y_clf_val, pred_logreg)),
        "roc_auc": float(roc_auc_score(y_clf_val, prob_logreg)),
        "f1": float(f1_score(y_clf_val, pred_logreg)),
        "precision": float(precision_score(y_clf_val, pred_logreg)),
        "recall": float(recall_score(y_clf_val, pred_logreg))
    }
    
    # --- Regression Baseline 2: HistGradientBoosting Regressor ---
    print("Training Gradient Boosted Regressor (XGBoost/GBDT Equivalent)...")
    gbr = HistGradientBoostingRegressor(max_iter=150, max_depth=8, learning_rate=0.08, random_state=42)
    gbr.fit(X_train, y_reg_train)
    pred_gbr = np.clip(gbr.predict(X_val), 0, None)
    
    results["random_split_80_20"]["gradient_boosting_regressor"] = {
        "mae": float(mean_absolute_error(y_reg_val, pred_gbr)),
        "rmse": float(np.sqrt(mean_squared_error(y_reg_val, pred_gbr))),
        "medae": float(median_absolute_error(y_reg_val, pred_gbr)),
        "r2": float(r2_score(y_reg_val, pred_gbr))
    }
    
    # --- Classification Baseline 2: HistGradientBoosting Classifier ---
    print("Training Gradient Boosted Classifier (XGBoost/GBDT Equivalent)...")
    gbc = HistGradientBoostingClassifier(max_iter=150, max_depth=8, learning_rate=0.08, random_state=42)
    gbc.fit(X_train, y_clf_train)
    pred_gbc = gbc.predict(X_val)
    prob_gbc = gbc.predict_proba(X_val)[:, 1]
    
    results["random_split_80_20"]["gradient_boosting_classifier"] = {
        "accuracy": float(accuracy_score(y_clf_val, pred_gbc)),
        "roc_auc": float(roc_auc_score(y_clf_val, prob_gbc)),
        "f1": float(f1_score(y_clf_val, pred_gbc)),
        "precision": float(precision_score(y_clf_val, pred_gbc)),
        "recall": float(recall_score(y_clf_val, pred_gbc))
    }
    
    # =========================================================================
    # 2. CHRONOLOGICAL OUT-OF-TIME SPLIT (2018-2023 vs 2024)
    # =========================================================================
    print("\n" + "=" * 60)
    print("RUNNING CHRONOLOGICAL OUT-OF-TIME SPLIT (2018-2023 Train vs 2024 Test)")
    print("=" * 60)
    
    train_mask = (years < 2024)
    test_mask = (years == 2024)
    
    X_train_time, X_test_time = X[train_mask], X[test_mask]
    y_reg_train_time, y_reg_test_time = y_reg[train_mask], y_reg[test_mask]
    y_clf_train_time, y_clf_test_time = y_clf[train_mask], y_clf[test_mask]
    
    print(f"Historical Train (2018-2023): {len(X_train_time)} rows")
    print(f"Out-of-Time Test (2024): {len(X_test_time)} rows")
    
    gbr_time = HistGradientBoostingRegressor(max_iter=150, max_depth=8, learning_rate=0.08, random_state=42)
    gbr_time.fit(X_train_time, y_reg_train_time)
    pred_gbr_time = np.clip(gbr_time.predict(X_test_time), 0, None)
    
    results["chronological_split_2024"]["gradient_boosting_regressor"] = {
        "mae": float(mean_absolute_error(y_reg_test_time, pred_gbr_time)),
        "rmse": float(np.sqrt(mean_squared_error(y_reg_test_time, pred_gbr_time))),
        "medae": float(median_absolute_error(y_reg_test_time, pred_gbr_time)),
        "r2": float(r2_score(y_reg_test_time, pred_gbr_time))
    }
    
    gbc_time = HistGradientBoostingClassifier(max_iter=150, max_depth=8, learning_rate=0.08, random_state=42)
    gbc_time.fit(X_train_time, y_clf_train_time)
    pred_gbc_time = gbc_time.predict(X_test_time)
    prob_gbc_time = gbc_time.predict_proba(X_test_time)[:, 1]
    
    results["chronological_split_2024"]["gradient_boosting_classifier"] = {
        "accuracy": float(accuracy_score(y_clf_test_time, pred_gbc_time)),
        "roc_auc": float(roc_auc_score(y_clf_test_time, prob_gbc_time)),
        "f1": float(f1_score(y_clf_test_time, pred_gbc_time)),
        "precision": float(precision_score(y_clf_test_time, pred_gbc_time)),
        "recall": float(recall_score(y_clf_test_time, pred_gbc_time))
    }
    
    # Save benchmark JSON
    os.makedirs("reports", exist_ok=True)
    with open("reports/kaggle_baseline_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print("\nBenchmark results saved to reports/kaggle_baseline_results.json")
    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    evaluate_baselines()
