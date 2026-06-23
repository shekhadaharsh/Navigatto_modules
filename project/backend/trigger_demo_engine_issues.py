"""
Script to trigger Engine Health issues for two vehicles in the database.
This updates their engine health to ~26% (by setting accumulated_wear to 37000 out of 50000 base life)
and generates the corresponding unacknowledged alerts in maintenance_alerts table.
"""
import os
import sys

# Ensure backend directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import driver_module.model  # Fix: Ensure Vehicle model is loaded for SQLAlchemy relationships
from database.db import SessionLocal
from maintenance_module.wear_engines import ensure_wear_state_initialized, run_alert_check
from sqlalchemy import text

def trigger_engine_issues():
    db = SessionLocal()
    try:
        print("Fetching vehicles from the database...")
        # Get vehicles
        vehicles = db.execute(text("SELECT id, reg_no, make, model FROM dbo.vehicles")).fetchall()
        if not vehicles:
            print("[ERROR] No vehicles found in the database. Please make sure demo data is loaded first.")
            return

        print(f"Found {len(vehicles)} vehicles.")
        target_vehicles = vehicles[2:4] # Target the 3rd and 4th vehicles

        for v in target_vehicles:
            vid, reg_no, make, model = v
            print(f"\nSetting Engine Wear for Vehicle: {reg_no} ({make} {model}) - ID: {vid}")
            
            # Ensure wear state rows are initialized first
            ensure_wear_state_initialized(db, vid)

            # Clear any existing alert for engine for this vehicle to prevent conflicts
            db.execute(
                text("DELETE FROM dbo.maintenance_alerts WHERE vehicle_id = :vid AND component = 'engine'"),
                {"vid": vid}
            )

            # Set engine wear to 46000.0 (health = 8%)
            db.execute(
                text("""
                    UPDATE dbo.component_wear_state
                    SET accumulated_wear = 46000.0,
                        last_updated = SYSUTCDATETIME()
                    WHERE vehicle_id = :vid AND component = 'engine'
                """),
                {"vid": vid}
            )
            print(f"  -> Reset accumulated_wear to 46000.0 (Health Score will be 8.0%)")

        db.commit()

        # Run backend alert generator to automatically create the alert entries
        print("\nRunning backend Alert Generator...")
        alerts_created = run_alert_check(db)
        print(f"Alert Generator complete. Created {alerts_created} new maintenance alerts.")
        print("\nSuccessfully updated 2 vehicles to show Engine Issues!")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to set engine issues: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    trigger_engine_issues()
