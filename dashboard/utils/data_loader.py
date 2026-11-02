"""
Safe data loading helpers.
Never crash the dashboard if a file is missing – return empty DataFrames / None.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import streamlit as st

from . import config as cfg

logger = logging.getLogger(__name__)


def _safe_read_parquet(path: Path) -> Optional[pd.DataFrame]:
    if not path.exists():
        return None
    try:
        return pd.read_parquet(path)
    except Exception as e:
        logger.warning("Could not read %s: %s", path, e)
        return None


def _safe_read_csv(path: Path) -> Optional[pd.DataFrame]:
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except Exception as e:
        logger.warning("Could not read %s: %s", path, e)
        return None


def _safe_read_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Could not read %s: %s", path, e)
        return None


@st.cache_data(show_spinner="Loading station data…")
def load_latest_readings() -> Optional[pd.DataFrame]:
    return _safe_read_csv(cfg.LATEST_READINGS)


@st.cache_data(show_spinner="Loading yearly summary…")
def load_yearly_summary() -> Optional[pd.DataFrame]:
    df = _safe_read_csv(cfg.YEARLY_SUMMARY)

    if df is not None:
        # Standardize the yearly groundwater mean column.
        if "average_wl" in df.columns and "wl_mean" not in df.columns:
            df = df.rename(columns={"average_wl": "wl_mean"})

    return df


@st.cache_data(show_spinner="Loading quarterly summary…")
def load_quarterly_summary() -> Optional[pd.DataFrame]:
    df = _safe_read_csv(cfg.QUARTERLY_SUMMARY)

    if df is not None:
        # Standardize the groundwater-level mean column.
        if "average_wl" in df.columns and "wl_mean" not in df.columns:
            df = df.rename(columns={"average_wl": "wl_mean"})

        # Convert representative month names into month numbers.
        if "representative_month" in df.columns:
            month_map = {
                "March": 3,
                "June": 6,
                "September": 9,
                "December": 12,
            }
            df["representative_month"] = (
                df["representative_month"]
                .astype(str)
                .str.strip()
                .str.title()
                .map(month_map)
            )

    return df


@st.cache_data(show_spinner="Loading district summary…")
def load_district_summary() -> Optional[pd.DataFrame]:
    return _safe_read_csv(cfg.DISTRICT_SUMMARY)


@st.cache_data(show_spinner="Loading Phase-3 summary…")
def load_phase3_summary() -> Optional[dict]:
    return _safe_read_json(cfg.PHASE3_SUMMARY)


@st.cache_data(show_spinner="Loading model comparison…")
def load_model_comparison() -> Optional[pd.DataFrame]:
    return _safe_read_csv(cfg.MODEL_COMPARISON)


@st.cache_data(show_spinner="Loading stations master…")
def load_stations_master() -> Optional[pd.DataFrame]:
    return _safe_read_parquet(cfg.STATIONS_MASTER)


@st.cache_data(show_spinner="Loading a bounded feature sample…")
def load_features_sample(n: int = 50_000) -> Optional[pd.DataFrame]:
    """Read at most n rows using Arrow batches instead of loading the full dataset."""
    import pyarrow.dataset as ds

    path = cfg.FEATURES_V2
    if not path.exists():
        return None

    try:
        dataset = ds.dataset(str(path), format="parquet")
        scanner = dataset.scanner(batch_size=8192)

        chunks = []
        remaining = n

        for batch in scanner.to_batches():
            take = min(batch.num_rows, remaining)
            if take > 0:
                chunks.append(batch.slice(0, take).to_pandas())
                remaining -= take
            if remaining <= 0:
                break

        if not chunks:
            return pd.DataFrame()

        return pd.concat(chunks, ignore_index=True)

    except Exception as e:
        logger.warning("Could not load feature sample: %s", e)
        return None


def file_status() -> dict[str, bool]:
    """Return existence status of key files for the Data Quality page."""
    paths = {
        "features_clean_v2": cfg.FEATURES_V2,
        "latest_readings": cfg.LATEST_READINGS,
        "yearly_summary": cfg.YEARLY_SUMMARY,
        "quarterly_summary": cfg.QUARTERLY_SUMMARY,
        "district_summary": cfg.DISTRICT_SUMMARY,
        "phase3_summary": cfg.PHASE3_SUMMARY,
        "model_comparison": cfg.MODEL_COMPARISON,
        "hybrid_model": cfg.HYBRID_MODEL,
        "best_model": cfg.BEST_MODEL,
        "stations_master": cfg.STATIONS_MASTER,
    }
    return {k: v.exists() for k, v in paths.items()}
