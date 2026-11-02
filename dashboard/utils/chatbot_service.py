from pathlib import Path
import sqlite3

import pandas as pd
import ollama

from dashboard.utils.estimation_engine import (
    estimate_groundwater,
    load_estimation_data,
)


# ============================================================
# PROJECT PATHS AND CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

LATEST_FILE = ROOT / "reports" / "phase3" / "latest_station_readings.csv"
YEARLY_FILE = ROOT / "reports" / "phase3" / "yearly_station_summary.csv"
QUARTERLY_FILE = ROOT / "reports" / "phase3" / "representative_month_summary.csv"

DB_DIR = ROOT / "data" / "chatbot"
DB_PATH = DB_DIR / "suggestions.db"

MODEL_NAME = "llama3.2:latest"


# ============================================================
# DATA ACCESS
# ============================================================

def load_data():
    """Load existing project datasets."""
    latest, yearly, quarterly = load_estimation_data()
    return latest.copy(), yearly.copy(), quarterly.copy()


def nearest_station(latitude, longitude):
    """
    Find the nearest monitoring station.

    The returned reading belongs to the station, not the searched
    location. Kept for compatibility with earlier dashboard code.
    """
    result = estimate_groundwater(latitude, longitude)
    stations = result.get("stations_used", [])

    if result.get("method") == "exact_station_reading":
        return {
            "station": result.get("station"),
            "district": result.get("district"),
            "distance_km": result.get("distance_km"),
            "wl_raw": result.get("groundwater_level"),
            "datetime": result.get("reading_date"),
            "latitude": result.get("latitude"),
            "longitude": result.get("longitude"),
            "estimated": False,
        }

    if stations:
        nearest = stations[0]
        return {
            "station": nearest.get("station"),
            "district": nearest.get("district"),
            "distance_km": nearest.get("distance_km"),
            "wl_raw": nearest.get(
                "groundwater_level",
                nearest.get("annual_average_wl"),
            ),
            "datetime": (
                nearest.get("reading_date")
                or nearest.get("last_reading")
            ),
            "estimated": False,
        }

    return None


# ============================================================
# ESTIMATION RESULT FORMATTING
# ============================================================

def _display_station_name(value):
    """Make station names readable without changing source data."""
    return str(value if value is not None else "Unknown station").replace("_", " ")


def _format_number(value, decimals=3):
    """Format numeric values compactly while retaining their sign."""
    try:
        number = float(value)
        return f"{number:.{decimals}f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return str(value)


def _format_station_list(stations):
    """
    Format station observations without presenting them as a reading
    at the searched location.
    """
    if not stations:
        return "No supporting station details are available."

    lines = []

    for index, item in enumerate(stations, start=1):
        value = item.get(
            "annual_average_wl",
            item.get("groundwater_level"),
        )

        if value is None:
            value_text = "Unavailable"
        else:
            value_text = f"{_format_number(value)} m"

        distance = item.get("distance_km")
        distance_text = (
            f"{_format_number(distance)} km"
            if distance is not None
            else "Unavailable"
        )

        # For yearly summaries, show the complete available date range.
        first_reading = item.get("first_reading")
        last_reading = item.get("last_reading")
        if first_reading or last_reading:
            period_text = (
                f"{first_reading or 'Start unavailable'} to "
                f"{last_reading or 'End unavailable'}"
            )
        else:
            period_text = (
                item.get("reading_date")
                or "Date unavailable"
            )

        station_name = _display_station_name(item.get("station"))
        district = str(item.get("district") or "District unavailable")

        lines.extend([
            f"{index}. **{station_name}** ({district})",
            f"   - Reading: {value_text}",
            f"   - Distance: {distance_text}",
            f"   - Observation/available period: {period_text}",
            "",
        ])

    return "\n".join(lines).rstrip()


def format_estimation_result(result):
    """
    Convert deterministic estimation output into readable, grounded text.

    If interpolation is rejected, show nearby station observations
    supplied by the estimation engine. Never calculate a replacement value.
    """
    status = result.get("status", "unknown")
    method = result.get("method", "unknown")
    estimated = result.get("estimated", False)
    stations = result.get("stations_used", [])

    # --------------------------------------------------------
    # Unsuccessful / withheld estimate
    # --------------------------------------------------------
    if status != "success":
        lines = [
            "GROUNDWATER RESULT: NO RELIABLE VALUE AVAILABLE",
            "",
            "## A reliable groundwater estimate is unavailable",
            result.get(
                "message",
                "The available monitoring data does not support a reliable estimate.",
            ),
            "",
            "### Estimation details",
            f"- **Status:** {status}",
            f"- **Method attempted:** {method}",
        ]

        station_count = result.get("available_station_count")
        if station_count is not None:
            lines.append(f"- **Nearby stations available:** {station_count}")

        spatial_std = result.get("weighted_spatial_std")
        if spatial_std is not None:
            lines.append(
                f"- **Weighted spatial variation:** "
                f"{_format_number(spatial_std)} m"
            )

        if stations:
            lines.extend([
                "",
                "## Nearby monitoring stations",
                "",
                _format_station_list(stations),
            ])
        else:
            lines.extend([
                "",
                "No nearby station observations were returned by the estimation engine.",
            ])

        lines.extend([
            "",
            "### Important interpretation",
            "The readings above belong to the individual monitoring stations. "
            "They are **not measurements at the searched location** and must "
            "not be combined or treated as a groundwater estimate for that location.",
            "",
            "**No groundwater value has been calculated or guessed.**",
        ])

        return "\n".join(lines)

    # --------------------------------------------------------
    # Successful estimate
    # --------------------------------------------------------
    value = result.get("groundwater_level")

    lines = [
        "GROUNDWATER RESULT: SUCCESS",
        "",
        "## Groundwater result",
        f"- **Groundwater level:** {_format_number(value)} m",
        f"- **Value type:** {result.get('value_type', 'Not specified')}",
        f"- **Method:** {method}",
        f"- **Estimated:** {'Yes' if estimated else 'No'}",
    ]

    if result.get("year") is not None:
        lines.append(f"- **Requested year:** {result['year']}")

    if result.get("station"):
        lines.append(
            f"- **Monitoring station:** "
            f"{_display_station_name(result['station'])}"
        )

    if result.get("district"):
        lines.append(f"- **District:** {result['district']}")

    if result.get("reading_date"):
        lines.append(f"- **Reading date:** {result['reading_date']}")

    if result.get("reading_age_days") is not None:
        lines.append(
            f"- **Reading age relative to dataset reference date:** "
            f"{_format_number(result['reading_age_days'], 1)} days"
        )
        lines.append(
            f"- **Freshness:** {result.get('freshness', 'Unknown')}"
        )

    if result.get("period_start"):
        lines.append(f"- **Period start:** {result['period_start']}")

    if result.get("period_end"):
        lines.append(f"- **Period end:** {result['period_end']}")

    if result.get("distance_km") is not None:
        lines.append(
            f"- **Distance to station:** "
            f"{_format_number(result['distance_km'])} km"
        )

    if result.get("station_count") is not None:
        lines.append(f"- **Stations used:** {result['station_count']}")

    if result.get("nearest_station_distance_km") is not None:
        lines.append(
            f"- **Nearest station distance:** "
            f"{_format_number(result['nearest_station_distance_km'])} km"
        )

    if result.get("farthest_station_distance_km") is not None:
        lines.append(
            f"- **Farthest station distance:** "
            f"{_format_number(result['farthest_station_distance_km'])} km"
        )

    if result.get("weighted_spatial_std") is not None:
        lines.append(
            f"- **Weighted spatial variation:** "
            f"{_format_number(result['weighted_spatial_std'])} m"
        )

    if result.get("spatial_support"):
        lines.append(
            f"- **Spatial support:** {result['spatial_support']}"
        )

    if result.get("message"):
        lines.extend(["", f"**Details:** {result['message']}"])

    if result.get("period_note"):
        lines.extend(["", f"**Observation-period note:** {result['period_note']}"])

    station_periods = result.get("station_periods") or []
    if station_periods:
        lines.extend(["", "## Available period for each station"])
        for item in station_periods:
            station_name = _display_station_name(item.get("station"))
            lines.append(
                f"- **{station_name}:** "
                f"{item.get('period_start') or 'Start unavailable'} to "
                f"{item.get('period_end') or 'End unavailable'}"
            )

    if stations:
        lines.extend([
            "",
            "## Supporting monitoring stations",
            "",
            _format_station_list(stations),
        ])

    history = result.get("historical_data") or {}

    yearly_history = history.get("yearly") or []
    if yearly_history:
        lines.extend(["", "## Yearly station history"])
        for row in yearly_history:
            lines.append(
                f"- **{row.get('year', 'Unknown year')}:** "
                f"available-period average {_format_number(row.get('average_wl'))} m; "
                f"minimum {_format_number(row.get('minimum_wl'))} m; "
                f"maximum {_format_number(row.get('maximum_wl'))} m; "
                f"records {row.get('reading_count')}; "
                f"period {row.get('first_reading')} to "
                f"{row.get('last_reading')}"
            )

    quarterly_history = history.get("quarterly") or []
    if quarterly_history:
        lines.extend(["", "## Representative-month history"])
        for row in quarterly_history:
            lines.append(
                f"- **{row.get('year')} "
                f"{row.get('representative_month')}:** "
                f"average {_format_number(row.get('average_wl'))} m; "
                f"records {row.get('reading_count')}"
            )

    lines.extend([
        "",
        "### Interpretation",
        "Groundwater readings retain the sign convention used in the source dataset. "
        "Negative values have not been converted to positive values.",
    ])

    if estimated:
        lines.append(
            "This is a **spatial estimate**, not a direct measurement at the "
            "searched location, home, or borewell."
        )

    return "\n".join(lines)


# ============================================================
# LOCATION-BASED GROUNDWATER SERVICE
# ============================================================

def location_year_answer(latitude, longitude, year=None):
    """
    Return grounded text from the deterministic estimation engine.

    If the engine cannot support a value, nearby station observations
    are still displayed when the engine supplies them.
    """
    try:
        result = estimate_groundwater(
            latitude=latitude,
            longitude=longitude,
            year=year,
        )
        return format_estimation_result(result)

    except (ValueError, TypeError) as exc:
        return (
            "GROUNDWATER RESULT: INVALID LOCATION OR YEAR\n"
            f"Details: {exc}\n"
            "Do not invent a groundwater reading."
        )

    except FileNotFoundError as exc:
        return (
            "GROUNDWATER RESULT: DATA FILE UNAVAILABLE\n"
            f"Details: {exc}\n"
            "Do not invent a groundwater reading."
        )


def location_answer(latitude, longitude):
    """Backward-compatible location answer helper."""
    return location_year_answer(latitude, longitude)


# ============================================================
# PROJECT INFORMATION
# ============================================================

def project_information():
    return """
PROJECT:
AI-Enabled Groundwater Monitoring, Prediction and Well Suitability
Assessment System for Madhya Pradesh.

DEVELOPER:
Sarthak Jain

COURSE:
B.Tech CSE (AI-IBM)

INSTITUTION:
Shri Vaishnav Vidyapeeth Vishwavidyalaya.

TECHNOLOGIES:
Python, Pandas, Machine Learning, Streamlit, Plotly, Ollama.

CURRENT DATA:
4,097,128 records
1,379 monitoring stations
52 districts
Available historical years: 2021-2026.

AVAILABLE FEATURES:
Groundwater monitoring, historical analysis, quarterly analysis,
AI prediction, location-based station search, data quality analysis,
model performance analysis.

NOT YET INTEGRATED:
Verified soil and geology datasets, laboratory-based water quality
analysis, rainfall-based forecasting and verified well suitability.

LIMITATION:
Groundwater telemetry alone cannot establish drinking-water safety,
borewell yield, drilling depth or household borewell suitability.
"""


# ============================================================
# USER SUGGESTIONS - SQLITE
# ============================================================

def save_suggestion(suggestion, category="General"):
    """Save user suggestions in SQLite."""

    suggestion = str(suggestion).strip()
    category = str(category).strip() or "General"

    if not suggestion:
        raise ValueError("Suggestion cannot be empty.")

    DB_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                suggestion TEXT NOT NULL,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'Pending'
            )
            """
        )

        conn.execute(
            """
            INSERT INTO suggestions (suggestion, category)
            VALUES (?, ?)
            """,
            (suggestion, category),
        )

    return True


def get_suggestions():
    """Return saved suggestions."""

    if not DB_PATH.exists():
        return pd.DataFrame()

    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            "SELECT * FROM suggestions ORDER BY id DESC",
            conn,
        )


# ============================================================
# OLLAMA ANSWER GENERATION
# ============================================================

def generate_answer(question, context=""):
    """
    Generate a natural-language answer using Ollama.

    Deterministic groundwater results are authoritative. A withheld
    estimate is returned directly, including its nearby station details,
    so the LLM cannot invent a replacement groundwater value.
    """
    context_text = str(context or "")

    no_reliable_groundwater_value = (
        "GROUNDWATER RESULT: NO RELIABLE VALUE AVAILABLE"
        in context_text
        or "GROUNDWATER RESULT: INVALID LOCATION OR YEAR"
        in context_text
        or "GROUNDWATER RESULT: DATA FILE UNAVAILABLE"
        in context_text
    )

    if no_reliable_groundwater_value:
        return (
            "I couldn't produce a reliable groundwater-level estimate "
            "for this location or year from the available monitoring data.\n\n"
            + context_text
        )

    prompt = f"""
You are the AI assistant for a Madhya Pradesh groundwater
monitoring and prediction application.

Answer the user's question clearly and concisely.

STRICT RULES:
1. Use only the supplied project information and retrieved data for
   project-specific factual claims.
2. Never invent groundwater readings, dates, stations, coordinates,
   historical values, distances, or statistics.
3. If retrieved data does not contain an answer, say it is unavailable.
4. Preserve the negative or positive sign of groundwater values exactly
   as supplied by the source data.
5. Clearly distinguish an actual station reading from a spatial estimate.
6. A station reading is not a direct measurement of a user's house,
   village, or borewell.
7. Do not describe an available-period average as a complete annual
   average unless the supplied dates establish full-year coverage.
8. Do not claim drinking water is safe without laboratory results.
9. Do not infer borewell yield, drilling depth, or well suitability
   from groundwater-level telemetry alone.
10. Explain technical concepts in simple language.
11. If the user asks about a location but the retrieved context has no
    reliable value, clearly state that no reliable estimate is available.
12. Do not calculate a replacement groundwater value from nearby
    station values unless the estimation engine has supplied a successful
    estimate.

PROJECT INFORMATION:
{project_information()}

RETRIEVED DATA:
{context_text}

USER QUESTION:
{question}
"""

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.1},
    )

    return response["message"]["content"]
