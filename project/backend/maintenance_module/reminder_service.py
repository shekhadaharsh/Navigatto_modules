import os
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from database.db import SessionLocal
from maintenance_module.model import MaintenanceAlert
from driver_module.model import Vehicle
from maintenance_module.tasks import send_alert_notification_task

# Logger setup
logger = logging.getLogger("maintenance_reminder")

# Settings: Default interval is 24 hours (1440 minutes)
REMINDER_INTERVAL_MINUTES = int(os.getenv("REMINDER_INTERVAL_MINUTES", "1440"))
LOOP_CHECK_INTERVAL_SEC = int(os.getenv("LOOP_CHECK_INTERVAL_SEC", "300")) # Check database every 5 minutes

def check_and_send_critical_reminders(db: Session):
    """
    Scans for active critical/urgent alerts and triggers email reminders
    if they haven't been notified in the configured reminder interval.
    """
    logger.info("Running critical maintenance alert reminder check...")
    try:
        # Fetch unacknowledged critical/urgent alerts
        active_alerts = db.query(MaintenanceAlert).filter(
            MaintenanceAlert.acknowledged == False,
            MaintenanceAlert.alert_level.in_(["critical", "urgent"])
        ).all()
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=REMINDER_INTERVAL_MINUTES)
        emails_sent = 0
        
        for alert in active_alerts:
            # Send if last_notified_at is None, or it was sent longer than REMINDER_INTERVAL_MINUTES ago
            if alert.last_notified_at is None or alert.last_notified_at <= cutoff_time:
                # Fetch vehicle registration number
                v = db.query(Vehicle).filter(Vehicle.id == alert.vehicle_id).first()
                reg_no = v.reg_no if v else alert.vehicle_id
                
                # Fetch decimal values as float
                rul_val = float(alert.rul_at_alert) if alert.rul_at_alert is not None else 0.0
                health_val = float(alert.health_at_alert) if alert.health_at_alert is not None else 0.0
                
                logger.info(f"Triggering email reminder for Vehicle: {reg_no}, Component: {alert.component}, Level: {alert.alert_level}")
                
                # Send email via background Celery task with reminder flag set to True
                send_alert_notification_task.delay(
                    vehicle_reg_no=reg_no,
                    component=alert.component,
                    level=alert.alert_level,
                    message=alert.message,
                    rul=rul_val,
                    health=health_val,
                    is_reminder=True
                )
                
                # Update last notified time
                alert.last_notified_at = datetime.utcnow()
                emails_sent += 1
                
        if emails_sent > 0:
            db.commit()
            logger.info(f"Triggered {emails_sent} reminder email(s).")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error checking and sending reminders: {e}")

async def start_reminder_scheduler():
    """
    Async background loop running in FastAPI main thread.
    """
    logger.info(f"Starting predictive maintenance reminder loop (Check interval: {LOOP_CHECK_INTERVAL_SEC}s, Reminder interval: {REMINDER_INTERVAL_MINUTES}m)")
    
    # Wait a few seconds for database startup and migrations to complete
    await asyncio.sleep(5)
    
    while True:
        try:
            db = SessionLocal()
            check_and_send_critical_reminders(db)
            db.close()
        except Exception as e:
            logger.error(f"Unhandled error in reminder scheduler tick: {e}")
            
        await asyncio.sleep(LOOP_CHECK_INTERVAL_SEC)
