import os
import sys
import uuid
from datetime import datetime, timedelta

# Ensure backend directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import SessionLocal
from maintenance_module.engines import process_vehicle_engine, run_alert_check
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

        # Create some fake live telemetry data (3 rows)
        now = datetime.utcnow()
        fake_data = [
            {"id": str(uuid.uuid4()), "vid": vid, "ts": now - timedelta(minutes=3),
             "rpm": 1500, "temp": 85.0, "load": 30.0, "fuel": 5.0, "idle": 0.0},
            {"id": str(uuid.uuid4()), "vid": vid, "ts": now - timedelta(minutes=2),
             "rpm": 2000, "temp": 95.0, "load": 95.0, "fuel": 30.0, "idle": 0.0},
            {"id": str(uuid.uuid4()), "vid": vid, "ts": now - timedelta(minutes=1),
             "rpm": 2500, "temp": 110.0, "load": 60.0, "fuel": 10.0, "idle": 0.0}
        ]

        print("\nInserting 3 new fake Telemetry rows into 'raw_telemetry'...")
        for row in fake_data:
            db.execute(
                text("""
                    INSERT INTO raw_telemetry (
                        vehicle_id, ts, rpm, coolant_temp, engine_load, fuel_rate, idle_time, 
                        speed, ignition, engine_torque, oil_pressure
                    ) VALUES (
                        :vid, :ts, :rpm, :temp, :load, :fuel, :idle, 
                        50.0, 1, 0.0, 350.0
                    )
                """),
                row
            )
        db.commit()
        print("Data inserted successfully!")

        print("\nNow running the AI Wear Engine (process_vehicle_engine) on this new data...")
        events_processed = process_vehicle_engine(db, vid, reg_no)
        print(f"AI Engine processed {events_processed} events!")

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
