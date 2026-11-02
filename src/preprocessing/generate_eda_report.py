"""
Generate a concise EDA / data-quality report after Phase 1.
"""

from __future__ import annotations

import logging

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.preprocessing import config as cfg

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    cfg.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    cfg.REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    if not cfg.STATIONS_MASTER.exists():
        logger.error("stations_master.parquet not found – run the pipeline first")
        return

    stations = pd.read_parquet(cfg.STATIONS_MASTER)
    n_keep = int(stations["keep_station"].sum())

    # Figure 1 – observations per station
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.histplot(stations["n_obs"], bins=40, ax=ax, color="seagreen")
    ax.axvline(
        cfg.MIN_OBS_PER_STATION,
        color="red",
        linestyle="--",
        label=f"Min obs ({cfg.MIN_OBS_PER_STATION})",
    )
    ax.set_title("Observations per station")
    ax.set_xlabel("n_obs")
    ax.legend()
    fig.tight_layout()
    fig.savefig(cfg.FIGURES_DIR / "03_obs_per_station.png", dpi=120)
    plt.close()

    # Figure 2 – spatial map
    fig, ax = plt.subplots(figsize=(7, 6))
    sc = ax.scatter(
        stations["longitude"],
        stations["latitude"],
        c=stations["n_obs"],
        cmap="viridis",
        s=18,
        alpha=0.8,
    )
    plt.colorbar(sc, ax=ax, label="n_obs")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("CGWB telemetry stations – Madhya Pradesh")
    fig.tight_layout()
    fig.savefig(cfg.FIGURES_DIR / "04_station_map.png", dpi=120)
    plt.close()

    report = f"""# Phase-1 EDA & Data-Quality Report
**AI-Enabled Water Well Predictor – Madhya Pradesh**

## 1. Overview

| Item | Value |
|------|-------|
| Total stations discovered | {len(stations)} |
| Stations retained (≥ {cfg.MIN_OBS_PER_STATION} observations) | {n_keep} |
| Feature matrix | `{cfg.FEATURES_FILE.name}` |

## 2. Measurement Convention (Important)

The column `Groundwater Level Telemetry 6 Hourly (meter)` contains a high proportion of negative values in the published CGWB telemetry files.

**A high negative rate alone does not scientifically prove that the values represent relative hydraulic head.**

Possible explanations that still require verification against official CGWB / NWIC documentation:

- Sensor zero / installation reference below ground level
- Signed depth relative to a local datum
- Data-logger configuration that stores head relative to the transducer

**Pipeline decision (transparent and reversible):**

- The original signed value is stored as `wl_raw` and is **never** automatically converted with `abs()`.
- Extreme magnitudes and large inter-observation jumps are only **flagged**.
- Downstream models currently receive the signed series.

## 3. Quality flags

| Flag | Meaning |
|------|---------|
| `flag_extreme_magnitude` | Absolute value outside [{cfg.MIN_PLAUSIBLE_DEPTH}, {cfg.MAX_PLAUSIBLE_DEPTH}] m |
| `flag_large_jump` | Change from previous reading of the same station > {cfg.MAX_JUMP_METRES} m |
| `flag_bad_coords` | Latitude / longitude missing or outside Madhya Pradesh bounding box |
| `flag_any_suspicious` | Logical OR of the above |

## 4. Visualisations

![Observations per station](../figures/03_obs_per_station.png)

![Station map](../figures/04_station_map.png)

## 5. Next steps (Phase 2)

- Chronological train / validation / test split
- Train Random Forest, XGBoost, CatBoost
- Select the single best model by validation MAE
- Evaluate on the untouched test set
- Integrate forecasts into the Streamlit application

*Data source: Central Ground Water Board (CGWB) telemetry. Academic use only.*
"""
    with open(cfg.EDA_REPORT, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info("EDA report written → %s", cfg.EDA_REPORT)


if __name__ == "__main__":
    main()
