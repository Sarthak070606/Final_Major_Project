
import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from src.training.config_phase2 import FEATURE_COLS, TARGET_COL

TEST_PATH = "data/processed/phase2/test.parquet"
MODEL_PATH = "models/best_model.joblib"

print("Loading test dataset...")
df = pd.read_parquet(TEST_PATH)

print("Loading trained model...")
model = joblib.load(MODEL_PATH)

X = df[FEATURE_COLS].to_numpy(dtype=np.float64)
y = df[TARGET_COL].to_numpy(dtype=np.float64)

print("\n========== ALL TEST RECORDS ==========")

predictions = model.predict(X)

def show_metrics(name, actual, predicted):
    print(f"\n{name}")
    print("Records:", len(actual))
    print("MAE:", mean_absolute_error(actual, predicted))
    print("RMSE:", np.sqrt(mean_squared_error(actual, predicted)))
    print("R2:", r2_score(actual, predicted))

show_metrics("All records", y, predictions)

# Groundwater-related input features only
groundwater_features = [
    col for col in FEATURE_COLS
    if col.startswith("wl_")
    or col.startswith("lag_")
    or col.startswith("rolling_")
]

# Keep plausible targets and plausible groundwater input features
mask = (
    np.isfinite(y)
    & (np.abs(y) <= 150)
    & np.isfinite(X).all(axis=1)
)

for col in groundwater_features:
    values = df[col].to_numpy(dtype=np.float64)
    mask &= np.isfinite(values) & (np.abs(values) <= 150)

print("\n========== QUALITY-FILTERED TEST ==========")
print("Original records:", len(df))
print("Retained records:", int(mask.sum()))
print("Excluded records:", int((~mask).sum()))

show_metrics(
    "Filtered test records",
    y[mask],
    predictions[mask]
)

# Persistence baseline: predict the current groundwater level
wl_index = FEATURE_COLS.index("wl_raw")
baseline_predictions = X[:, wl_index]

show_metrics(
    "Filtered persistence baseline",
    y[mask],
    baseline_predictions[mask]
)

print("\nEvaluation completed.")