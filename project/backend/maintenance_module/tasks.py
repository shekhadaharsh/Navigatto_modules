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
        from sqlalchemy import func
        from maintenance_module.model import RawTelemetry
        
        max_telemetry_ts = db_session.query(func.max(RawTelemetry.ts)).filter(
            RawTelemetry.vehicle_id == vehicle_id
        ).scalar()
        
        process_vehicle_brakes(db_session, vehicle_id, reg_no, max_telemetry_ts)
        process_vehicle_clutch(db_session, vehicle_id, reg_no, max_telemetry_ts)
        process_vehicle_tires(db_session, vehicle_id, reg_no, max_telemetry_ts)
        process_vehicle_battery(db_session, vehicle_id, reg_no, max_telemetry_ts)
        process_vehicle_engine(db_session, vehicle_id, reg_no, max_telemetry_ts)
        run_alert_check(db_session)
    except Exception as e:
        logging.error(f"Error executing Celery wear engines for vehicle {reg_no}: {e}")
    finally:
        db_session.close()


@celery_app.task(name="send_alert_notification_task")
def send_alert_notification_task(vehicle_reg_no: str, component: str, level: str, message: str, rul: float, health: float, is_reminder: bool = False):
    """
    Background worker to send email notifications for critical alerts. Supports reminder flag.
    """
    from maintenance_module.notification_service import send_email_alert
    
    try:
        send_email_alert(
            vehicle_reg_no=vehicle_reg_no,
            component=component,
            level=level,
            message=message,
            rul=rul,
            health=health,
            is_reminder=is_reminder
        )
    except Exception as e:
        logging.error(f"Failed to execute send_alert_notification_task: {e}")
