from sqlalchemy import func
from .utils import ensure_wear_state_initialized
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
def process_vehicle_battery(db: Session, vehicle_id: str, reg_no: str):
    ensure_wear_state_initialized(db, vehicle_id)
    
    last_ts = db.query(func.max(BatteryWearEvent.ts)).filter(
        BatteryWearEvent.vehicle_id == vehicle_id
    ).scalar()
    
    telemetry_query = db.query(RawTelemetry).filter(RawTelemetry.vehicle_id == vehicle_id)
    if last_ts:
        telemetry_query = telemetry_query.filter(RawTelemetry.ts > last_ts)
        
    rows = telemetry_query.order_by(RawTelemetry.ts.asc()).all()
    if not rows:
        return 0

    prev_ignition = 1
    startup_cycle = db.query(BatteryWearEvent).filter(
        BatteryWearEvent.vehicle_id == vehicle_id
    ).count()
    
    events = []
    total_wear = 0.0

    for row in rows:
        ts, ignition, batt_v, idle_time, trip_id = (
            row.ts, row.ignition, row.battery_voltage, row.idle_time, row.trip_id
        )
        
        ignition  = int(ignition)      if ignition  is not None else 0
        batt_v    = float(batt_v)      if batt_v    is not None else V_NOMINAL
        idle_time = float(idle_time)   if idle_time is not None else 0.0

        # Ignition OFF -> ON (Startup trigger)
        if prev_ignition == 0 and ignition == 1:
            startup_cycle += 1
            v_under_load = batt_v
            
            soh = round((v_under_load / V_NOMINAL) * 100.0, 2)

            if v_under_load < DEEP_DISCHARGE_V:
                event_type, base_wear = "deep_discharge", 8.0
            elif v_under_load < COLD_CRANK_V:
                event_type, base_wear = "cold_crank", 5.0
            elif idle_time > LONG_IDLE_MIN:
                event_type, base_wear = "long_idle", 3.0
            else:
                event_type, base_wear = "normal_start", 1.0

            voltage_drop = V_NOMINAL - v_under_load
            raw_multi    = 1.0 + (voltage_drop / V_NOMINAL) * 3.0
            severity_multi = min(round(raw_multi, 2), MAX_MULTIPLIER)
            wear_units     = round(base_wear * severity_multi, 4)
            total_wear    += wear_units

            events.append({
                "vehicle_id": vehicle_id, "trip_id": trip_id, "ts": ts,
                "startup_cycle": startup_cycle, "event_type": event_type,
                "v_nominal": V_NOMINAL, "v_under_load": v_under_load, "soh_percent": soh,
                "idle_minutes": idle_time, "severity_multi": severity_multi, "wear_units": wear_units
            })

        prev_ignition = ignition

    if events:
        db.bulk_insert_mappings(BatteryWearEvent, events)
        
        state = db.query(ComponentWearState).filter(
            ComponentWearState.vehicle_id == vehicle_id,
            ComponentWearState.component == 'battery'
        ).first()
        if state:
            state.accumulated_wear = float(state.accumulated_wear) + total_wear
            state.last_updated = datetime.utcnow()
            
        db.commit()

    return len(events)


