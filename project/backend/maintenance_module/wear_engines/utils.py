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
    Optimized to fetch all components in a single query.
    """
    existing = db.query(ComponentWearState.component).filter(
        ComponentWearState.vehicle_id == vehicle_id
    ).all()
    existing_components = {c[0] for c in existing}
    
    needed = [comp for comp in DEFAULT_BASE_LIFE.keys() if comp not in existing_components]
    if not needed:
        return
        
    base_life_records = db.query(ComponentBaseLife).filter(
        ComponentBaseLife.vehicle_id == vehicle_id,
        ComponentBaseLife.component.in_(needed)
    ).all()
    base_life_map = {r.component: r.base_life for r in base_life_records}
    
    for component in needed:
        def_life = DEFAULT_BASE_LIFE[component]
        base_life = base_life_map.get(component, def_life)
            
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


def get_vehicle_g_thresholds(db: Session, vehicle_id: str):
    """
    Returns (harsh_brake_g, harsh_corner_g, harsh_accel_g) based on the vehicle type.
    """
    from driver_module.model import Vehicle
    try:
        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        v_type = vehicle.vehicle_type if vehicle else None
    except Exception:
        v_type = None

    # Custom thresholds by vehicle class matching Geotab Aggressive Driving Report standards
    if v_type == "Cargo Van":
        # Passenger Car (G)
        return -0.61, 0.47, 0.43
    elif v_type == "Medium Truck":
        # Truck/Cube Van (G)
        return -0.54, 0.40, 0.34
    elif v_type == "Heavy Truck" or v_type == "Heavy Duty Truck" or v_type == "Medium Duty Truck":
        # Heavy-Duty (G)
        return -0.47, 0.32, 0.29
    
    # Fallback to default constants
    return HARSH_BRAKE_G, HARSH_CORNER_G, 0.34


from maintenance_module.model import BrakeWearEvent, RawTelemetry
from sqlalchemy import func

# ── 1. Brake Wear Engine ──────────────────────────────────────
