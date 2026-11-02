"""
Configuration for Phase 1 – Memory-efficient Groundwater Preprocessing
AI-Enabled Water Well Predictor (Madhya Pradesh)
"""

from pathlib import Path

# ---------------------------------------------------------------------
# Project paths (work on Windows and Linux)
# ---------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR        = PROJECT_ROOT / "data" / "raw"
INTERIM_DIR    = PROJECT_ROOT / "data" / "interim"
PROCESSED_DIR  = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR    = PROJECT_ROOT / "reports"
FIGURES_DIR    = PROJECT_ROOT / "figures"
CHECKPOINT_DIR = INTERIM_DIR / "checkpoints"
STATION_TEMP   = INTERIM_DIR / "station_temp"

# Raw input files (must be placed by the user)
RAW_2021_2025 = RAW_DIR / "gwl_tel_6_hourly_madhya_pradesh_gw_mp_2021_2025.csv"
RAW_2026      = RAW_DIR / "gwl_tel_6_hourly_cgwb_mp_2026_2030.csv"

# ---------------------------------------------------------------------
# Original column names observed in the CGWB files
# ---------------------------------------------------------------------
COL_STATION  = "Station"
COL_STATE    = "State"
COL_DISTRICT = "District"
COL_LAT      = "Latitude"
COL_LON      = "Longitude"
COL_RL_MSL   = "RL_MSL"
COL_DATETIME = "Data Acquisition Time"
COL_WL       = "Groundwater Level Telemetry 6 Hourly (meter)"

# ---------------------------------------------------------------------
# Physical thresholds (all configurable)
# ---------------------------------------------------------------------
MIN_PLAUSIBLE_DEPTH = 0.05      # metres
MAX_PLAUSIBLE_DEPTH = 150.0     # metres
MAX_JUMP_METRES     = 10.0      # metres between consecutive readings of same station
MIN_OBS_PER_STATION = 30

# ---------------------------------------------------------------------
# Feature engineering (number of 6-hour observation steps)
# 1 step ≈ 6 h, 4 steps ≈ 1 day, 28 steps ≈ 7 days, 120 steps ≈ 30 days
# ---------------------------------------------------------------------
LAG_STEPS       = [1, 4, 28, 120]
ROLLING_WINDOWS = [4, 28, 120]

# ---------------------------------------------------------------------
# Chunk size for first pass
# ---------------------------------------------------------------------
CHUNKSIZE = 300_000

# ---------------------------------------------------------------------
# Output files
# ---------------------------------------------------------------------
STATIONS_MASTER     = INTERIM_DIR / "stations_master.parquet"
FEATURES_FILE       = PROCESSED_DIR / "features_lag_rolling.parquet"
CHECKPOINT_STATIONS = CHECKPOINT_DIR / "processed_stations.txt"
EDA_REPORT          = REPORTS_DIR / "eda_data_quality_report.md"
PHASE1_SUMMARY      = REPORTS_DIR / "phase1_summary.json"
