
"""
Hybrid Groundwater Prediction Pipeline
Known stations: Random Forest
Unseen stations: Persistence baseline

Uses the existing trained Random Forest model.
Does not overwrite the original model.
"""

import os
import json
import logging
import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

from src.training.config_phase2 import FEATURE_COLS, TARGET_COL


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

TRAIN_PATH = "data/processed/phase2/train.parquet"
TEST_PATH = "data/processed/phase2/test.parquet"

OLD_MODEL_PATH = "models/best_model.joblib"

OUTPUT_DIR = "models/hybrid"
REPORT_DIR = "reports/hybrid"

HYBRID_MODEL_PATH = os.path.join(
    OUTPUT_DIR, "hybrid_model.joblib"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# --------------------------------------------------
# METRICS
# --------------------------------------------------

def calculate_metrics(actual, predicted):

    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(
            mean_squared_error(actual, predicted)
        )),
        "r2": float(r2_score(actual, predicted)),
        "records": int(len(actual))
    }


# --------------------------------------------------
# MAIN PIPELINE
# --------------------------------------------------

def main():

    logger.info("Starting hybrid groundwater pipeline.")

    # Load training station names
    logger.info("Loading training station information...")

    train_stations = pd.read_parquet(
        TRAIN_PATH,
        columns=["station"]
    )

    known_stations = set(
        train_stations["station"].dropna().unique()
    )

    logger.info(
        "Known training stations: %s",
        len(known_stations)
    )

    del train_stations

    # Load existing model
    logger.info("Loading existing Random Forest model...")

    rf_model = joblib.load(OLD_MODEL_PATH)

    # Load test data
    logger.info("Loading test dataset...")

    test = pd.read_parquet(TEST_PATH)

    X_df = test[FEATURE_COLS]
    y = test[TARGET_COL].to_numpy(dtype=np.float64)

    X = X_df.to_numpy(dtype=np.float64)

    # Identify station groups
    station_values = test["station"].to_numpy()

    known_mask = np.isin(
        station_values,
        list(known_stations)
    )

    unseen_mask = ~known_mask

    # Quality filter for diagnostic evaluation
    quality_mask = (
        np.isfinite(y)
        & (np.abs(y) <= 150)
        & np.isfinite(X).all(axis=1)
    )

    groundwater_features = [
        c for c in FEATURE_COLS
        if c.startswith(("wl_", "lag_", "rolling_"))
    ]

    for col in groundwater_features:
        values = test[col].to_numpy(dtype=np.float64)

        quality_mask &= (
            np.isfinite(values)
            & (np.abs(values) <= 150)
        )

    logger.info(
        "Quality-filtered records: %s",
        int(quality_mask.sum())
    )

    # Persistence prediction
    current_wl_index = FEATURE_COLS.index("wl_raw")
    persistence_predictions = X[:, current_wl_index]

    # Random Forest prediction
    logger.info("Generating Random Forest predictions...")

    rf_predictions = rf_model.predict(X)

    # Hybrid prediction
    hybrid_predictions = np.where(
        known_mask,
        rf_predictions,
        persistence_predictions
    )

    # Evaluate
    results = {}

    groups = {
        "all": quality_mask,
        "known_stations": quality_mask & known_mask,
        "unseen_stations": quality_mask & unseen_mask
    }

    for group_name, mask in groups.items():

        if mask.sum() == 0:
            continue

        actual = y[mask]

        results[group_name] = {
            "random_forest": calculate_metrics(
                actual,
                rf_predictions[mask]
            ),
            "persistence": calculate_metrics(
                actual,
                persistence_predictions[mask]
            ),
            "hybrid": calculate_metrics(
                actual,
                hybrid_predictions[mask]
            )
        }

    # Print results
    print("\n========== HYBRID MODEL RESULTS ==========")

    for group_name, group_results in results.items():

        print(f"\n{group_name.upper()}")

        for model_name, metrics in group_results.items():

            print(
                f"{model_name:15s} | "
                f"MAE: {metrics['mae']:.5f} | "
                f"RMSE: {metrics['rmse']:.5f} | "
                f"R2: {metrics['r2']:.5f}"
            )

    # Save hybrid artifact
    artifact = {
        "model": rf_model,
        "known_stations": known_stations,
        "feature_cols": FEATURE_COLS,
        "target_col": TARGET_COL,
        "known_station_method": "random_forest",
        "unseen_station_method": "persistence",
        "forecast_horizon": (
            "Next available observation; "
            "not guaranteed to be exactly six hours."
        )
    }

    joblib.dump(artifact, HYBRID_MODEL_PATH)

    # Save report
    report = {
        "known_station_count": len(known_stations),
        "test_record_count": len(test),
        "quality_filtered_record_count": int(
            quality_mask.sum()
        ),
        "known_test_records": int(
            (quality_mask & known_mask).sum()
        ),
        "unseen_test_records": int(
            (quality_mask & unseen_mask).sum()
        ),
        "results": results
    }

    report_path = os.path.join(
        REPORT_DIR,
        "hybrid_evaluation.json"
    )

    with open(report_path, "w") as f:
        json.dump(report, f, indent=4)

    print("\n==========================================")
    print("HYBRID PIPELINE COMPLETED")
    print("Model:", HYBRID_MODEL_PATH)
    print("Report:", report_path)
    print("==========================================")


if __name__ == "__main__":
    main()
