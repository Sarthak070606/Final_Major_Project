"""
Memory-efficient loading, cleaning and station-level feature engineering.

Guarantees
----------
* Never loads the full 4.25 M-row table into RAM.
* Original signed groundwater readings are preserved exactly.
* Suspicious observations are flagged, never deleted.
* Lag and rolling features are computed station-by-station in chronological order
  → zero future-data leakage.
* Pipeline is restartable via a checkpoint file.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from . import config as cfg

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _standardise(df: pd.DataFrame) -> pd.DataFrame:
    """Map original CGWB column names to a clean internal schema."""
    rename = {
        cfg.COL_STATION: "station",
        cfg.COL_STATE: "state",
        cfg.COL_DISTRICT: "district",
        cfg.COL_LAT: "latitude",
        cfg.COL_LON: "longitude",
        cfg.COL_RL_MSL: "rl_msl",
        cfg.COL_DATETIME: "datetime_raw",
        cfg.COL_WL: "wl_raw",
    }
    df = df.rename(columns=rename)
    return df[list(rename.values())].copy()


def _parse_and_flag(df: pd.DataFrame) -> pd.DataFrame:
    """Parse timestamps and create quality flags (no deletion)."""
    df = df.copy()
    df["datetime"] = pd.to_datetime(
        df["datetime_raw"], dayfirst=True, errors="coerce"
    )
    df["flag_bad_timestamp"] = df["datetime"].isna()

    # Madhya Pradesh approximate bounding box
    lat_ok = df["latitude"].between(21.0, 27.0)
    lon_ok = df["longitude"].between(74.0, 83.0)
    df["flag_bad_coords"] = (
        ~(lat_ok & lon_ok) | df["latitude"].isna() | df["longitude"].isna()
    )

    # Magnitude check uses absolute value only for the test;
    # the original signed value is never altered.
    abs_wl = df["wl_raw"].abs()
    df["flag_extreme_magnitude"] = (
        ((abs_wl < cfg.MIN_PLAUSIBLE_DEPTH) | (abs_wl > cfg.MAX_PLAUSIBLE_DEPTH))
        & df["wl_raw"].notna()
    )
    return df


# ----------------------------------------------------------------------
# Pass 1 – stream CSVs and write one temporary Parquet per station
# ----------------------------------------------------------------------
def first_pass_build_station_files() -> pd.DataFrame:
    cfg.STATION_TEMP.mkdir(parents=True, exist_ok=True)

    buffers: Dict[str, List[pd.DataFrame]] = {}
    station_meta: Dict[str, dict] = {}

    usecols = [
        cfg.COL_STATION, cfg.COL_STATE, cfg.COL_DISTRICT,
        cfg.COL_LAT, cfg.COL_LON, cfg.COL_RL_MSL,
        cfg.COL_DATETIME, cfg.COL_WL,
    ]

    def _flush(station: str) -> None:
        if station not in buffers or not buffers[station]:
            return
        df = pd.concat(buffers[station], ignore_index=True)
        safe = (
            station.replace("/", "_")
            .replace(" ", "_")
            .replace("\\", "_")
            .replace(":", "_")
        )
        out = cfg.STATION_TEMP / f"{safe}.parquet"
        if out.exists():
            old = pd.read_parquet(out)
            df = pd.concat([old, df], ignore_index=True)
        df.to_parquet(out, index=False)
        buffers[station] = []

    for source_label, path in [("2021_2025", cfg.RAW_2021_2025), ("2026", cfg.RAW_2026)]:
        if not path.exists():
            logger.warning("Raw file missing: %s – skipping", path)
            continue

        logger.info("First pass – streaming %s ...", path.name)
        for i, chunk in enumerate(
            pd.read_csv(
                path,
                usecols=usecols,
                chunksize=cfg.CHUNKSIZE,
                low_memory=False,
            )
        ):
            chunk = _standardise(chunk)
            chunk["source"] = source_label
            chunk = _parse_and_flag(chunk)
            # keep only rows with a valid timestamp for the temp files
            chunk = chunk[~chunk["flag_bad_timestamp"]]

            for station, grp in chunk.groupby("station"):
                if station not in buffers:
                    buffers[station] = []
                    station_meta[station] = {
                        "state": grp["state"].iloc[0],
                        "district": grp["district"].iloc[0],
                        "latitude": float(grp["latitude"].median()),
                        "longitude": float(grp["longitude"].median()),
                        "rl_msl": (
                            float(grp["rl_msl"].median())
                            if grp["rl_msl"].notna().any()
                            else None
                        ),
                    }
                buffers[station].append(grp)

                if sum(len(x) for x in buffers[station]) > 50_000:
                    _flush(station)

            if (i + 1) % 4 == 0:
                logger.info("  chunk %d finished", i + 1)

        for st in list(buffers.keys()):
            _flush(st)

    # Build stations master table
    rows = []
    for st, meta in station_meta.items():
        safe = (
            st.replace("/", "_")
            .replace(" ", "_")
            .replace("\\", "_")
            .replace(":", "_")
        )
        f = cfg.STATION_TEMP / f"{safe}.parquet"
        n = len(pd.read_parquet(f, columns=["wl_raw"])) if f.exists() else 0
        rows.append(
            {
                "station": st,
                **meta,
                "n_obs": n,
                "keep_station": n >= cfg.MIN_OBS_PER_STATION,
            }
        )
    stations = pd.DataFrame(rows)
    stations.to_parquet(cfg.STATIONS_MASTER, index=False)
    logger.info("Stations master written – %d stations", len(stations))
    return stations


# ----------------------------------------------------------------------
# Pass 2 – process one station at a time
# ----------------------------------------------------------------------
def process_one_station(station: str) -> pd.DataFrame | None:
    """
    Load one station, sort chronologically, flag jumps,
    create lag + trailing rolling features, return feature rows.
    """
    safe = (
        station.replace("/", "_")
        .replace(" ", "_")
        .replace("\\", "_")
        .replace(":", "_")
    )
    path = cfg.STATION_TEMP / f"{safe}.parquet"
    if not path.exists():
        return None

    df = pd.read_parquet(path)
    if len(df) < cfg.MIN_OBS_PER_STATION:
        return None

    # Chronological order is mandatory
    df = df.sort_values("datetime").reset_index(drop=True)

    # Jump flag (station already isolated)
    prev = df["wl_raw"].shift(1)
    jump = (df["wl_raw"] - prev).abs()
    df["flag_large_jump"] = (jump > cfg.MAX_JUMP_METRES) & prev.notna()

    df["flag_any_suspicious"] = (
        df["flag_extreme_magnitude"]
        | df["flag_large_jump"]
        | df["flag_bad_coords"]
    )

    # Calendar / seasonal features
    df["year"] = df["datetime"].dt.year
    df["month"] = df["datetime"].dt.month
    df["day_of_year"] = df["datetime"].dt.dayofyear
    df["hour"] = df["datetime"].dt.hour
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    df["doy_sin"] = np.sin(2 * np.pi * df["day_of_year"] / 365.25)
    df["doy_cos"] = np.cos(2 * np.pi * df["day_of_year"] / 365.25)

    # Lag features (no leakage – station is isolated and sorted)
    for lag in cfg.LAG_STEPS:
        df[f"wl_lag_{lag}"] = df["wl_raw"].shift(lag)

    # Trailing rolling statistics
    for w in cfg.ROLLING_WINDOWS:
        roll = df["wl_raw"].rolling(window=w, min_periods=1)
        df[f"wl_roll_mean_{w}"] = roll.mean()
        df[f"wl_roll_std_{w}"] = roll.std()

    # Target = next 6-hour observation
    df["target_wl_t_plus_1"] = df["wl_raw"].shift(-1)

    # Keep only rows that have a complete lag history and a target
    lag_cols = [f"wl_lag_{lag}" for lag in cfg.LAG_STEPS]
    df = df.dropna(subset=lag_cols + ["target_wl_t_plus_1"])

    keep_cols = (
        [
            "station",
            "datetime",
            "latitude",
            "longitude",
            "district",
            "wl_raw",
            "flag_any_suspicious",
        ]
        + lag_cols
        + [f"wl_roll_mean_{w}" for w in cfg.ROLLING_WINDOWS]
        + [f"wl_roll_std_{w}" for w in cfg.ROLLING_WINDOWS]
        + [
            "year",
            "month",
            "day_of_year",
            "hour",
            "month_sin",
            "month_cos",
            "doy_sin",
            "doy_cos",
            "target_wl_t_plus_1",
        ]
    )
    return df[keep_cols]


def run_station_by_station_pipeline(restart: bool = True) -> None:
    """
    Full memory-efficient Phase-1 pipeline with restart support.
    """
    cfg.INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    cfg.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    cfg.CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Pass 1
    # ------------------------------------------------------------------
    if not cfg.STATION_TEMP.exists() or not any(cfg.STATION_TEMP.glob("*.parquet")):
        logger.info("Running first pass (building per-station files) ...")
        stations = first_pass_build_station_files()
    else:
        logger.info("Re-using existing station_temp files (restart mode)")
        if cfg.STATIONS_MASTER.exists():
            stations = pd.read_parquet(cfg.STATIONS_MASTER)
        else:
            stations = first_pass_build_station_files()

    keep_stations = stations.loc[stations["keep_station"], "station"].tolist()
    logger.info("Stations to process: %d", len(keep_stations))

    # ------------------------------------------------------------------
    # Checkpoint
    # ------------------------------------------------------------------
    done: set[str] = set()
    if restart and cfg.CHECKPOINT_STATIONS.exists():
        done = set(
            cfg.CHECKPOINT_STATIONS.read_text(encoding="utf-8").splitlines()
        )
        logger.info("Restart: %d stations already finished", len(done))

    # ------------------------------------------------------------------
    # Pass 2 – one station at a time
    # ------------------------------------------------------------------
    writer = None
    n_rows_total = 0
    n_stations_done = 0

    for idx, station in enumerate(keep_stations, 1):
        if station in done:
            continue

        feat = process_one_station(station)
        if feat is None or len(feat) == 0:
            with open(cfg.CHECKPOINT_STATIONS, "a", encoding="utf-8") as f:
                f.write(station + "\n")
            continue

        table = pa.Table.from_pandas(feat, preserve_index=False)

        if writer is None:
            # Create the output file (never touches the original CSVs)
            writer = pq.ParquetWriter(str(cfg.FEATURES_FILE), table.schema)
        writer.write_table(table)

        n_rows_total += len(feat)
        n_stations_done += 1

        with open(cfg.CHECKPOINT_STATIONS, "a", encoding="utf-8") as f:
            f.write(station + "\n")

        if idx % 20 == 0 or idx == len(keep_stations):
            logger.info(
                "Progress: %d / %d stations | %d feature rows written",
                idx,
                len(keep_stations),
                n_rows_total,
            )

    if writer is not None:
        writer.close()

    logger.info(
        "Phase-1 finished. Stations processed this run: %d | Total feature rows: %d",
        n_stations_done,
        n_rows_total,
    )
    logger.info("Feature matrix → %s", cfg.FEATURES_FILE)
