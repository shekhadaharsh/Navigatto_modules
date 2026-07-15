import sys
import os
import uuid
import datetime

# Set Python path to backend directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db import SessionLocal, run_migrations
from maintenance_module.integration_service import VehicleIntegrationService
from driver_module.model import Vehicle
from maintenance_module.model import ComponentBaseLife, ComponentWearState
from sqlalchemy import text

def run_tests():
    print("Running database migrations first...")
    run_migrations()
    db = SessionLocal()
    print("Starting FleetIQ Integration Tests...")
    
    test_vin = "TEST-VIN-HONDA-123"
    test_vehicle_id = str(uuid.uuid4())

    try:
        # 1. Test VIN Decoding & Caching
        print("\n[Test 1] Testing VIN Decode...")
        decoded = VehicleIntegrationService.decode_vin(db, test_vin)
        assert decoded is not None, "Decoded output should not be None"
        assert decoded["make"] == "Honda", f"Expected make Honda, got {decoded.get('make')}"
        assert decoded["model"] == "Civic", f"Expected model Civic, got {decoded.get('model')}"
        print("[OK] VIN decoded successfully.")

        # Verify that it is written to db cache
        cache_row = db.execute(
            text("SELECT make, model FROM dbo.vehicle_api_cache WHERE vin = :vin"),
            {"vin": test_vin.upper()}
        ).fetchone()
        assert cache_row is not None, "Cache row should exist in database"
        assert cache_row[0] == "Honda"
        print("[OK] VIN response cached successfully in vehicle_api_cache table.")

        # Create a dummy vehicle first to satisfy foreign key constraints for the schedule cache
        db.execute(text("""
            INSERT INTO dbo.vehicles (id, reg_no, vehicle_name, vehicle_type, make, model, is_active)
            VALUES (:id, 'TEST-REG', 'Test Vehicle', 'Cargo Van', 'Honda', 'Civic', 1)
        """), {"id": test_vehicle_id})
        db.commit()

        # 2. Test OEM Maintenance Schedule Fetching & Caching
        print("\n[Test 2] Testing OEM Maintenance Schedule...")
        schedule = VehicleIntegrationService.fetch_maintenance_schedule(
            db=db,
            vehicle_id=test_vehicle_id,
            make=decoded["make"],
            model=decoded["model"],
            year=decoded["year"],
            vin=test_vin
        )
        assert len(schedule) > 0, "Schedule items should not be empty"
        print(f"[OK] Fetched {len(schedule)} maintenance schedule items.")

        # Verify cached entries in dbo.maintenance_schedule_cache
        sched_cache_rows = db.execute(
            text("SELECT service_item FROM dbo.maintenance_schedule_cache WHERE vehicle_id = :v_id"),
            {"v_id": test_vehicle_id}
        ).fetchall()
        assert len(sched_cache_rows) == len(schedule), "Cached rows mismatch"
        print("[OK] OEM maintenance schedule cached successfully in database.")

        # 3. Test Base Life Generation Engine
        print("\n[Test 3] Testing Knowledge Engine Base Life Generator...")
        base_life_dict = VehicleIntegrationService.generate_base_life(
            db=db,
            vehicle_id=test_vehicle_id,
            vehicle_type="Cargo Van",
            make=decoded["make"],
            model=decoded["model"],
            year=decoded["year"],
            vin=test_vin
        )
        print(f"Generated Base Lives: {base_life_dict}")
        assert "brake" in base_life_dict, "Missing brake baseline"
        assert "tire" in base_life_dict, "Missing tire baseline"
        assert "battery" in base_life_dict, "Missing battery baseline"
        assert "engine" in base_life_dict, "Missing engine baseline"
        
        # Check clamping constraints
        assert base_life_dict["brake"] >= 10000.0 and base_life_dict["brake"] <= 80000.0
        assert base_life_dict["tire"] >= 20000.0 and base_life_dict["tire"] <= 150000.0
        assert base_life_dict["battery"] >= 1000.0 and base_life_dict["battery"] <= 10000.0
        assert base_life_dict["engine"] >= 2000.0 and base_life_dict["engine"] <= 20000.0
        print("[OK] Component base lives generated and clamped successfully.")

        # 4. Clean up test data
        print("\nCleaning up test data...")
        db.execute(text("DELETE FROM dbo.maintenance_schedule_cache WHERE vehicle_id = :v_id"), {"v_id": test_vehicle_id})
        db.execute(text("DELETE FROM dbo.vehicles WHERE id = :v_id"), {"v_id": test_vehicle_id})
        db.execute(text("DELETE FROM dbo.vehicle_api_cache WHERE vin = :vin"), {"vin": test_vin.upper()})
        db.commit()
        print("[OK] Test data cleaned up successfully.")
        
        print("\nALL FLEETIQ INTEGRATION TESTS PASSED SUCCESSFULLY!")
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Test failed: {e}")
        # Clean up database on failure
        try:
            db.execute(text("DELETE FROM dbo.maintenance_schedule_cache WHERE vehicle_id = :v_id"), {"v_id": test_vehicle_id})
            db.execute(text("DELETE FROM dbo.vehicles WHERE id = :v_id"), {"v_id": test_vehicle_id})
            db.execute(text("DELETE FROM dbo.vehicle_api_cache WHERE vin = :vin"), {"vin": test_vin.upper()})
            db.commit()
        except:
            pass
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
