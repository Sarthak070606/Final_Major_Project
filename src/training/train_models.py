
"""
Groundwater Level Forecasting - Model Training Pipeline

Features:
- Persistence baseline
- Linear and regularized regression
- Decision Tree and ensemble models
- Optional XGBoost, CatBoost and LightGBM
- Validation-based model selection
- One-time final test evaluation
- Memory-conscious training for large datasets

IMPORTANT:
Current v2 target represents the next available observation,
not necessarily an observation exactly six hours later.
"""

from __future__ import annotations

import json
import logging
import time
import gc

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import (
    RandomForestRegressor,
    ExtraTreesRegressor,
    HistGradientBoostingRegressor,
    GradientBoostingRegressor,
    AdaBoostRegressor,
)
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

from . import config_phase2 as cfg


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

MAX_TRAIN_ROWS = 250_000
MAX_VAL_ROWS = None

N_JOBS = 2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# --------------------------------------------------
# METRICS
# --------------------------------------------------

def calculate_metrics(y_true, y_pred):

    return {
        "mae": float(
            mean_absolute_error(y_true, y_pred)
        ),
        "rmse": float(
            np.sqrt(mean_squared_error(y_true, y_pred))
        ),
        "r2": float(
            r2_score(y_true, y_pred)
        ),
        "n": int(len(y_true)),
    }


# --------------------------------------------------
# OPTIONAL MODELS
# --------------------------------------------------

def build_models():

    models = {

        "linear": LinearRegression(),

        "ridge": Ridge(
            alpha=1.0
        ),

        "decision_tree": DecisionTreeRegressor(
            max_depth=8,
            random_state=cfg.RANDOM_SEED,
        ),

        "random_forest": RandomForestRegressor(
            n_estimators=30,
            max_depth=10,
            max_samples=0.5,
            n_jobs=N_JOBS,
            random_state=cfg.RANDOM_SEED,
        ),

        "extra_trees": ExtraTreesRegressor(
            n_estimators=30,
            max_depth=10,
            max_samples=0.5,
            n_jobs=N_JOBS,
            random_state=cfg.RANDOM_SEED,
        ),

        "hist_gradient_boosting": HistGradientBoostingRegressor(
            max_iter=50,
            max_depth=6,
            learning_rate=0.1,
            random_state=cfg.RANDOM_SEED,
        ),

        "adaboost": AdaBoostRegressor(
            n_estimators=30,
            random_state=cfg.RANDOM_SEED,
        ),

        "gradient_boosting": GradientBoostingRegressor(
            n_estimators=30,
            max_depth=3,
            random_state=cfg.RANDOM_SEED,
        ),
    }

    # XGBoost
    try:

        from xgboost import XGBRegressor

        models["xgboost"] = XGBRegressor(
            n_estimators=50,
            max_depth=5,
            learning_rate=0.08,
            n_jobs=N_JOBS,
            random_state=cfg.RANDOM_SEED,
            verbosity=0,
        )

    except ImportError:
        logger.warning("XGBoost not installed. Skipping.")

    # CatBoost
    try:

        from catboost import CatBoostRegressor

        models["catboost"] = CatBoostRegressor(
            iterations=50,
            depth=5,
            learning_rate=0.08,
            random_seed=cfg.RANDOM_SEED,
            verbose=0,
            thread_count=N_JOBS,
        )

    except ImportError:
        logger.warning("CatBoost not installed. Skipping.")

    # LightGBM
    try:

        from lightgbm import LGBMRegressor

        models["lightgbm"] = LGBMRegressor(
            n_estimators=50,
            max_depth=5,
            learning_rate=0.08,
            n_jobs=N_JOBS,
            random_state=cfg.RANDOM_SEED,
            verbosity=-1,
        )

    except ImportError:
        logger.warning("LightGBM not installed. Skipping.")

    return models


# --------------------------------------------------
# DATA VALIDATION
# --------------------------------------------------

def validate_dataset(df, name, required):

    if df.empty:
        raise ValueError(f"{name} dataset is empty.")

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"{name} dataset is missing columns: {missing}"
        )

    values = df[required].to_numpy(
        dtype=np.float64,
        copy=False,
    )

    if not np.isfinite(values).all():
        raise ValueError(
            f"{name} contains NaN or infinite feature/target values."
        )

    logger.info(
        "%s dataset validated: %s",
        name,
        df.shape,
    )


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

def load_training_data():

    for path in [
        cfg.TRAIN_FILE,
        cfg.VAL_FILE,
        cfg.TEST_FILE,
    ]:

        if not path.exists():
            raise FileNotFoundError(
                f"Required dataset not found: {path}"
            )

    logger.info("Loading training dataset...")

    train = pd.read_parquet(cfg.TRAIN_FILE)

    logger.info("Loading validation dataset...")

    val = pd.read_parquet(cfg.VAL_FILE)

    required = cfg.FEATURE_COLS + [
        cfg.TARGET_COL
    ]

    validate_dataset(
        train,
        "Training",
        required,
    )

    validate_dataset(
        val,
        "Validation",
        required,
    )

    # Deterministic training sample.
    # All models receive the same training rows.

    if len(train) > MAX_TRAIN_ROWS:

        logger.info(
            "Sampling %d rows from %d training rows.",
            MAX_TRAIN_ROWS,
            len(train),
        )

        train = train.sample(
            n=MAX_TRAIN_ROWS,
            random_state=cfg.RANDOM_SEED,
        )

    if MAX_VAL_ROWS is not None and len(val) > MAX_VAL_ROWS:

        val = val.sample(
            n=MAX_VAL_ROWS,
            random_state=cfg.RANDOM_SEED,
        )

    X_train = train[cfg.FEATURE_COLS].astype("float32")
    y_train = train[cfg.TARGET_COL].astype("float32")

    X_val = val[cfg.FEATURE_COLS].astype("float32")
    y_val = val[cfg.TARGET_COL].astype("float32")

    logger.info(
        "Final training rows: %d",
        len(X_train),
    )

    logger.info(
        "Final validation rows: %d",
        len(X_val),
    )

    return X_train, y_train, X_val, y_val, required


# --------------------------------------------------
# TRAIN MODELS
# --------------------------------------------------

def train_models(X_train, y_train, X_val, y_val):

    results = []

    best_name = None
    best_model = None
    best_mae = float("inf")

    models = build_models()

    for name, model in models.items():

        logger.info("=" * 55)
        logger.info("Training model: %s", name)

        start = time.time()

        try:

            model.fit(
                X_train,
                y_train,
            )

            prediction = model.predict(
                X_val
            )

            val_metrics = calculate_metrics(
                y_val,
                prediction,
            )

            elapsed = round(
                time.time() - start,
                2,
            )

            results.append({
                "model": name,
                **val_metrics,
                "training_seconds": elapsed,
                "status": "success",
            })

            logger.info(
                "%s | MAE: %.5f | RMSE: %.5f | R2: %.5f | Time: %.1fs",
                name,
                val_metrics["mae"],
                val_metrics["rmse"],
                val_metrics["r2"],
                elapsed,
            )

            if val_metrics["mae"] < best_mae:

                best_mae = val_metrics["mae"]
                best_name = name
                best_model = model

        except Exception as error:

            logger.exception(
                "Model %s failed: %s",
                name,
                error,
            )

            results.append({
                "model": name,
                "mae": None,
                "rmse": None,
                "r2": None,
                "n": 0,
                "training_seconds": round(
                    time.time() - start,
                    2,
                ),
                "status": "failed",
            })

        gc.collect()

    if best_model is None:
        raise RuntimeError(
            "All machine learning models failed."
        )

    return best_name, best_model, results


# --------------------------------------------------
# PERSISTENCE BASELINE
# --------------------------------------------------

def evaluate_persistence(X_val, y_val):

    prediction = X_val["wl_raw"].to_numpy()

    result = calculate_metrics(
        y_val,
        prediction,
    )

    result.update({
        "model": "persistence",
        "training_seconds": 0.0,
        "status": "baseline",
    })

    return result


# --------------------------------------------------
# FINAL TEST EVALUATION
# --------------------------------------------------

def evaluate_test(best_model, best_name, required):

    logger.info(
        "Loading test dataset for final evaluation..."
    )

    test = pd.read_parquet(
        cfg.TEST_FILE
    )

    validate_dataset(
        test,
        "Test",
        required,
    )

    X_test = test[
        cfg.FEATURE_COLS
    ].astype("float32")

    y_test = test[
        cfg.TARGET_COL
    ].astype("float32")

    prediction = best_model.predict(
        X_test
    )

    test_metrics = calculate_metrics(
        y_test,
        prediction,
    )

    report = {
        "selected_model": best_name,
        "test_metrics": test_metrics,
        "forecast_horizon": (
            "Next available observation; "
            "not guaranteed to be exactly six hours."
        ),
    }

    with open(
        cfg.TEST_REPORT,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=4,
        )

    logger.info("Final test evaluation completed.")

    print("\nFINAL TEST RESULTS")
    print(json.dumps(report, indent=4))

    del test, X_test, y_test, prediction
    gc.collect()

    return report


# --------------------------------------------------
# MAIN PIPELINE
# --------------------------------------------------

def train_and_evaluate():

    cfg.MODELS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    cfg.REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    logger.info("Starting groundwater model training.")

    (
        X_train,
        y_train,
        X_val,
        y_val,
        required,
    ) = load_training_data()

    # Persistence baseline
    baseline = evaluate_persistence(
        X_val,
        y_val,
    )

    logger.info(
        "Persistence baseline MAE: %.5f",
        baseline["mae"],
    )

    # Train ML models
    best_name, best_model, results = train_models(
        X_train,
        y_train,
        X_val,
        y_val,
    )

    results.append(baseline)

    comparison = pd.DataFrame(
        results
    )

    comparison = comparison.sort_values(
        "mae",
        na_position="last",
    )

    comparison.to_csv(
        cfg.COMPARISON_CSV,
        index=False,
    )

    print("\nVALIDATION MODEL COMPARISON")
    print(comparison.to_string(index=False))

    # Save best ML model
    joblib.dump(
        best_model,
        cfg.BEST_MODEL_PATH,
    )

    metadata = {
        "best_model_name": best_name,
        "feature_columns": cfg.FEATURE_COLS,
        "target_column": cfg.TARGET_COL,
        "validation_mae": best_name and float(
            comparison.loc[
                comparison["model"] == best_name,
                "mae",
            ].iloc[0]
        ),
        "random_seed": cfg.RANDOM_SEED,
        "training_sample_limit": MAX_TRAIN_ROWS,
        "training_rows_used": len(X_train),
        "validation_rows_used": len(X_val),
        "forecast_horizon": (
            "Next available observation; "
            "not guaranteed to be exactly six hours."
        ),
    }

    with open(
        cfg.MODEL_META_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata,
            file,
            indent=4,
        )

    logger.info(
        "Best model saved: %s",
        cfg.BEST_MODEL_PATH,
    )

    # Release training memory before test evaluation.
    del X_train, y_train, X_val, y_val
    gc.collect()

    # Evaluate test exactly once.
    evaluate_test(
        best_model,
        best_name,
        required,
    )

    print("\n" + "=" * 55)
    print("GROUNDWATER MODEL TRAINING COMPLETED")
    print("=" * 55)

    print("Best model:", best_name)
    print("Model file:", cfg.BEST_MODEL_PATH)
    print("Comparison:", cfg.COMPARISON_CSV)
    print("Test report:", cfg.TEST_REPORT)


# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    train_and_evaluate()
