from pathlib import Path
from functools import lru_cache
import math

import pandas as pd


# ============================================================
# PATHS AND CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

LATEST_FILE = ROOT / "reports" / "phase3" / "latest_station_readings.csv"
YEARLY_FILE = ROOT / "reports" / "phase3" / "yearly_station_summary.csv"
QUARTERLY_FILE = ROOT / "reports" / "phase3" / "representative_month_summary.csv"

EARTH_RADIUS_KM = 6371.0

EXACT_STATION_RADIUS_KM = 0.5
MAX_INTERPOLATION_DISTANCE_KM = 50.0
MAX_NEIGHBOUR_STATIONS = 5
MIN_INTERPOLATION_STATIONS = 3
MAX_READING_AGE_DAYS = 180

IDW_POWER = 2

# Provisional quality-control threshold. This is NOT a calibrated
# uncertainty interval. Validate it with spatial cross-validation.
MAX_WEIGHTED_SPATIAL_STD = 5.0

MONTH_ORDER = {
    "March": 3,
    "June": 6,
    "September": 9,
    "December": 12,
}


# ============================================================
# DATA LOADING
# ============================================================

@lru_cache(maxsize=1)
def load_estimation_data():
    """Load and validate the three Phase 3 summary datasets."""

    for file_path in (LATEST_FILE, YEARLY_FILE, QUARTERLY_FILE):
        if not file_path.exists():
            raise FileNotFoundError(
                f"Required estimation data file not found: {file_path}"
            )

    latest = pd.read_csv(LATEST_FILE)
    yearly = pd.read_csv(YEARLY_FILE)
    quarterly = pd.read_csv(QUARTERLY_FILE)

    required_latest = {
        "station", "datetime", "district",
        "latitude", "longitude", "wl_raw"
    }
    required_yearly = {
        "station", "district", "year", "average_wl",
        "minimum_wl", "maximum_wl", "reading_count",
        "first_reading", "last_reading"
    }
    required_quarterly = {
        "station", "district", "year", "representative_month",
        "average_wl", "minimum_wl", "maximum_wl", "reading_count"
    }

    for name, frame, required in (
        ("latest", latest, required_latest),
        ("yearly", yearly, required_yearly),
        ("quarterly", quarterly, required_quarterly),
    ):
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(
                f"{name} dataset is missing columns: {sorted(missing)}"
            )

    latest["datetime"] = pd.to_datetime(
        latest["datetime"], errors="coerce"
    )

    for column in ("latitude", "longitude", "wl_raw"):
        latest[column] = pd.to_numeric(
            latest[column], errors="coerce"
        )

    for frame in (yearly, quarterly):
        for column in (
            "year", "average_wl", "minimum_wl",
            "maximum_wl", "reading_count"
        ):
            frame[column] = pd.to_numeric(
                frame[column], errors="coerce"
            )

    latest = latest.dropna(
        subset=[
            "station", "datetime", "latitude",
            "longitude", "wl_raw"
        ]
    ).copy()

    yearly = yearly.dropna(
        subset=["station", "year", "average_wl"]
    ).copy()

    quarterly = quarterly.dropna(
        subset=["station", "year", "average_wl"]
    ).copy()

    latest = latest[
        latest["latitude"].between(-90, 90)
        & latest["longitude"].between(-180, 180)
    ].copy()

    latest["station"] = latest["station"].astype(str)
    yearly["station"] = yearly["station"].astype(str)
    quarterly["station"] = quarterly["station"].astype(str)

    yearly["year"] = yearly["year"].astype(int)
    quarterly["year"] = quarterly["year"].astype(int)

    # Keep one latest record per station if duplicate rows exist.
    latest = (
        latest.sort_values("datetime")
        .drop_duplicates(subset=["station"], keep="last")
        .reset_index(drop=True)
    )

    return latest, yearly, quarterly


def clear_estimation_cache():
    """Call this after replacing/updating the source CSV files."""
    load_estimation_data.cache_clear()


# ============================================================
# DISTANCE AND INPUT VALIDATION
# ============================================================

def haversine_km(lat1, lon1, lat2, lon2):
    """Calculate great-circle distance between two coordinates."""

    lat1, lon1, lat2, lon2 = map(
        math.radians, [lat1, lon1, lat2, lon2]
    )

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    # Guard against tiny floating-point overshoots.
    a = min(1.0, max(0.0, a))

    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def validate_coordinates(latitude, longitude):
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        raise ValueError("Latitude and longitude must be numeric.")

    if not math.isfinite(latitude) or not math.isfinite(longitude):
        raise ValueError("Coordinates must be finite numbers.")

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90.")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180.")

    return latitude, longitude


def validate_year(year):
    if year is None:
        return None

    try:
        year = int(year)
    except (TypeError, ValueError):
        raise ValueError("Year must be an integer.")

    available_years = {
        int(value)
        for value in load_estimation_data()[1]["year"].dropna().unique()
    }

    if year not in available_years:
        return None

    return year


# ============================================================
# STATION SEARCH AND HISTORY
# ============================================================

def find_nearby_stations(
    latitude,
    longitude,
    max_distance_km=MAX_INTERPOLATION_DISTANCE_KM,
):
    latest, _, _ = load_estimation_data()

    stations = latest.copy()

    stations["distance_km"] = stations.apply(
        lambda row: haversine_km(
            latitude,
            longitude,
            row["latitude"],
            row["longitude"],
        ),
        axis=1,
    )

    stations = stations[
        stations["distance_km"] <= max_distance_km
    ]

    return stations.sort_values("distance_km").reset_index(drop=True)


def get_station_history(station_name, year=None):
    _, yearly, quarterly = load_estimation_data()

    yearly_history = yearly[
        yearly["station"] == station_name
    ].copy()

    quarterly_history = quarterly[
        quarterly["station"] == station_name
    ].copy()

    if year is not None:
        yearly_history = yearly_history[
            yearly_history["year"] == int(year)
        ]
        quarterly_history = quarterly_history[
            quarterly_history["year"] == int(year)
        ]

    yearly_history = yearly_history.sort_values("year")

    quarterly_history["_month_order"] = (
        quarterly_history["representative_month"]
        .map(MONTH_ORDER)
        .fillna(99)
    )

    quarterly_history = (
        quarterly_history
        .sort_values(["year", "_month_order"])
        .drop(columns="_month_order")
    )

    return {
        "yearly": yearly_history.to_dict("records"),
        "quarterly": quarterly_history.to_dict("records"),
    }


# ============================================================
# DATA FRESHNESS
# ============================================================

def get_dataset_reference_date():
    latest, _, _ = load_estimation_data()
    return latest["datetime"].max()


def filter_recent_stations(stations):
    """Keep stations whose reading is recent relative to dataset max date."""

    if stations.empty:
        return stations.copy()

    reference_date = get_dataset_reference_date()

    age_days = (
        reference_date - stations["datetime"]
    ).dt.total_seconds() / 86400

    recent = stations.loc[
        age_days.between(0, MAX_READING_AGE_DAYS)
    ].copy()

    recent["age_days"] = age_days.loc[recent.index]

    return recent


# ============================================================
# EXACT STATION RESULT
# ============================================================

def exact_station_lookup(latitude, longitude, year=None):
    nearby = find_nearby_stations(
        latitude,
        longitude,
        max_distance_km=EXACT_STATION_RADIUS_KM,
    )

    if nearby.empty:
        return None

    station = nearby.iloc[0]
    station_name = station["station"]

    # A year-specific question must not be answered with a reading
    # from a different year.
    if year is not None:
        history = get_station_history(station_name, year)
        matching_year = history["yearly"]

        if not matching_year:
            return {
                "status": "historical_data_unavailable",
                "method": "exact_station_historical_lookup",
                "estimated": False,
                "station": station_name,
                "district": station["district"],
                "message": (
                    f"No yearly summary is available for {year} "
                    f"at station {station_name}."
                ),
            }

        annual = matching_year[0]

        return {
            "status": "success",
            "method": "exact_station_yearly_summary",
            "estimated": False,
            "station": station_name,
            "district": station["district"],
            "year": int(year),
            "groundwater_level": float(annual["average_wl"]),
            "unit": "meters",
            "value_type": "available-period average",
            "period_start": annual["first_reading"],
            "period_end": annual["last_reading"],
            "period_note": (
            "This average covers the available observation period, "
            "not necessarily the complete calendar year."
    ),
            "reading_count": int(annual["reading_count"]),
            "first_reading": annual["first_reading"],
            "last_reading": annual["last_reading"],
            "distance_km": round(float(station["distance_km"]), 3),
            "historical_data": history,
            "message": (
                f"Average of actual station observations available in {year}. "
                "The period may cover only part of the calendar year."
            ),
        }

    reference_date = get_dataset_reference_date()
    reading_date = station["datetime"]
    age_days = max(
        0.0, (reference_date - reading_date).total_seconds() / 86400
    )

    freshness = (
        "Recent"
        if age_days <= MAX_READING_AGE_DAYS
        else "Historical"
    )

    return {
        "status": "success",
        "method": "exact_station_reading",
        "estimated": False,
        "station": station_name,
        "district": station["district"],
        "groundwater_level": float(station["wl_raw"]),
        "unit": "meters",
        "value_type": "recorded reading",
        "reading_date": reading_date.isoformat(),
        "reading_age_days": round(age_days, 1),
        "freshness": freshness,
        "distance_km": round(float(station["distance_km"]), 3),
        "latitude": float(station["latitude"]),
        "longitude": float(station["longitude"]),
        "historical_data": get_station_history(station_name),
        "message": (
            "Actual recorded monitoring-station reading. "
            f"Freshness relative to the dataset's latest date: {freshness}."
        ),
    }


# ============================================================
# GENERIC IDW CALCULATION AND QUALITY CONTROL
# ============================================================

def calculate_idw(neighbours, value_column):
    """Return IDW value and weighted spatial standard deviation."""

    distances = neighbours["distance_km"].astype(float).tolist()
    values = neighbours[value_column].astype(float).tolist()

    if any(distance <= 0 for distance in distances):
        raise ValueError(
            "Zero-distance station should have been handled as exact lookup."
        )

    weights = [
        1.0 / (distance ** IDW_POWER)
        for distance in distances
    ]

    total_weight = sum(weights)

    estimate = sum(
        weight * value
        for weight, value in zip(weights, values)
    ) / total_weight

    variance = sum(
        weight * (value - estimate) ** 2
        for weight, value in zip(weights, values)
    ) / total_weight

    return estimate, math.sqrt(variance)


def insufficient_result(
    message,
    method,
    station_count=0,
    weighted_std=None,
    stations_used=None,
):
    result = {
        "status": "insufficient_data",
        "method": method,
        "estimated": True,
        "message": message,
        "available_station_count": int(station_count),
        "required_station_count": MIN_INTERPOLATION_STATIONS,
    }

    if weighted_std is not None:
        result["weighted_spatial_std"] = round(
            float(weighted_std), 3
        )

    if stations_used is not None:
        result["stations_used"] = stations_used

    return result


def assess_spatial_support(station_count, farthest_distance, weighted_std):
    """
    Descriptive support category only.
    This is not a probability or calibrated confidence score.
    """

    if (
        station_count >= 5
        and farthest_distance <= 20
        and weighted_std <= 2
    ):
        return "Good"

    if (
        station_count >= 3
        and farthest_distance <= 35
        and weighted_std <= 4
    ):
        return "Moderate"

    return "Limited"


# ============================================================
# CURRENT / LATEST SPATIAL ESTIMATION
# ============================================================

def idw_estimation(latitude, longitude):
    nearby = find_nearby_stations(
        latitude,
        longitude,
        max_distance_km=MAX_INTERPOLATION_DISTANCE_KM,
    )

    nearby = filter_recent_stations(nearby)

    if len(nearby) < MIN_INTERPOLATION_STATIONS:
        return insufficient_result(
            message=(
                "Not enough recent monitoring stations are available "
                "within the permitted distance. A spatial estimate "
                "cannot be supported by the available data."
            ),
            method="inverse_distance_weighting",
            station_count=len(nearby),
        )

    nearby = nearby.head(MAX_NEIGHBOUR_STATIONS).copy()

    estimate, weighted_std = calculate_idw(
        nearby, "wl_raw"
    )

    stations_used = [
        {
            "station": row["station"],
            "district": row["district"],
            "groundwater_level": float(row["wl_raw"]),
            "distance_km": round(float(row["distance_km"]), 3),
            "reading_date": row["datetime"].isoformat(),
        }
        for _, row in nearby.iterrows()
    ]

    if weighted_std > MAX_WEIGHTED_SPATIAL_STD:
        return insufficient_result(
            message=(
                "Nearby stations show substantial groundwater-level "
                "variation. The calculated IDW value has been withheld "
                "because the available spatial evidence is inconsistent."
            ),
            method="inverse_distance_weighting",
            station_count=len(nearby),
            weighted_std=weighted_std,
            stations_used=stations_used,
        )

    nearest_distance = float(nearby["distance_km"].min())
    farthest_distance = float(nearby["distance_km"].max())

    support = assess_spatial_support(
        len(nearby), farthest_distance, weighted_std
    )

    return {
        "status": "success",
        "method": "inverse_distance_weighting",
        "estimated": True,
        "groundwater_level": round(float(estimate), 3),
        "unit": "meters",
        "value_type": "spatially interpolated estimate",
        "station_count": len(nearby),
        "nearest_station_distance_km": round(nearest_distance, 3),
        "farthest_station_distance_km": round(farthest_distance, 3),
        "weighted_spatial_std": round(float(weighted_std), 3),
        "spatial_support": support,
        "reference_date": get_dataset_reference_date().isoformat(),
        "stations_used": stations_used,
        "message": (
            "Spatially interpolated estimate using nearby monitoring "
            "stations. It is not a direct measurement or a calibrated "
            "prediction interval."
        ),
    }


# ============================================================
# YEAR-SPECIFIC SPATIAL ESTIMATION
# ============================================================

def idw_year_estimation(latitude, longitude, year):
    """
    Interpolate annual station averages for the requested year.
    This is distinct from interpolating the latest station readings.
    """

    latest, yearly, _ = load_estimation_data()

    annual = yearly[yearly["year"] == int(year)].copy()

    if annual.empty:
        return {
            "status": "historical_data_unavailable",
            "method": "yearly_idw",
            "estimated": True,
            "message": f"No yearly station summaries are available for {year}.",
        }

    # Attach station coordinates from the latest station register.
    station_coordinates = latest[
        ["station", "latitude", "longitude"]
    ].drop_duplicates(subset=["station"])

    annual = annual.merge(
        station_coordinates,
        on="station",
        how="inner",
    )

    if annual.empty:
        return insufficient_result(
            "No station coordinates could be matched to the yearly records.",
            "yearly_idw",
        )

    annual["distance_km"] = annual.apply(
        lambda row: haversine_km(
            latitude,
            longitude,
            row["latitude"],
            row["longitude"],
        ),
        axis=1,
    )

    annual = annual[
        annual["distance_km"] <= MAX_INTERPOLATION_DISTANCE_KM
    ].sort_values("distance_km")

    if len(annual) < MIN_INTERPOLATION_STATIONS:
        return insufficient_result(
            (
                f"Fewer than {MIN_INTERPOLATION_STATIONS} stations have "
                f"yearly data for {year} within "
                f"{MAX_INTERPOLATION_DISTANCE_KM} km."
            ),
            "yearly_idw",
            station_count=len(annual),
        )

    annual = annual.head(MAX_NEIGHBOUR_STATIONS).copy()

    estimate, weighted_std = calculate_idw(
        annual, "average_wl"
    )

    stations_used = [
        {
            "station": row["station"],
            "district": row["district"],
            "annual_average_wl": float(row["average_wl"]),
            "distance_km": round(float(row["distance_km"]), 3),
            "reading_count": int(row["reading_count"]),
            "first_reading": row["first_reading"],
            "last_reading": row["last_reading"],
        }
        for _, row in annual.iterrows()
    ]

    if weighted_std > MAX_WEIGHTED_SPATIAL_STD:
        return insufficient_result(
            (
                f"Annual averages from nearby stations vary substantially "
                f"for {year}. The spatial estimate has been withheld."
            ),
            "yearly_idw",
            station_count=len(annual),
            weighted_std=weighted_std,
            stations_used=stations_used,
        )

    nearest_distance = float(annual["distance_km"].min())
    farthest_distance = float(annual["distance_km"].max())

    # These dates describe the combined outer bounds of the source
    # stations' available periods. They do NOT imply every station
    # has observations throughout this entire interval.
    first_dates = pd.to_datetime(
        annual["first_reading"], errors="coerce"
    )
    last_dates = pd.to_datetime(
        annual["last_reading"], errors="coerce"
    )

    period_start = (
        first_dates.min().isoformat()
        if first_dates.notna().any()
        else None
    )
    period_end = (
        last_dates.max().isoformat()
        if last_dates.notna().any()
        else None
    )

    station_periods = [
        {
            "station": row["station"],
            "period_start": row["first_reading"],
            "period_end": row["last_reading"],
        }
        for _, row in annual.iterrows()
    ]

    return {
        "status": "success",
        "method": "yearly_inverse_distance_weighting",
        "estimated": True,
        "year": int(year),
        "groundwater_level": round(float(estimate), 3),
        "unit": "meters",
        "value_type": "interpolated available-period average",
        "period_start": period_start,
        "period_end": period_end,
        "period_note": (
            "This estimate interpolates station averages over each "
            "station's available observation period. The periods may "
            "differ between stations and may cover only part of the "
            "requested calendar year. It is not a full-year average."
        ),
        "station_periods": station_periods,
        "station_count": len(annual),
        "nearest_station_distance_km": round(nearest_distance, 3),
        "farthest_station_distance_km": round(farthest_distance, 3),
        "weighted_spatial_std": round(float(weighted_std), 3),
        "spatial_support": assess_spatial_support(
            len(annual), farthest_distance, weighted_std
        ),
        "stations_used": stations_used,
        "message": (
            f"Spatial interpolation of available-period station averages "
            f"for {year}. This is not a direct measurement or a complete "
            "calendar-year average. Source stations may cover different "
            "date ranges; see station_periods."
        ),
    }


# ============================================================
# MAIN PUBLIC API
# ============================================================

def estimate_groundwater(latitude, longitude, year=None):
    """
    Main entry point.

    year=None:
        Exact station's latest recorded reading, or spatial estimate
        from recent station readings.

    year=YYYY:
        Exact station's available-period average, or spatial interpolation
        of available-period station averages for that year. Never
        substitutes another year or claims partial data is a full-year average.
    """

    latitude, longitude = validate_coordinates(
        latitude, longitude
    )

    latest, yearly, _ = load_estimation_data()

    available_years = sorted(
        int(value)
        for value in yearly["year"].dropna().unique()
    )

    if year is not None:
        try:
            year = int(year)
        except (TypeError, ValueError):
            raise ValueError("Year must be an integer.")

        if year not in available_years:
            return {
                "status": "invalid_year",
                "message": (
                    f"Year {year} is unavailable. Available years: "
                    f"{available_years}."
                ),
            }

    # Exact station result takes priority.
    exact = exact_station_lookup(
        latitude, longitude, year=year
    )

    if exact is not None:
        return exact

    # Year-specific questions use that year's annual summaries.
    if year is not None:
        result = idw_year_estimation(
            latitude, longitude, year
        )

        if result.get("status") == "success":
            nearest = result["stations_used"][0]["station"]
            result["nearest_station"] = nearest
            result["historical_data"] = get_station_history(
                nearest, year
            )

        return result

    # Unqualified/current questions use recent station readings.
    result = idw_estimation(latitude, longitude)

    if result.get("status") == "success":
        nearest = result["stations_used"][0]["station"]
        result["nearest_station"] = nearest
        result["historical_data"] = get_station_history(nearest)

    return result
