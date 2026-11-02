
"""
Chronological train / validation / test split
for groundwater-level forecasting.

Input:
    features_clean_v2.parquet

Split:
    70% Training
    15% Validation
    15% Testing

Uses global chronological cutoffs.
"""

from __future__ import annotations

import json
import logging

import pandas as pd

from . import config_phase2 as cfg

logger = logging.getLogger(__name__)


def chronological_split(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    required_columns = [
        "station",
        "datetime",
        cfg.TARGET_COL,
        *cfg.FEATURE_COLS,
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    if df.empty:
        raise ValueError("Input dataset is empty.")

    df = df.copy()

    df["datetime"] = pd.to_datetime(
        df["datetime"], errors="raise"
    )

    if df["datetime"].isna().any():
        raise ValueError("Datetime contains missing values.")

    if df[cfg.TARGET_COL].isna().any():
        raise ValueError("Target contains missing values.")

    if not 0 < cfg.TRAIN_RATIO < 1:
        raise ValueError("Invalid TRAIN_RATIO.")

    if not 0 < cfg.VAL_RATIO < 1:
        raise ValueError("Invalid VAL_RATIO.")

    if cfg.TRAIN_RATIO + cfg.VAL_RATIO >= 1:
        raise ValueError("Train and validation ratios must sum to less than 1.")

    # Global chronological ordering
    df = df.sort_values(
        ["datetime", "station"]
    ).reset_index(drop=True)

    t_min = df["datetime"].min()
    t_max = df["datetime"].max()

    logger.info("Full date range: %s to %s", t_min, t_max)

    # Global time cutoffs
    q_train = df["datetime"].quantile(
        cfg.TRAIN_RATIO
    )

    q_val = df["datetime"].quantile(
        cfg.TRAIN_RATIO + cfg.VAL_RATIO
    )

    train = df[df["datetime"] <= q_train].copy()

    val = df[
        (df["datetime"] > q_train)
        & (df["datetime"] <= q_val)
    ].copy()

    test = df[
        df["datetime"] > q_val
    ].copy()

    if train.empty or val.empty or test.empty:
        raise ValueError(
            "One or more splits are empty."
        )

    # Verify strict chronological separation
    if not train["datetime"].max() < val["datetime"].min():
        raise ValueError("Train/validation chronology failed.")

    if not val["datetime"].max() < test["datetime"].min():
        raise ValueError("Validation/test chronology failed.")

    # Verify station coverage
    train_stations = set(train["station"].unique())
    val_stations = set(val["station"].unique())
    test_stations = set(test["station"].unique())

    boundaries = {
        "input_file": str(cfg.CLEAN_FEATURES),
        "train_ratio": cfg.TRAIN_RATIO,
        "validation_ratio": cfg.VAL_RATIO,
        "test_ratio": 1 - cfg.TRAIN_RATIO - cfg.VAL_RATIO,

        "full_start": str(t_min),
        "full_end": str(t_max),

        "train_start": str(train["datetime"].min()),
        "train_end": str(train["datetime"].max()),

        "validation_start": str(val["datetime"].min()),
        "validation_end": str(val["datetime"].max()),

        "test_start": str(test["datetime"].min()),
        "test_end": str(test["datetime"].max()),

        "n_train": len(train),
        "n_validation": len(val),
        "n_test": len(test),

        "n_stations_train": len(train_stations),
        "n_stations_validation": len(val_stations),
        "n_stations_test": len(test_stations),

        "chronological_validation": "PASSED",
    }

    # Create output directory
    cfg.PHASE2_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Prevent accidental overwriting
    output_files = [
        cfg.SPLIT_INFO,
        cfg.TRAIN_FILE,
        cfg.VAL_FILE,
        cfg.TEST_FILE,
    ]

    existing = [
        str(path) for path in output_files
        if path.exists()
    ]

    if existing:
        raise FileExistsError(
            "Existing split files found. "
            "Review or back them up before rerunning: "
            + ", ".join(existing)
        )

    # Save split information
    with open(
        cfg.SPLIT_INFO,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(boundaries, f, indent=2)

    train.to_parquet(cfg.TRAIN_FILE, index=False)
    val.to_parquet(cfg.VAL_FILE, index=False)
    test.to_parquet(cfg.TEST_FILE, index=False)

    logger.info("Chronological split successful.")

    logger.info(
        "Train: %d rows | %d stations",
        len(train), len(train_stations)
    )

    logger.info(
        "Validation: %d rows | %d stations",
        len(val), len(val_stations)
    )

    logger.info(
        "Test: %d rows | %d stations",
        len(test), len(test_stations)
    )

    logger.info("Split boundaries saved to %s", cfg.SPLIT_INFO)

    return train, val, test


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

    logger.info("Loading validated Phase 2 dataset...")

    if not cfg.CLEAN_FEATURES.exists():
        raise FileNotFoundError(
            f"Dataset not found: {cfg.CLEAN_FEATURES}"
        )

    df = pd.read_parquet(cfg.CLEAN_FEATURES)

    logger.info("Loaded dataset: %s", df.shape)

    chronological_split(df)
