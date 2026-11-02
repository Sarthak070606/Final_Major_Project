
import pandas as pd
from pathlib import Path

files = [
    Path("data/raw/gwl_tel_6_hourly_madhya_pradesh_gw_mp_2021_2025.csv"),
    Path("data/raw/gwl_tel_6_hourly_cgwb_mp_2026_2030.csv"),
]

stations = [
    "Chandranagar_2",
    "Bhakhuri",
    "Khategaon_1",
    "Lohana-ii",
]

columns = [
    "Station",
    "District",
    "RL_MSL",
    "Data Acquisition Time",
    "Groundwater Level Telemetry 6 Hourly (meter)",
]

for file in files:
    if not file.exists():
        print(f"\nFILE NOT FOUND: {file}")
        continue

    print(f"\n{'=' * 70}\nFILE: {file.name}\n{'=' * 70}")

    found = 0

    for chunk in pd.read_csv(
        file,
        usecols=columns,
        chunksize=300_000,
        low_memory=False
    ):
        chunk["Station"] = chunk["Station"].astype(str).str.strip()

        mask = chunk["Station"].str.contains(
            "|".join(stations),
            case=False,
            na=False,
            regex=True
        )

        matched = chunk.loc[mask].copy()

        if not matched.empty:
            matched["Data Acquisition Time"] = pd.to_datetime(
                matched["Data Acquisition Time"],
                format="%d-%m-%Y %H:%M",
                errors="coerce"
            )

            matched["Groundwater Level Telemetry 6 Hourly (meter)"] = (
                pd.to_numeric(
                    matched["Groundwater Level Telemetry 6 Hourly (meter)"],
                    errors="coerce"
                )
            )

            print(matched.to_string(index=False))
            found += len(matched)

    print(f"\nTotal matching original records: {found}")
