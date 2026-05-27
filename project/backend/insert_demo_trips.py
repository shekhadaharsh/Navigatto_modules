"""
Add demo trips for DR999 (Test Driver) to show Rule-Based vs ML score difference.

DEMO TRIPS DESIGN:
  Pair 1 (Trip DEMO-01 vs DEMO-02): Same events, City vs Highway
  Pair 2 (Trip DEMO-03 vs DEMO-04): Same events, Mountain vs Rural  
  Pair 3 (Trip DEMO-05 vs DEMO-06): High speed highway vs Calm city

These trips are designed so Rule-Based gives SAME/SIMILAR scores,
but ML gives CLEARLY DIFFERENT scores based on context.

Run from: project/backend/
"""

import os, sys, uuid
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.db import SessionLocal
from driver_module.model import Trip, JourneyScore
from driver_module.scorer import calculate_trip_score
from sqlalchemy import text

DRIVER_ID  = "DR999"
VEHICLE_ID = "FD4981DD-FCC3-4B94-A674-011E45C3048A"
BASE_TIME  = datetime(2025, 6, 1, 8, 0, 0)

# ── 6 Demo Trips ──────────────────────────────────────────────────
# Each trip has all required fields.
# "note" field is just for our reference, not inserted to DB.
DEMO_TRIPS = [
    # ── PAIR 1: Same events, City vs Highway ──────────────────────
    {
        "trip_id":           "DEMO-CITY-01",
        "route_type":        "City",
        "accel_events":      5,
        "brake_events":      8,
        "over_speed_count":  1,
        "cornering_events":  4,
        "idle_time_min":     18.0,
        "distance_km":       35.0,
        "trip_duration_min": 85.0,
        "avg_speed_kmh":     26.0,
        "max_speed_kmh":     48.0,
        "num_stops":         22,
        "avg_engine_rpm":    1350.0,
        "note":              "PAIR-1 CITY -- mild city rush hour",
        "offset_days":       0,
    },
    {
        "trip_id":           "DEMO-HWY-01",
        "route_type":        "Highway",
        "accel_events":      5,
        "brake_events":      8,
        "over_speed_count":  1,
        "cornering_events":  4,
        "idle_time_min":     18.0,
        "distance_km":       35.0,
        "trip_duration_min": 85.0,
        "avg_speed_kmh":     88.0,
        "max_speed_kmh":     118.0,
        "num_stops":         3,
        "avg_engine_rpm":    2700.0,
        "note":              "PAIR-1 HIGHWAY -- same events, very different risk",
        "offset_days":       1,
    },

    # ── PAIR 2: Mountain vs Rural ──────────────────────────────────
    {
        "trip_id":           "DEMO-MTN-01",
        "route_type":        "Mountain",
        "accel_events":      4,
        "brake_events":      6,
        "over_speed_count":  0,
        "cornering_events":  8,
        "idle_time_min":     10.0,
        "distance_km":       40.0,
        "trip_duration_min": 100.0,
        "avg_speed_kmh":     32.0,
        "max_speed_kmh":     65.0,
        "num_stops":         6,
        "avg_engine_rpm":    2100.0,
        "note":              "PAIR-2 MOUNTAIN -- corners normal on mountain but multiplier 1.30",
        "offset_days":       2,
    },
    {
        "trip_id":           "DEMO-RRL-01",
        "route_type":        "Rural",
        "accel_events":      4,
        "brake_events":      6,
        "over_speed_count":  0,
        "cornering_events":  8,
        "idle_time_min":     10.0,
        "distance_km":       40.0,
        "trip_duration_min": 100.0,
        "avg_speed_kmh":     32.0,
        "max_speed_kmh":     65.0,
        "num_stops":         6,
        "avg_engine_rpm":    2100.0,
        "note":              "PAIR-2 RURAL -- identical, neutral multiplier 1.00",
        "offset_days":       3,
    },

    # ── PAIR 3: Aggressive Highway vs Calm City ────────────────────
    {
        "trip_id":           "DEMO-HWY-AGG",
        "route_type":        "Highway",
        "accel_events":      9,
        "brake_events":      12,
        "over_speed_count":  5,
        "cornering_events":  3,
        "idle_time_min":     5.0,
        "distance_km":       80.0,
        "trip_duration_min": 75.0,
        "avg_speed_kmh":     105.0,
        "max_speed_kmh":     148.0,
        "num_stops":         2,
        "avg_engine_rpm":    3800.0,
        "note":              "PAIR-3 AGGRESSIVE HIGHWAY -- ML will punish heavily",
        "offset_days":       4,
    },
    {
        "trip_id":           "DEMO-CITY-CLM",
        "route_type":        "City",
        "accel_events":      3,
        "brake_events":      5,
        "over_speed_count":  0,
        "cornering_events":  2,
        "idle_time_min":     20.0,
        "distance_km":       22.0,
        "trip_duration_min": 90.0,
        "avg_speed_kmh":     20.0,
        "max_speed_kmh":     38.0,
        "num_stops":         28,
        "avg_engine_rpm":    1100.0,
        "note":              "PAIR-3 CALM CITY -- ML will reward heavily",
        "offset_days":       5,
    },
]


def insert_demo_trips():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("Inserting Demo Trips for DR999 (Test Driver)")
        print("=" * 60)

        for td in DEMO_TRIPS:
            trip_id = td["trip_id"]

            # Check if already exists
            existing = db.query(Trip).filter(Trip.trip_id == trip_id).first()
            if existing:
                print(f"  [SKIP] {trip_id} already exists.")
                continue

            start_time = BASE_TIME + timedelta(days=td["offset_days"])
            end_time   = start_time + timedelta(minutes=td["trip_duration_min"])

            # Calculate rule-based score for journey_scores table
            rule_result = calculate_trip_score(
                accel_events=td["accel_events"],
                brake_events=td["brake_events"],
                over_speed_count=td["over_speed_count"],
                cornering_events=td["cornering_events"],
                idle_time_min=td["idle_time_min"],
                trip_duration_min=td["trip_duration_min"],
                distance_km=td["distance_km"],
            )
            rule_score = rule_result["final_score"]

            # Insert into dbo.journeys
            trip = Trip(
                trip_id          = trip_id,
                vehicle_id       = VEHICLE_ID,
                driver_id        = DRIVER_ID,
                route_type       = td["route_type"],
                trip_start       = start_time,
                trip_end         = end_time,
                trip_duration_min= td["trip_duration_min"],
                distance_km      = td["distance_km"],
                avg_speed_kmh    = td["avg_speed_kmh"],
                max_speed_kmh    = td["max_speed_kmh"],
                idle_time_min    = td["idle_time_min"],
                num_stops        = td["num_stops"],
                accel_events     = td["accel_events"],
                brake_events     = td["brake_events"],
                over_speed_count = td["over_speed_count"],
                cornering_events = td["cornering_events"],
                avg_engine_rpm   = td["avg_engine_rpm"],
                # Reasonable defaults for non-scoring columns
                load_pct            = 45.0,
                temp_celsius        = 28.0,
                hour_of_day         = 9,
                day_of_week         = "Monday",
                engine_total_hour   = 1200.0,
                Total_Odometer      = 85000.0,
                avg_engine_load_pct = 42.0,
                avg_fuel_rate_Lhr   = 8.5,
                fuel_efficiency_kmpl= 5.2,
                P87_fuel_start_pct  = 80.0,
                P87_fuel_end_pct    = 65.0,
            )
            db.add(trip)
            db.flush()  # get trip_id committed before inserting FK

            # Insert into dbo.journey_scores
            score_row = JourneyScore(
                trip_id           = trip_id,
                vehicle_id        = VEHICLE_ID,
                driver_id         = DRIVER_ID,
                actual_fuel_used_L= round(td["distance_km"] / 5.2, 2),
                expected_fuel_L   = round(td["distance_km"] / 5.5, 2),
                theft_occurred    = "No",
                theft_type        = None,
                theft_amount_L    = 0.0,
                driver_score      = rule_score,
                created_at        = start_time,
            )
            db.add(score_row)

            print(f"  [OK] {trip_id}")
            print(f"       Route     : {td['route_type']}")
            print(f"       Note      : {td['note']}")
            print(f"       Rule-Based: {rule_score}")
            print()

        db.commit()
        print("=" * 60)
        print("All demo trips inserted successfully!")
        print("=" * 60)
        print()
        print("Now run the backend and check DR999 in the frontend.")
        print("Rule-Based vs ML difference will be clearly visible.")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    insert_demo_trips()
