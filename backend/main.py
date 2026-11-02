
from pathlib import Path
from datetime import datetime
import warnings

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

FEATURES_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phase2"
    / "features_clean_v2.parquet"
)

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "hybrid"
    / "hybrid_model.joblib"
)


# --------------------------------------------------
# LOAD HYBRID MODEL
# --------------------------------------------------

if not FEATURES_PATH.exists():
    raise FileNotFoundError(f"Feature dataset not found: {FEATURES_PATH}")

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Hybrid model not found: {MODEL_PATH}")

artifact = joblib.load(MODEL_PATH)

model = artifact["model"]
FEATURE_COLS = artifact["feature_cols"]
TARGET_COL = artifact["target_col"]

KNOWN_STATIONS = {
    str(station) for station in artifact["known_stations"]
}

FORECAST_HORIZON = artifact["forecast_horizon"]


# --------------------------------------------------
# FASTAPI APPLICATION
# --------------------------------------------------

app = FastAPI(
    title="Groundwater Prediction API",
    description=(
        "AI-enabled groundwater next-observation prediction "
        "using CGWB-derived data."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Groundwater Prediction API is running",
        "model": type(model).__name__,
        "feature_count": len(FEATURE_COLS),
        "known_station_count": len(KNOWN_STATIONS),
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "dataset_exists": FEATURES_PATH.exists(),
    }


# --------------------------------------------------
# PREDICTION ENDPOINT
# --------------------------------------------------

@app.get("/api/predict/{station}")
def predict_groundwater(station: str):

    try:
        # Read only the required columns and requested station.
        required_columns = list(
            dict.fromkeys(
                ["station", "datetime", "wl_raw"]
                + FEATURE_COLS
                + ["flag_any_suspicious"]
            )
        )

        df = pd.read_parquet(
            FEATURES_PATH,
            columns=required_columns,
            filters=[("station", "==", station)],
            engine="pyarrow",
        )

        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No feature records found for station: {station}. "
                    "The station may not have sufficient historical data."
                ),
            )

        df["datetime"] = pd.to_datetime(
            df["datetime"], errors="coerce"
        )

        df = df.dropna(subset=["datetime", "wl_raw"])

        if df.empty:
            raise HTTPException(
                status_code=422,
                detail="No valid observations found for this station.",
            )

        # Latest available observation.
        latest = df.sort_values("datetime").iloc[-1]

        last_level = float(latest["wl_raw"])
        last_time = latest["datetime"]

        # Check model input features.
        missing_features = [
            col for col in FEATURE_COLS
            if col not in df.columns
        ]

        if missing_features:
            raise HTTPException(
                status_code=500,
                detail=f"Missing model features: {missing_features}",
            )

        feature_row = latest[FEATURE_COLS].to_frame().T

        feature_row = feature_row.apply(
            pd.to_numeric, errors="coerce"
        )

        if feature_row.isna().any().any():
            raise HTTPException(
                status_code=422,
                detail="Latest observation has missing model features.",
            )

        # --------------------------------------------------
        # KNOWN STATION: RANDOM FOREST
        # UNSEEN STATION: PERSISTENCE BASELINE
        # --------------------------------------------------

        if station in KNOWN_STATIONS:

            prediction = float(
                model.predict(feature_row[FEATURE_COLS])[0]
            )

            method = "Random Forest"

        else:

            prediction = last_level
            method = "Persistence baseline"

        if not np.isfinite(prediction):
            raise HTTPException(
                status_code=500,
                detail="Model returned an invalid prediction.",
            )

        suspicious = False

        if (
            "flag_any_suspicious" in latest.index
            and pd.notna(latest["flag_any_suspicious"])
        ):
            suspicious = bool(latest["flag_any_suspicious"])

        warning = (
            "The latest source observation is flagged as suspicious. "
            "Interpret this prediction cautiously."
            if suspicious
            else
            "This predicts the next available observation, not a "
            "guaranteed six-hour forecast. It is not a drinking-water "
            "safety assessment or a borewell suitability assessment."
        )

        return {
            "station": station,
            "predicted_next_available_observation": round(
                prediction, 4
            ),
            "prediction_method": method,
            "last_observed_level": round(last_level, 4),
            "last_observation_time": last_time.isoformat(),
            "forecast_horizon": FORECAST_HORIZON,
            "warning": warning,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(exc)}",
        )
