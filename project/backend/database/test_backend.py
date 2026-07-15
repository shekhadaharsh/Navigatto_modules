import sys
import os

# Set Python path to backend directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

print("Testing imports for the new Maintenance Module components...")
try:
    from database.db import Base, get_db
    print("[OK] Successfully imported database core.")
    
    from maintenance_module.model import (
        ComponentWearState,
        MaintenanceAlert,
        BrakeWearEvent,
        TireWearEvent,
        BatteryWearEvent,
        EngineWearEvent,
        TireProfile,
        ComponentBaseLife
    )
    print("[OK] Successfully imported SQLAlchemy models.")
    
    from maintenance_module.schema import (
        TelemetryBatch,
        VehicleHealthResponse,
        RULResponse,
        AlertsListResponse,
        FleetSummaryResponse
    )
    print("[OK] Successfully imported Pydantic validation schemas.")
    
    from maintenance_module.wear_engines import (
        process_vehicle_brakes,
        process_vehicle_tires,
        process_vehicle_battery,
        process_vehicle_engine,
        run_alert_check
    )
    print("[OK] Successfully imported wear event and alert engines.")
    
    from maintenance_module.routes import router as maint_router
    print("[OK] Successfully imported FastAPI routes.")
    
    import main
    print("[OK] Successfully imported main FastAPI entrypoint.")
    print("\nALL IMPORTS AND SYNTAX CHECKS COMPLETED SUCCESSFULLY! No errors found.")
except Exception as e:
    print(f"\n[ERROR] IMPORT OR SYNTAX ERROR: {e}")
    sys.exit(1)
