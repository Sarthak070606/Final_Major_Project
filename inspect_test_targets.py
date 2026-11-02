
import pandas as pd
import numpy as np

path = "data/processed/phase2/test.parquet"

df = pd.read_parquet(path)

target = "target_wl_t_plus_1"

print("\n========== TEST TARGET SUMMARY ==========")
print(df[target].describe(
    percentiles=[0.50, 0.90, 0.95, 0.99, 0.999]
))

print("\n========== EXTREME TARGET COUNTS ==========")

for limit in [100, 150, 500, 1000, 10000]:
    count = (df[target].abs() > limit).sum()
    print(f"Absolute target > {limit}: {count:,}")

print("\n========== TOP 30 EXTREME RECORDS ==========")

columns = [
    c for c in [
        "station",
        "datetime",
        "wl_raw",
        "target_wl_t_plus_1",
        "flag_any_suspicious"
    ]
    if c in df.columns
]

extreme = df.loc[
    df[target].abs().nlargest(30).index,
    columns
]

print(extreme.to_string(index=False))

print("\n========== DATA QUALITY ==========")
print("Missing targets:", df[target].isna().sum())
print("Infinite targets:", np.isinf(df[target]).sum())

print("\nInspection completed.")
