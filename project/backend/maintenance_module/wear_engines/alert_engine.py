"""
Vehicle Maintenance Wear and Alert Engines
--------------------------------------------
Calculates wear increments and alerts based on FMC650 sensor data.
Supports incremental processing to prevent double-counting.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime
import math
import joblib
import os
import pandas as pd
import logging

from maintenance_module.model import *
from .constants import *
from .ml_loader import get_brake_model, get_engine_model, get_tire_model
def run_alert_check(db: Session):
    """
    Scans component_wear_state and checks health thresholds:
    health < 30% -> WARNING alert
    health < 10% or RUL=0 -> CRITICAL/URGENT alert
    """
    rows = db.query(ComponentWearState).all()
    alerts_created = 0

    for row in rows:
        vid, component, rul, health = (row.vehicle_id, row.component, row.rul, row.health_score)
        rul    = float(rul)    if rul    is not None else 0.0
        health = float(health) if health is not None else 0.0

        if rul <= 0:
            level = "urgent"
            message = f"{component.upper()} completely worn out! Immediate replacement needed."
        elif health < 10.0:
            level = "critical"
            message = f"{component.upper()} critically low — schedule replacement within days."
        elif health < 30.0:
            level = "warning"
            message = f"{component.upper()} wear warning — plan maintenance soon."
        else:
            continue

        # Check if same level alert is already open (unacknowledged)
        already_open = db.query(MaintenanceAlert).filter(
            MaintenanceAlert.vehicle_id == vid,
            MaintenanceAlert.component == component,
            MaintenanceAlert.alert_level == level,
            MaintenanceAlert.acknowledged == False
        ).count()

        if already_open == 0:
            last_not_val = datetime.utcnow() if level in ['urgent', 'critical'] else None
            new_alert = MaintenanceAlert(
                id=str(uuid.uuid4()),
                vehicle_id=vid,
                component=component,
                ts=datetime.utcnow(),
                rul_at_alert=rul,
                health_at_alert=health,
                alert_level=level,
                message=message,
                acknowledged=False,
                last_notified_at=last_not_val
            )
            db.add(new_alert)
            alerts_created += 1

            # Trigger background notification task for critical/urgent alerts
            if level in ['urgent', 'critical']:
                from driver_module.model import Vehicle
                from maintenance_module.tasks import send_alert_notification_task
                
                v = db.query(Vehicle).filter(Vehicle.id == vid).first()
                reg_no = v.reg_no if v else vid
                
                send_alert_notification_task.delay(
                    vehicle_reg_no=reg_no,
                    component=component,
                    level=level,
                    message=message,
                    rul=rul,
                    health=health
                )


    if alerts_created > 0:
        db.commit()

    return alerts_created
