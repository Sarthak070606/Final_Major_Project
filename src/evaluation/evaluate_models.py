"""
Post-training evaluation helpers (station-wise metrics, etc.).
"""

from __future__ import annotations

import json
import logging

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.training import config_phase2 as cfg

logger = logging.getLogger(__name__)


def station_wise_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    stations: pd.Series,
) -> pd.DataFrame:
    """Compute MAE / RMSE / R² per station."""
    df = pd.DataFrame(
        {"station": stations.values, "y_true": y_true, "y_pred": y_pred}
    )
    rows = []
    for st, g in df.groupby("station"):
        if len(g) < 5:
            continue
        rows.append(
            {
                "station": st,
                "n": len(g),
                "mae": mean_absolute_error(g["y_true"], g["y_pred"]),
                "rmse": np.sqrt(mean_squared_error(g["y_true"], g["y_pred"])),
                "r2": r2_score(g["y_true"], g["y_pred"]),
            }
        )
    return pd.DataFrame(rows).sort_values("mae")


def run_station_evaluation() -> None:
    """Evaluate the best saved model on the test set, station by station."""
    meta_path = cfg.MODEL_META_PATH
    if not meta_path.exists():
        logger.error("Model metadata not found – run training first")
        return

    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)

    best_name = meta["best_model_name"]
    logger.info("Evaluating best model: %s", best_name)

    test = pd.read_parquet(cfg.TEST_FILE)
    X_test = test[cfg.FEATURE_COLS]
    y_test = test[cfg.TARGET_COL].values
    stations = test["station"]

    if best_name == "persistence":
        y_pred = X_test["wl_raw"].values
    else:
        model = joblib.load(cfg.BEST_MODEL_PATH)
        y_pred = model.predict(X_test)

    station_df = station_wise_metrics(y_test, y_pred, stations)
    out = cfg.REPORTS_DIR / "station_wise_metrics.csv"
    station_df.to_csv(out, index=False)
    logger.info("Station-wise metrics saved → %s", out)
    logger.info("Median station MAE: %.4f", station_df["mae"].median())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
    run_station_evaluation()
