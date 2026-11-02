
import pyarrow.parquet as pq

files = [
    "data/processed/phase2/features_clean_v2.parquet",
    "data/processed/features_lag_rolling.parquet"
]

for file in files:
    print("\n" + "=" * 70)
    print("FILE:", file)

    parquet_file = pq.ParquetFile(file)

    print("Total rows:", parquet_file.metadata.num_rows)
    print("Total columns:", len(parquet_file.schema.names))
    print("\nCOLUMN NAMES:")

    for column in parquet_file.schema.names:
        print("-", column)

    print("\nSAMPLE DATA:")
    sample = parquet_file.read_row_group(0).slice(0, 2)
    print(sample.to_pandas().to_string(index=False))
