
from dashboard.views.chatbot import (
    extract_location,
    geocode_location,
)

from dashboard.utils.chatbot_service import location_year_answer


test_cases = [
    {
        "question": "what is ground water level of rj wada indore currently",
        "year": None,
    },
    {
        "question": "what is groundwater level in sagar makronia in 2026",
        "year": 2026,
    },
    {
        "question": "show groundwater data for bhopal in 2025",
        "year": 2025,
    },
]


for test in test_cases:

    question = test["question"]
    year = test["year"]

    location = extract_location(question)

    coordinates = geocode_location(location)

    print("\n" + "=" * 65)
    print("QUESTION:", question)
    print("LOCATION:", location)
    print("COORDINATES:", coordinates)

    if coordinates is None:
        print("RESULT: Location could not be verified.")
        continue

    latitude, longitude = coordinates

    result = location_year_answer(
        latitude,
        longitude,
        year,
    )

    print("\nGROUNDWATER RESULT:")
    print(result)
