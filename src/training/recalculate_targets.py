"""
Phase 2 target realignment and feature recalculation.

Problem addressed
-----------------
After cleaning / deduplication the original target_wl_t_plus_1 column
(created in Phase 1) no longer matches the true next chronological
observation for many rows.

Solution
--------
1. Load the cleaned Phase-2 dataset (or the Phase-1 features if needed).
2. Resolve any remaining station-timestamp duplicates with a documented rule.
3. Sort strictly by station + datetime.
4. For every station, recalculate:
   - target_wl_t_plus_1  = next observation's wl_raw  (last row → NaN)
   - lag features        (shift of wl_raw)
   - trailing rolling statistics
5. Drop rows that still lack a complete feature vector or a target.
6. Save as features_clean_v2.parquet (never overwrite previous files).
7. Preserve signed wl_raw and extreme-value flags.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Paths (relative to project root)
# ---------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PHASE2_DIR   = PROJECT_ROOT / "data" / "processed" / "phase2"

# Prefer the already-cleaned file; fall back to Phase-1 features
INPUT_CANDIDATES = [
    PHASE2_DIR / "features_clean.parquet",
    PROJECT_ROOT / "data" / "processed" / "features_lag_rolling.parquet",
]
OUTPUT_V2 = PHASE2_DIR / "features_clean_v2.parquet"
REPORT    = PROJECT_ROOT / "reports" / "phase2" / "target_realignment_report.json"

LAG_STEPS       = [1, 4, 28, 120]
ROLLING_WINDOWS = [4, 28, 120]
MAX_PLAUSIBLE   = 150.0


def find_input() -> Path:
    for p in INPUT_CANDIDATES:
        if p.exists():
            logger.info("Using input: %s", p)
            return p
    raise FileNotFoundError(
        "Neither features_clean.parquet nor features_lag_rolling.parquet found."
    )


def resolve_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Documented rule for station-timestamp duplicates:
    Keep the first occurrence after sorting by datetime
    (i.e. the earliest recorded value for that exact timestamp).
    """
    before = len(df)
    df = (
        df.sort_values(["station", "datetime"])
        .drop_duplicates(subset=["station", "datetime"], keep="first")
        .reset_index(drop=True)
    )
    removed = before - len(df)
    if removed:
        logger.info("Removed %d station-timestamp duplicates (kept first)", removed)
    return df


def recalculate_station(group: pd.DataFrame) -> pd.DataFrame:
    """
    Recalculate target, lags and trailing rolling features
    for a single station.  group is already sorted by datetime.
    """
    g = group.copy()

    # Target = next observation's wl_raw (last row becomes NaN)
    g["target_wl_t_plus_1"] = g["wl_raw"].shift(-1)

    # Lag features (past only)
    for lag in LAG_STEPS:
        g[f"wl_lag_{lag}"] = g["wl_raw"].shift(lag)

    # Trailing rolling statistics (past only)
    for w in ROLLING_WINDOWS:
        roll = g["wl_raw"].rolling(window=w, min_periods=1)
        g[f"wl_roll_mean_{w}"] = roll.mean()
        g[f"wl_roll_std_{w}"]  = roll.std()

    return g


def run_realignment() -> pd.DataFrame:
    PHASE2_DIR.mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "reports" / "phase2").mkdir(parents=True, exist_ok=True)

    src = find_input()
    logger.info("Loading %s ...", src)
    df = pd.read_parquet(src)
    logger.info("Loaded shape: %s", df.shape)

    # Basic required columns
    required = {"station", "datetime", "wl_raw"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Required columns missing: {missing}")

    # Ensure datetime is datetime64
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.dropna(subset=["datetime", "wl_raw", "station"])

    # Preserve / create extreme flag (never delete)
    if "flag_extreme_phase2" not in df.columns:
        df["flag_extreme_phase2"] = df["wl_raw"].abs() > MAX_PLAUSIBLE
    n_extreme = int(df["flag_extreme_phase2"].sum())
    logger.info("Extreme readings flagged: %d", n_extreme)

    # Resolve duplicates
    df = resolve_duplicates(df)

    # Sort globally (required before groupby)
    df = df.sort_values(["station", "datetime"]).reset_index(drop=True)

    # Recalculate target + lags + rolling per station
    logger.info("Recalculating target and features station-by-station ...")
    parts = []
    for station, group in df.groupby("station", sort=False):
        parts.append(recalculate_station(group))
    df = pd.concat(parts, ignore_index=True)

    # Rows that still lack a complete lag history or a target are dropped
    lag_cols = [f"wl_lag_{lag}" for lag in LAG_STEPS]
    before = len(df)
    df = df.dropna(subset=lag_cols + ["target_wl_t_plus_1"])
    logger.info(
        "Dropped %d rows lacking complete lag history or target",
        before - len(df),
    )

    # Final sort
    df = df.sort_values(["station", "datetime"]).reset_index(drop=True)

    # Save
    df.to_parquet(OUTPUT_V2, index=False)
    logger.info("Saved → %s  (shape %s)", OUTPUT_V2, df.shape)

    # Quick summary
    summary = {
        "input_file": str(src),
        "output_file": str(OUTPUT_V2),
        "n_rows": int(len(df)),
        "n_stations": int(df["station"].nunique()),
        "n_extreme_flagged": n_extreme,
        "date_min": str(df["datetime"].min()),
        "date_max": str(df["datetime"].max()),
        "note": (
            "target_wl_t_plus_1 recalculated as the next chronological "
            "wl_raw of the same station. Last observation of each station "
            "has missing target and was removed. Signed values preserved."
        ),
    }
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    logger.info("Report written → %s", REPORT)
    return df


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )
    run_realignment()
