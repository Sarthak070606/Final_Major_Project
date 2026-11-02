
import re
import requests


# ============================================================
# LOCATION EXTRACTION
# ============================================================


def extract_location(question):
    """Extract a clean locality, village, or city from a question."""

    q = question.lower().strip()

    # Remove years.
    q = re.sub(r"\b20(?:2[1-6])\b", " ", q)

    # Remove time expressions.
    q = re.sub(
        r"\b(currently|today|now|latest|recently)\b",
        " ",
        q
    )

    # Remove leftover trailing prepositions.
    q = re.sub(
        r"\b(in|at|for|of|near|around)\s*$",
        "",
        q
    )

    # Extract location after a preposition.
    match = re.search(
        r"\b(?:in|at|near|around|of|for)\s+(.+)$",
        q
    )

    if not match:
        return None

    location = match.group(1).strip()

    # Remove question-related words.
    stop_words = [
        "groundwater", "ground water", "ground-water",
        "water level", "water table", "level",
        "readings", "reading", "data", "show",
        "what is", "tell me", "give me",
        "please", "find", "get", "the", "ground"
    ]

    for word in stop_words:
        location = re.sub(
            rf"\b{re.escape(word)}\b",
            " ",
            location
        )

    location = re.sub(r"\s+", " ", location).strip(" ,.-")

    return location.title() if location else None

# ============================================================
# LOCATION NORMALIZATION
# ============================================================

def normalize_location(location):
    """Normalize common spelling variations of MP locations."""

    normalized = re.sub(
        r"[^a-z0-9 ]",
        " ",
        location.lower()
    )

    normalized = re.sub(r"\s+", " ", normalized).strip()

    aliases = {
        "rj wada indore": "Rajwada, Indore",
        "rj wada": "Rajwada, Indore",
        "raj wada indore": "Rajwada, Indore",
        "rajwada indore": "Rajwada, Indore",
        "indore rajwada": "Rajwada, Indore",

        "makronia sagar": "Makronia, Sagar",
        "sagar makronia": "Makronia, Sagar",

        "svvv indore": "Shri Vaishnav Vidyapeeth Vishwavidyalaya, Indore",
    }

    return aliases.get(normalized, location.strip())


# ============================================================
# GEOCODING
# ============================================================

def geocode_location(location):
    """
    Resolve a location using OpenStreetMap Nominatim.

    Only accepts verified locations in Madhya Pradesh, India.
    Returns (latitude, longitude), otherwise None.
    """

    if not location or not location.strip():
        return None

    search_location = normalize_location(location)

    queries = [
        f"{search_location}, Madhya Pradesh, India",
        f"{search_location}, India",
    ]

    # Specific locality alternatives.
    lower = search_location.lower()

    if "makronia" in lower:
        queries.insert(
            0,
            "Makronia, Sagar district, Madhya Pradesh, India"
        )

    if "rajwada" in lower:
        queries.insert(
            0,
            "Rajwada, Indore, Madhya Pradesh, India"
        )

    headers = {
        "User-Agent": "MPGroundwaterIntelligence/1.0"
    }

    for query in queries:
        try:
            response = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": query,
                    "format": "jsonv2",
                    "addressdetails": 1,
                    "limit": 5,
                    "countrycodes": "in",
                },
                headers=headers,
                timeout=15,
            )

            response.raise_for_status()

            results = response.json()

            for result in results:
                address = result.get("address", {})

                country = address.get(
                    "country", ""
                ).lower()

                state = address.get(
                    "state", ""
                ).lower()

                # Strict geographical validation.
                if country != "india":
                    continue

                if "madhya pradesh" not in state:
                    continue

                latitude = float(result["lat"])
                longitude = float(result["lon"])

                return latitude, longitude

        except requests.RequestException:
            continue

        except (ValueError, KeyError, TypeError):
            continue

    return None
