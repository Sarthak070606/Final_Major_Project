# Phase 2 – Groundwater Level Forecasting

**AI-Enabled Water Well Predictor (Madhya Pradesh)**  
B.Tech Major Project

---

## Objective

Predict the **next chronological groundwater-level observation** (`target_wl_t_plus_1`)  
for existing CGWB monitoring stations using only past information.

- Target is the signed `wl_raw` value (never converted to absolute).
- Forecast horizon = 1 step (approximately 6 hours).
- No claims are made about discharge, drilling depth or water quality.

---

## Folder structure

```
major_project_phase_one/
├── data/processed/
│   ├── features_lag_rolling.parquet   ← Phase 1 output (input)
│   └── phase2/                        ← Phase 2 outputs
├── src/
│   ├── training/
│   │   ├── config_phase2.py
│   │   ├── prepare_dataset.py
│   │   ├── split_data.py
│   │   └── train_models.py
│   └── evaluation/
│       └── evaluate_models.py
├── models/
├── reports/phase2/
├── figures/phase2/
├── requirements-phase2.txt
└── PHASE2_README.md
```

---

## Exact PowerShell commands

Run these commands **from the root of `major_project_phase_one`**:

```powershell
# 1. Install dependencies
pip install -r requirements-phase2.txt

# 2. Make the package importable
$env:PYTHONPATH = (Get-Location).Path

# 3. Inspect + clean Phase 1 data (creates data/processed/phase2/features_clean.parquet)
python -m src.training.prepare_dataset

# 4. Create chronological train / val / test splits
python -m src.training.split_data

# 5. Train all models and select the best by validation MAE
python -m src.training.train_models

# 6. Station-wise evaluation of the selected model
python -m src.evaluation.evaluate_models
```

---

## Models trained

| Group | Models |
|-------|--------|
| Baseline | Persistence, Linear Regression, Ridge |
| Trees | Decision Tree, Random Forest, Extra Trees, HistGradientBoosting |
| Boosting | AdaBoost, Gradient Boosting, XGBoost*, CatBoost*, LightGBM* |

\* Optional – skipped gracefully if the library is not installed.

---

## Selection rule

1. All models are evaluated on the **validation** set.  
2. The model with the lowest validation MAE is selected.  
3. That model is then evaluated on the completely untouched **test** set.  
4. Results are compared against the persistence baseline.

---

## Important scientific guarantees

- Original signed groundwater readings are never converted with `abs()`.
- No future information enters the feature matrix.
- Test set remains untouched until final evaluation.
- No metrics are fabricated.
- Phase 1 files are never overwritten.

---

## Expected outputs

| File | Description |
|------|-------------|
| `data/processed/phase2/features_clean.parquet` | Cleaned modelling dataset |
| `data/processed/phase2/train.parquet` | Training split |
| `data/processed/phase2/val.parquet` | Validation split |
| `data/processed/phase2/test.parquet` | Test split |
| `models/best_model.joblib` | Selected model |
| `models/model_metadata.json` | Feature list + metrics |
| `reports/phase2/model_comparison.csv` | All models ranked by val MAE |
| `reports/phase2/test_report.json` | Final test metrics |
| `reports/phase2/station_wise_metrics.csv` | Per-station performance |

After the pipeline finishes, share `reports/phase2/model_comparison.csv` (or the test report) so we can interpret the results together.
