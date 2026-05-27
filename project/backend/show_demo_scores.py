"""
Print Rule-Based vs ML scores for all DR999 demo trips side by side.
Run from: project/backend/
"""
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Force ML v2
os.environ["USE_ML_MODEL"] = "2"

from driver_module.scorer import calculate_trip_score
from driver_module.ml_scorer import calculate_trip_score_ml

DEMO_TRIPS = [
    {"id": "DEMO-CITY-01",  "route_type": "City",    "accel_events": 5,  "brake_events": 8,  "over_speed_count": 1, "cornering_events": 4, "idle_time_min": 18.0, "distance_km": 35.0, "trip_duration_min": 85.0,  "avg_speed_kmh": 26.0,  "max_speed_kmh": 48.0,  "num_stops": 22, "avg_engine_rpm": 1350.0},
    {"id": "DEMO-HWY-01",   "route_type": "Highway", "accel_events": 5,  "brake_events": 8,  "over_speed_count": 1, "cornering_events": 4, "idle_time_min": 18.0, "distance_km": 35.0, "trip_duration_min": 85.0,  "avg_speed_kmh": 88.0,  "max_speed_kmh": 118.0, "num_stops": 3,  "avg_engine_rpm": 2700.0},
    {"id": "DEMO-MTN-01",   "route_type": "Mountain","accel_events": 4,  "brake_events": 6,  "over_speed_count": 0, "cornering_events": 8, "idle_time_min": 10.0, "distance_km": 40.0, "trip_duration_min": 100.0, "avg_speed_kmh": 32.0,  "max_speed_kmh": 65.0,  "num_stops": 6,  "avg_engine_rpm": 2100.0},
    {"id": "DEMO-RRL-01",   "route_type": "Rural",   "accel_events": 4,  "brake_events": 6,  "over_speed_count": 0, "cornering_events": 8, "idle_time_min": 10.0, "distance_km": 40.0, "trip_duration_min": 100.0, "avg_speed_kmh": 32.0,  "max_speed_kmh": 65.0,  "num_stops": 6,  "avg_engine_rpm": 2100.0},
    {"id": "DEMO-HWY-AGG",  "route_type": "Highway", "accel_events": 9,  "brake_events": 12, "over_speed_count": 5, "cornering_events": 3, "idle_time_min": 5.0,  "distance_km": 80.0, "trip_duration_min": 75.0,  "avg_speed_kmh": 105.0, "max_speed_kmh": 148.0, "num_stops": 2,  "avg_engine_rpm": 3800.0},
    {"id": "DEMO-CITY-CLM", "route_type": "City",    "accel_events": 3,  "brake_events": 5,  "over_speed_count": 0, "cornering_events": 2, "idle_time_min": 20.0, "distance_km": 22.0, "trip_duration_min": 90.0,  "avg_speed_kmh": 20.0,  "max_speed_kmh": 38.0,  "num_stops": 28, "avg_engine_rpm": 1100.0},
]

print()
print("=" * 75)
print("  DR999 TEST DRIVER -- Rule-Based vs ML Score Comparison")
print("=" * 75)
print(f"  {'Trip ID':<18} {'Route':<10} {'Rule-Based':>11} {'ML v2':>8} {'Diff':>8}  Verdict")
print("-" * 75)

for t in DEMO_TRIPS:
    rule = calculate_trip_score(
        accel_events=t["accel_events"], brake_events=t["brake_events"],
        over_speed_count=t["over_speed_count"], cornering_events=t["cornering_events"],
        idle_time_min=t["idle_time_min"], trip_duration_min=t["trip_duration_min"],
        distance_km=t["distance_km"],
    )["final_score"]

    ml = calculate_trip_score_ml(
        accel_events=t["accel_events"], brake_events=t["brake_events"],
        over_speed_count=t["over_speed_count"], cornering_events=t["cornering_events"],
        idle_time_min=t["idle_time_min"], trip_duration_min=t["trip_duration_min"],
        distance_km=t["distance_km"], route_type=t["route_type"],
        avg_speed_kmh=t["avg_speed_kmh"], max_speed_kmh=t["max_speed_kmh"],
        num_stops=t["num_stops"], avg_engine_rpm=t["avg_engine_rpm"],
    )["final_score"]

    diff = round(ml - rule, 2)
    sign = "+" if diff > 0 else ""
    verdict = "ML more lenient" if diff > 0 else "ML more strict"
    print(f"  {t['id']:<18} {t['route_type']:<10} {rule:>11} {ml:>8} {sign+str(diff):>8}  {verdict}")

print("=" * 75)
print()
print("  PAIRS SUMMARY:")
print("  Pair 1 -- DEMO-CITY-01 vs DEMO-HWY-01   : Same events, Route changes score")
print("  Pair 2 -- DEMO-MTN-01  vs DEMO-RRL-01   : Same events, Mountain vs Rural")
print("  Pair 3 -- DEMO-HWY-AGG vs DEMO-CITY-CLM : Aggressive vs Calm driver")
print("=" * 75)
