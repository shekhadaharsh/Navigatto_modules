from maintenance_module.celery_app import celery_app
import logging

@celery_app.task(name="process_vehicle_wear_task")
def process_vehicle_wear_task(vehicle_id: str, reg_no: str):
    """
    Background worker that runs all wear modules and checks for alerts asynchronously.
    """
    from database.db import SessionLocal
    import driver_module.model  # Fix: Ensure Vehicle model is loaded for SQLAlchemy relationships
    from maintenance_module.wear_engines import (
        process_vehicle_brakes,
        process_vehicle_clutch,
        process_vehicle_tires,
        process_vehicle_battery,
        process_vehicle_engine,
        run_alert_check
    )
    
    db_session = SessionLocal()
    try:
        process_vehicle_brakes(db_session, vehicle_id, reg_no)
        process_vehicle_clutch(db_session, vehicle_id, reg_no)
        process_vehicle_tires(db_session, vehicle_id, reg_no)
        process_vehicle_battery(db_session, vehicle_id, reg_no)
        process_vehicle_engine(db_session, vehicle_id, reg_no)
        run_alert_check(db_session)
    except Exception as e:
        logging.error(f"Error executing Celery wear engines for vehicle {reg_no}: {e}")
    finally:
        db_session.close()
