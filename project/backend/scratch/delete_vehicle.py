import sys
import os

# Add parent path to import database config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db import SessionLocal
from sqlalchemy import text

def delete_vehicle():
    db = SessionLocal()
    vehicle_id = "433f3c2d-eb76-4514-9498-248874c7bc99"
    try:
        print(f"Deleting vehicle {vehicle_id} and its associated baseline/wear records...")
        
        # Delete related tables first due to foreign keys
        db.execute(text("DELETE FROM dbo.component_wear_state WHERE vehicle_id = :v_id"), {"v_id": vehicle_id})
        db.execute(text("DELETE FROM dbo.component_base_life WHERE vehicle_id = :v_id"), {"v_id": vehicle_id})
        db.execute(text("DELETE FROM dbo.maintenance_schedule_cache WHERE vehicle_id = :v_id"), {"v_id": vehicle_id})
        
        # Delete the main vehicle record
        db.execute(text("DELETE FROM dbo.vehicles WHERE id = :v_id"), {"v_id": vehicle_id})
        
        db.commit()
        print("Successfully deleted vehicle and related records!")
    except Exception as e:
        db.rollback()
        print(f"Failed to delete vehicle: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    delete_vehicle()
