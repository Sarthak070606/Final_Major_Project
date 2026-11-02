
from dashboard.utils.estimation_engine import (
    estimate_groundwater,
    load_estimation_data
)

# Confirm data loading
latest, yearly, quarterly = load_estimation_data()

print("Stations:", len(latest))
print("Yearly records:", len(yearly))
print("Quarterly records:", len(quarterly))

# Test 1: University Campus, Bhopal
result = estimate_groundwater(
    latitude=23.13333,
    longitude=77.46667,
    year=2025
)

print("\nTEST 1: UNIVERSITY CAMPUS")
print(result)

# Test 2: SVVV, Indore
result = estimate_groundwater(
    latitude=22.81796,
    longitude=75.84781,
    year=2026
)

print("\nTEST 2: SVVV INDORE")
print(result)

# Test 3: A location with potentially insufficient coverage
result = estimate_groundwater(
    latitude=22.0,
    longitude=78.0
)

print("\nTEST 3: COVERAGE CHECK")
print(result)
