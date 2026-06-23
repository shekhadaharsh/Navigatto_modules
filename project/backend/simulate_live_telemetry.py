import os
import sys
import uuid
from datetime import datetime, timedelta

# Ensure backend directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import driver_module.model  # Fix: Ensure Vehicle model is loaded for SQLAlchemy relationships
from database.db import SessionLocal
from maintenance_module.wear_engines import process_vehicle_engine, process_vehicle_brakes, process_vehicle_tires, run_alert_check
from sqlalchemy import text

def simulate_telemetry():
    db = SessionLocal()
    try:
        print("Fetching a test vehicle from the database...")
        vehicles = db.execute(text("SELECT id, reg_no FROM dbo.vehicles")).fetchall()
        if not vehicles:
            print("[ERROR] No vehicles found in DB!")
            return

        # Pick the first vehicle
        vid, reg_no = vehicles[0]
        print(f"Selected Vehicle: {reg_no} (ID: {vid})")

        # Create some fake live telemetry data (3 rows Engine + Brake + Tire)
        now = datetime.utcnow()
        fake_data = [
            # Normal Driving
            {"id": str(uuid.uuid4()), "vid": vid, "ts": now - timedelta(minutes=3),
             "rpm": 1500, "temp": 85.0, "load": 30.0, "fuel": 5.0, "idle": 0.0,
             "brake": 0, "speed": 40.0, "accel": 0.0, "gvw": 10000.0, "slope": 0.0,
             "lateral_g": 0.1, "accel_z": 0.05, "odometer": 10000.0},
            # Harsh Cornering on Rough Road
            {"id": str(uuid.uuid4()), "vid": vid, "ts": now - timedelta(minutes=2),
             "rpm": 2000, "temp": 95.0, "load": 95.0, "fuel": 30.0, "idle": 0.0,
             "brake": 0, "speed": 60.0, "accel": 0.0, "gvw": 15000.0, "slope": 0.0,
             "lateral_g": 0.6, "accel_z": 0.3, "odometer": 10000.5},
            # High Speed driving
            {"id": str(uuid.uuid4()), "vid": vid, "ts": now - timedelta(minutes=1),
             "rpm": 2500, "temp": 110.0, "load": 60.0, "fuel": 10.0, "idle": 0.0,
             "brake": 0, "speed": 110.0, "accel": 0.0, "gvw": 12000.0, "slope": 0.0,
             "lateral_g": 0.05, "accel_z": 0.02, "odometer": 10001.0}
        ]

        print("\nInserting 3 new fake Telemetry rows into 'raw_telemetry'...")
        for row in fake_data:
            db.execute(
                text("""
                    INSERT INTO raw_telemetry (
                        vehicle_id, ts, rpm, coolant_temp, engine_load, fuel_rate, idle_time, 
                        speed, ignition, engine_torque, oil_pressure,
                        brake_pedal, accel_x, gvw, gps_slope,
                        accel_y, accel_z, odometer
                    ) VALUES (
                        :vid, :ts, :rpm, :temp, :load, :fuel, :idle, 
                        :speed, 1, 0.0, 350.0,
                        :brake, :accel, :gvw, :slope,
                        :lateral_g, :accel_z, :odometer
                    )
                """),
                row
            )
        db.commit()
        print("Data inserted successfully!")

        print("\n[AI ENGINE] Processing Engine Wear...")
        engine_events = process_vehicle_engine(db, vid, reg_no)
        print(f"Engine AI processed {engine_events} events!")

        print("\n[AI BRAKES] Processing Brake Wear...")
        brake_events = process_vehicle_brakes(db, vid, reg_no)
        print(f"Brake AI processed {brake_events} events!")
        
        print("\n[AI TIRES] Processing Tire Wear...")
        tire_events = process_vehicle_tires(db, vid, reg_no)
        print(f"Tire AI processed {tire_events} events!")

        print("\nRunning Alert Check (run_alert_check)...")
        alerts = run_alert_check(db)
        print(f"Alert Generator complete. Created {alerts} alerts.")

        print("\n[OK] Simulation Complete! Check backend console or DB.")

    except Exception as e:
        db.rollback()
        print(f"[FAIL] Error during simulation: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    simulate_telemetry()
