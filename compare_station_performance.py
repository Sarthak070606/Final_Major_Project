
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.training.config_phase2 import FEATURE_COLS, TARGET_COL

TRAIN_PATH = "data/processed/phase2/train.parquet"
TEST_PATH = "data/processed/phase2/test.parquet"
MODEL_PATH = "models/best_model.joblib"

print("Loading datasets...")
train = pd.read_parquet(TRAIN_PATH, columns=["station"])
test = pd.read_parquet(TEST_PATH)

model = joblib.load(MODEL_PATH)

known_stations = set(train["station"].dropna().unique())
test["station_group"] = np.where(
    test["station"].isin(known_stations),
    "Known stations",
    "Unseen stations"
)

X = test[FEATURE_COLS].to_numpy(dtype=np.float64)
y = test[TARGET_COL].to_numpy(dtype=np.float64)

wl_index = FEATURE_COLS.index("wl_raw")
baseline = X[:, wl_index]
predictions = model.predict(X)

mask = (
    np.isfinite(y)
    & (np.abs(y) <= 150)
    & np.isfinite(X).all(axis=1)
)

for col in FEATURE_COLS:
    if col.startswith(("wl_", "lag_", "rolling_")):
        values = test[col].to_numpy(dtype=np.float64)
        mask &= np.abs(values) <= 150

print("\n========== STATION-WISE TEST RESULTS ==========")

for group in ["Known stations", "Unseen stations"]:
    group_mask = mask & (test["station_group"].to_numpy() == group)

    actual = y[group_mask]
    pred = predictions[group_mask]
    base = baseline[group_mask]

    print(f"\n{group}")
    print("Records:", len(actual))

    if len(actual) == 0:
        continue

    print("Random Forest MAE:", mean_absolute_error(actual, pred))
    print("Persistence MAE:", mean_absolute_error(actual, base))
    print("Random Forest RMSE:", np.sqrt(mean_squared_error(actual, pred)))
    print("Persistence RMSE:", np.sqrt(mean_squared_error(actual, base)))
    print("Random Forest R2:", r2_score(actual, pred))

print("\nEvaluation completed.")
