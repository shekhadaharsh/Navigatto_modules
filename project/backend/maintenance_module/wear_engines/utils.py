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

from .constants import *
from .ml_loader import get_brake_model, get_engine_model, get_tire_model
def ensure_wear_state_initialized(db: Session, vehicle_id: str):
    """
    Checks if component_wear_state is populated for all components.
    If not, reads from component_base_life or inserts defaults.
    """
    for component, def_life in DEFAULT_BASE_LIFE.items():
        count = db.query(ComponentWearState).filter(
            ComponentWearState.vehicle_id == vehicle_id,
            ComponentWearState.component == component
        ).count()
        
        if count == 0:
            # Check base life config
            base_life_record = db.query(ComponentBaseLife).filter(
                ComponentBaseLife.vehicle_id == vehicle_id,
                ComponentBaseLife.component == component
            ).first()
            
            base_life = base_life_record.base_life if base_life_record else def_life
                
            new_state = ComponentWearState(
                id=str(uuid.uuid4()),
                vehicle_id=vehicle_id,
                component=component,
                accumulated_wear=0.0,
                base_life=base_life,
                last_updated=datetime.utcnow()
            )
            db.add(new_state)
    db.commit()


from maintenance_module.model import BrakeWearEvent, RawTelemetry
from sqlalchemy import func

# ── 1. Brake Wear Engine ──────────────────────────────────────
