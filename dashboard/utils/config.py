"""
Dashboard configuration and path constants.
All paths are relative to the project root (major_project_phase_one).
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Data files (may or may not exist – dashboard handles missing files gracefully)
FEATURES_V2 = PROJECT_ROOT / "data" / "processed" / "phase2" / "features_clean_v2.parquet"
LATEST_READINGS = PROJECT_ROOT / "reports" / "phase3" / "latest_station_readings.csv"
YEARLY_SUMMARY = PROJECT_ROOT / "reports" / "phase3" / "yearly_station_summary.csv"
QUARTERLY_SUMMARY = PROJECT_ROOT / "reports" / "phase3" / "representative_month_summary.csv"
DISTRICT_SUMMARY = PROJECT_ROOT / "reports" / "phase3" / "district_yearly_summary.csv"
PHASE3_SUMMARY = PROJECT_ROOT / "reports" / "phase3" / "phase3_summary.json"
MODEL_COMPARISON = PROJECT_ROOT / "reports" / "phase2" / "model_comparison.csv"
TEST_REPORT = PROJECT_ROOT / "reports" / "phase2" / "test_report.json"
HYBRID_MODEL = PROJECT_ROOT / "models" / "hybrid" / "hybrid_model.joblib"
BEST_MODEL = PROJECT_ROOT / "models" / "best_model.joblib"
MODEL_META = PROJECT_ROOT / "models" / "model_metadata.json"
STATIONS_MASTER = PROJECT_ROOT / "data" / "interim" / "stations_master.parquet"

# FastAPI base URL (local development)
API_BASE = "http://127.0.0.1:8000"

# Display settings
APP_TITLE = "MP Groundwater Intelligence"
APP_SUBTITLE = "AI-Enabled Monitoring, Prediction & Well Suitability Assessment"
PAGE_ICON = "💧"
