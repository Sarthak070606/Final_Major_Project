"""
Phase 2 data preparation.

Investigates the known Phase 1 issues and produces a cleaned modelling
dataset WITHOUT deleting original Phase 1 files and WITHOUT converting
signed groundwater readings to absolute values.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from . import config_phase2 as cfg

logger = logging.getLogger(__name__)


def inspect_phase1() -> dict:
    """Load Phase 1 features and produce a quality report."""
    if not cfg.PHASE1_FEATURES.exists():
        raise FileNotFoundError(
            f"Phase 1 feature file not found: {cfg.PHASE1_FEATURES}\n"
            "Run Phase 1 successfully before starting Phase 2."
        )

    logger.info("Loading Phase 1 features (this may take a minute) ...")
    df = pd.read_parquet(cfg.PHASE1_FEATURES)
    logger.info("Loaded shape: %s", df.shape)

    report = {
        "n_rows": int(len(df)),
        "n_stations": int(df["station"].nunique()) if "station" in df.columns else 0,
        "columns": list(df.columns),
        "date_min": str(df["datetime"].min()) if "datetime" in df.columns else None,
        "date_max": str(df["datetime"].max()) if "datetime" in df.columns else None,
    }

    # Duplicate station-timestamp groups
    if {"station", "datetime"}.issubset(df.columns):
        dup_mask = df.duplicated(subset=["station", "datetime"], keep=False)
        report["n_duplicate_station_timestamp_rows"] = int(dup_mask.sum())
    else:
        report["n_duplicate_station_timestamp_rows"] = None

    # Extreme readings
    if "wl_raw" in df.columns:
        extreme = df["wl_raw"].abs() > cfg.MAX_PLAUSIBLE_ABS
        report["n_extreme_abs_gt_150"] = int(extreme.sum())
        report["wl_raw_median"] = float(df["wl_raw"].median())
        report["wl_raw_negative_pct"] = float((df["wl_raw"] < 0).mean() * 100)

    # Target presence
    if cfg.TARGET_COL in df.columns:
        report["n_missing_target"] = int(df[cfg.TARGET_COL].isna().sum())
    else:
        report["n_missing_target"] = None
        logger.warning("Target column %s not found", cfg.TARGET_COL)

    # Missing feature columns
    missing_feats = [c for c in cfg.FEATURE_COLS if c not in df.columns]
    report["missing_feature_columns"] = missing_feats

    logger.info("Inspection summary: %s", json.dumps(report, indent=2, default=str))
    return report, df


def clean_for_modelling(df: pd.DataFrame) -> pd.DataFrame:
    """
    Produce a modelling-ready dataset.

    Actions taken (all documented):
    - Keep only the first occurrence of exact station+datetime duplicates.
    - Flag (but keep) extreme magnitude readings.
    - Drop rows that still lack a target or any required feature.
    - Never convert wl_raw to absolute value.
    """
    df = df.copy()
    n_start = len(df)

    # 1. Resolve exact duplicates (keep first chronological occurrence)
    if {"station", "datetime"}.issubset(df.columns):
        before = len(df)
        df = df.sort_values(["station", "datetime"]).drop_duplicates(
            subset=["station", "datetime"], keep="first"
        )
        logger.info("Removed %d exact station-timestamp duplicates", before - len(df))

    # 2. Flag extremes (do not delete)
    if "wl_raw" in df.columns:
        df["flag_extreme_phase2"] = df["wl_raw"].abs() > cfg.MAX_PLAUSIBLE_ABS
        logger.info(
            "Flagged %d extreme readings (|wl| > %.0f m)",
            df["flag_extreme_phase2"].sum(),
            cfg.MAX_PLAUSIBLE_ABS,
        )

    # 3. Ensure required columns exist
    required = cfg.FEATURE_COLS + [cfg.TARGET_COL, "station", "datetime"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Required columns missing from Phase 1 output: {missing}")

    # 4. Drop rows that cannot be used for supervised learning
    before = len(df)
    df = df.dropna(subset=cfg.FEATURE_COLS + [cfg.TARGET_COL])
    # Replace remaining infinities
    df = df.replace([np.inf, -np.inf], np.nan).dropna(
        subset=cfg.FEATURE_COLS + [cfg.TARGET_COL]
    )
    logger.info("Dropped %d rows with missing/inf features or target", before - len(df))

    # 5. Final sort
    df = df.sort_values(["station", "datetime"]).reset_index(drop=True)

    logger.info(
        "Clean modelling dataset: %d rows (from %d) | %d stations",
        len(df), n_start, df["station"].nunique(),
    )
    return df


def run_preparation() -> pd.DataFrame:
    """Full preparation pipeline."""
    cfg.PHASE2_DIR.mkdir(parents=True, exist_ok=True)
    cfg.REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    report, df = inspect_phase1()

    # Save inspection report
    with open(cfg.REPORTS_DIR / "phase1_inspection.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    if report.get("missing_feature_columns"):
        raise RuntimeError(
            "Phase 1 feature matrix is missing required columns. "
            "Re-run Phase 1 or adjust FEATURE_COLS in config_phase2.py."
        )

    clean = clean_for_modelling(df)
    clean.to_parquet(cfg.CLEAN_FEATURES, index=False)
    logger.info("Saved cleaned features → %s", cfg.CLEAN_FEATURES)
    return clean


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
    run_preparation()
