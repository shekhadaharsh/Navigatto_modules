import sys
import os
from datetime import datetime, timedelta
import random

# Add project path to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import SessionLocal, Base, engine
from driver_module.model import Trip

def seed_data():
    db = SessionLocal()
    # Check if table has data already
    try:
        count = db.query(Trip).count()
        if count > 0:
            print(f"Database already has {count} records. Skipping seeding.")
            return
    except Exception as e:
        print("Error checking table, creating tables first:", e)
        Base.metadata.create_all(bind=engine)

    print("Seeding database with realistic telemetry data...")

    # Mock drivers and vehicles
    drivers = ["DR001", "DR002", "DR003", "DR004", "DR005"]
    vehicles = ["VH001", "VH002", "VH003", "VH004", "VH005"]
    vehicle_types = ["Mini Truck", "Medium Cargo", "Heavy Cargo Truck", "Pickup Truck", "Heavy Cargo Truck"]
    route_types = ["Highway", "City", "Mountain", "Rural", "Mixed"]

    trip_count = 0
    now = datetime.now()

    for idx, driver_id in enumerate(drivers):
        vehicle_id = vehicles[idx]
        v_type = vehicle_types[idx]
        
        # Create 12 journeys per driver
        for i in range(12):
            trip_id = f"TR00{9131 + trip_count}"
            route = route_types[i % 5]
            
            # Distance, duration, speed depending on route type
            if route == "Highway":
                dist = 320.5
                dur = 240.0
                avg_speed = 80.1
                max_speed = 112.0
                accel = random.choice([0, 1, 2])
                brake = random.choice([0, 1, 2])
                overspeed = random.choice([0, 1])
                corner = random.choice([0, 1])
                idle = 12.8
            elif route == "City":
                dist = 42.1
                dur = 95.0
                avg_speed = 26.6
                max_speed = 55.0
                accel = random.choice([8, 12, 15])
                brake = random.choice([10, 15, 18])
                overspeed = random.choice([1, 2])
                corner = random.choice([5, 8])
                idle = 42.5
            else:
                dist = 145.2
                dur = 135.0
                avg_speed = 64.5
                max_speed = 85.0
                accel = random.choice([3, 5, 7])
                brake = random.choice([4, 6, 8])
                overspeed = random.choice([0, 1])
                corner = random.choice([2, 4])
                idle = 20.0

            # Custom behavior for specific driver to match frontend expectations
            is_theft = (i == 4 and driver_id == "DR001")
            is_maint_crit = (i == 2 and driver_id == "DR001")
            
            # Fuel calculations
            expected_fuel = dist * 0.15 # 15L per 100km average
            if is_theft:
                actual_fuel = expected_fuel + 14.2
                theft_occurred = True
                theft_type = "Siphon"
                theft_amount = 14.2
            else:
                actual_fuel = expected_fuel * random.uniform(0.98, 1.05)
                theft_occurred = False
                theft_type = None
                theft_amount = 0.0

            trip_start = now - timedelta(days=i, hours=3)
            trip_end = trip_start + timedelta(minutes=dur)

            # Create trip record
            trip = Trip(
                trip_id=trip_id,
                vehicle_id=vehicle_id,
                vehicle_type=v_type,
                driver_id=driver_id,
                route_type=route,
                trip_start=trip_start,
                trip_end=trip_end,
                trip_duration_min=dur,
                engine_total_hour=1000.0 + (trip_count * 4.5),
                Total_Odometer=50000.0 + (trip_count * 150),
                distance_km=dist,
                load_pct=68.4,
                temp_celsius=104.5 if is_maint_crit else 82.5,
                hour_of_day=trip_start.hour,
                day_of_week=trip_start.weekday(),
                avg_speed_kmh=avg_speed,
                max_speed_kmh=max_speed,
                idle_time_min=idle,
                num_stops=18 if route == "City" else 2,
                accel_events=accel,
                brake_events=brake,
                over_speed_count=overspeed,
                cornering_events=corner,
                avg_engine_rpm=1680.0,
                avg_engine_load_pct=58.2,
                avg_fuel_rate_Lhr=8.4,
                P86_fuel_start_L=100.0,
                P86_fuel_end_L=100.0 - actual_fuel,
                P86_trip_diff_L=actual_fuel,
                P87_fuel_start_pct=94.5,
                P87_fuel_end_pct=94.5 - (actual_fuel / 2.0),
                P87_fuel_start_L=100.0,
                P87_fuel_end_L=100.0 - actual_fuel,
                actual_fuel_used_L=actual_fuel,
                expected_fuel_L=expected_fuel,
                fuel_efficiency_kmpl=dist / (actual_fuel if actual_fuel > 0 else 1.0),
                refuel_L=0.0,
                theft_occurred=theft_occurred,
                theft_type=theft_type,
                theft_amount_L=theft_amount,
                Driver_score=85.0
            )

            # Custom attribute for external_voltage (simulated via db model mapping if dynamic)
            # Trip model uses Base which maps columns. If we look at route code:
            # ext_voltage = getattr(trip, "external_voltage", None)
            # Since external_voltage is not a Column in the Trip model, we can dynamically add it,
            # or since SQL server allows adding columns, wait, does Trip have external_voltage column?
            # No, looking at model.py, Trip does not define external_voltage.
            # But routes.py does: `ext_voltage = getattr(trip, "external_voltage", None)`
            # And: `if ext_voltage is not None and ext_voltage < 11.5:`
            # This is dynamic. To avoid errors, we'll let it be. But wait! Let's check if we can add
            # an external_voltage column to Trip, or if we can define it. Since the route expects it
            # from database rows, let's look if there is any other column.
            # Oh, wait! In database/db.py or model.py, is there external_voltage?
            # Let's double check model.py. No, there isn't. So it will return None, which is perfectly safe.

            db.add(trip)
            trip_count += 1

    db.commit()
    db.close()
    print(f"Successfully seeded {trip_count} records into the database.")

if __name__ == "__main__":
    seed_data()
