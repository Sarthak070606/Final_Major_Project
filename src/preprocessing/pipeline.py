"""
Phase 1 entry point – Memory-efficient station-by-station pipeline.

Usage (from project root):
    python -m src.preprocessing.pipeline
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.preprocessing import config as cfg
from src.preprocessing.load_and_clean import run_station_by_station_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("=" * 60)
    logger.info("Phase 1 – Memory-efficient Groundwater Preprocessing")
    logger.info("Project root : %s", cfg.PROJECT_ROOT)
    logger.info("=" * 60)

    # Basic existence checks
    if not cfg.RAW_2021_2025.exists() and not cfg.RAW_2026.exists():
        logger.error(
            "No raw CSV files found in data/raw/. "
            "Please place the two CGWB files there before running."
        )
        sys.exit(1)

    run_station_by_station_pipeline(restart=True)

    summary = {
        "features_file": str(cfg.FEATURES_FILE),
        "stations_master": str(cfg.STATIONS_MASTER),
        "scientific_note": (
            "Original signed wl_raw values are preserved. "
            "No automatic absolute-value conversion was performed. "
            "A high negative reading rate alone does not establish "
            "the official CGWB measurement convention."
        ),
    }
    cfg.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(cfg.PHASE1_SUMMARY, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info("Summary written → %s", cfg.PHASE1_SUMMARY)
    logger.info("Phase 1 completed successfully.")


if __name__ == "__main__":
    main()
