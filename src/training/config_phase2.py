
"""
Phase 2 configuration – Groundwater Level Forecasting
"""

from pathlib import Path

# --------------------------------------------------
# PROJECT ROOT
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# --------------------------------------------------
# PHASE 1 INPUT
# --------------------------------------------------

PHASE1_FEATURES = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "features_lag_rolling.parquet"
)

# --------------------------------------------------
# PHASE 2 DIRECTORIES
# --------------------------------------------------

PHASE2_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phase2"
)

MODELS_DIR = PROJECT_ROOT / "models"

REPORTS_DIR = (
    PROJECT_ROOT
    / "reports"
    / "phase2"
)

FIGURES_DIR = (
    PROJECT_ROOT
    / "figures"
    / "phase2"
)

# --------------------------------------------------
# CORRECTED MODELLING DATASET
# IMPORTANT: Use validated v2 dataset
# --------------------------------------------------

CLEAN_FEATURES = (
    PHASE2_DIR / "features_clean_v2.parquet"
)

# --------------------------------------------------
# TRAIN / VALIDATION / TEST FILES
# --------------------------------------------------

SPLIT_INFO = PHASE2_DIR / "split_boundaries.json"

TRAIN_FILE = PHASE2_DIR / "train.parquet"

VAL_FILE = PHASE2_DIR / "val.parquet"

TEST_FILE = PHASE2_DIR / "test.parquet"

# --------------------------------------------------
# MODEL ARTEFACTS
# --------------------------------------------------

BEST_MODEL_PATH = MODELS_DIR / "best_model.joblib"

MODEL_META_PATH = MODELS_DIR / "model_metadata.json"

COMPARISON_CSV = REPORTS_DIR / "model_comparison.csv"

VAL_REPORT = REPORTS_DIR / "validation_report.json"

TEST_REPORT = REPORTS_DIR / "test_report.json"

# --------------------------------------------------
# FEATURE COLUMNS
# --------------------------------------------------

FEATURE_COLS = [
    "wl_raw",

    "wl_lag_1",
    "wl_lag_4",
    "wl_lag_28",
    "wl_lag_120",

    "wl_roll_mean_4",
    "wl_roll_mean_28",
    "wl_roll_mean_120",

    "wl_roll_std_4",
    "wl_roll_std_28",
    "wl_roll_std_120",

    "month",
    "day_of_year",
    "hour",

    "month_sin",
    "month_cos",
    "doy_sin",
    "doy_cos",

    "latitude",
    "longitude",
]

# --------------------------------------------------
# TARGET COLUMN
# --------------------------------------------------

TARGET_COL = "target_wl_t_plus_1"

# --------------------------------------------------
# CHRONOLOGICAL SPLIT RATIOS
# --------------------------------------------------

TRAIN_RATIO = 0.70

VAL_RATIO = 0.15

# Remaining 0.15 is used for testing.

# --------------------------------------------------
# REPRODUCIBILITY
# --------------------------------------------------

RANDOM_SEED = 42

# Flagging threshold only.
# Do not automatically convert signed groundwater
# readings into absolute values.

MAX_PLAUSIBLE_ABS = 150.0
