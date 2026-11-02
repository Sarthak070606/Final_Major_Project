# Phase 1 – Groundwater Data Preprocessing & Feature Engineering

**AI-Enabled Water Well Predictor (Madhya Pradesh)**  
B.Tech Major Project

---

## Folder structure

```
major_project_phase_one/
├── data/
│   ├── raw/                          ← place the two original CSVs here
│   ├── interim/
│   │   ├── checkpoints/
│   │   └── station_temp/
│   └── processed/
├── src/
│   └── preprocessing/
│       ├── __init__.py
│       ├── config.py
│       ├── load_and_clean.py
│       ├── feature_engineering.py
│       ├── pipeline.py
│       └── generate_eda_report.py
├── reports/
├── figures/
├── notebooks/
├── requirements-phase1.txt
└── PHASE1_README.md
```

---

## Quick start (Windows PowerShell)

1. Copy the entire contents of this package into your `major_project_phase_one` folder.

2. Place the two original CSVs into `data\raw\` (do **not** overwrite them later):

   - `gwl_tel_6_hourly_madhya_pradesh_gw_mp_2021_2025.csv`
   - `gwl_tel_6_hourly_cgwb_mp_2026_2030.csv`

3. Open PowerShell **in the project root** and run:

```powershell
# Create folders (safe if they already exist)
New-Item -ItemType Directory -Force -Path data\raw, data\interim, data\processed, data\interim\checkpoints, data\interim\station_temp, reports, figures, notebooks

# Install dependencies
pip install -r requirements-phase1.txt

# Make the package importable
$env:PYTHONPATH = (Get-Location).Path

# Run the full Phase-1 pipeline
python -m src.preprocessing.pipeline

# Generate the EDA report + figures
python -m src.preprocessing.generate_eda_report
```

---

## What the pipeline guarantees

| Guarantee | Implemented |
|-----------|-------------|
| Original CSVs never modified | Yes |
| Signed `wl_raw` preserved (no auto `abs()`) | Yes |
| Suspicious values only flagged | Yes |
| Chunked reading of the 569 MB file | Yes |
| Station-by-station chronological processing | Yes |
| Lag + trailing rolling features (no leakage) | Yes |
| Restartable via checkpoint | Yes |
| All outputs written as Parquet | Yes |

---

## Expected outputs

| File | Description |
|------|-------------|
| `data/interim/stations_master.parquet` | One row per station |
| `data/interim/station_temp/*.parquet` | Temporary per-station files |
| `data/processed/features_lag_rolling.parquet` | Final feature matrix |
| `data/interim/checkpoints/processed_stations.txt` | Restart checkpoint |
| `reports/phase1_summary.json` | Short summary |
| `reports/eda_data_quality_report.md` | Data-quality report |
| `figures/03_obs_per_station.png` | Histogram |
| `figures/04_station_map.png` | Spatial map |

---

## After Phase 1 succeeds

Share the content of `reports/phase1_summary.json` (or any error log) and we will move to Phase 2 – model training.
