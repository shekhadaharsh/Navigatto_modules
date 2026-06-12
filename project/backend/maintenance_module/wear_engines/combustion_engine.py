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
def process_vehicle_engine(db: Session, vehicle_id: str, reg_no: str):
    ensure_wear_state_initialized(db, vehicle_id)
    
    last_ts = db.query(func.max(EngineWearEvent.ts)).filter(
        EngineWearEvent.vehicle_id == vehicle_id
    ).scalar()
    
    telemetry_query = db.query(RawTelemetry).filter(RawTelemetry.vehicle_id == vehicle_id)
    if last_ts:
        telemetry_query = telemetry_query.filter(RawTelemetry.ts > last_ts)
        
    rows = telemetry_query.order_by(RawTelemetry.ts.asc()).all()
    if not rows:
        return 0

    events = []
    total_wear = 0.0

    for row in rows:
        ts, rpm, temp, torque, load, fuel_rate, idle_min, oil_press, dtc_codes, trip_id = (
            row.ts, row.rpm, row.coolant_temp, row.engine_torque, row.engine_load, 
            row.fuel_rate, row.idle_time, row.oil_pressure, row.dtc_codes, row.trip_id
        )
        
        rpm       = int(rpm)         if rpm       is not None else 0
        temp      = float(temp)      if temp      is not None else 85.0
        torque    = float(torque)    if torque    is not None else 0.0
        load      = float(load)      if load      is not None else 0.0
        fuel_rate = float(fuel_rate) if fuel_rate is not None else 0.0
        idle_min  = float(idle_min)  if idle_min  is not None else 0.0
        oil_press = float(oil_press) if oil_press is not None else 350.0

        if rpm < 500:
            continue

        is_overheat = temp > 105.0
        
        model = get_engine_model()
        if model:
            # Use AI Model for inference
            # features: 'rpm', 'coolant_temp', 'engine_load', 'fuel_rate', 'idle_time'
            input_df = pd.DataFrame([{
                'rpm': rpm, 
                'coolant_temp': temp, 
                'engine_load': load, 
                'fuel_rate': fuel_rate, 
                'idle_time': idle_min
            }])
            
            event_type = model['event_classifier'].predict(input_df)[0]
            multi = float(model['multi_regressor'].predict(input_df)[0])
            wear_units = float(model['wear_regressor'].predict(input_df)[0])
            multi = round(multi, 2)
            wear_units = round(wear_units, 6)
        else:
            # Fallback to rules if AI not loaded
            is_high_rpm = rpm > 3200
            is_high_trq = torque > 450.0
            is_long_idl = idle_min > 20.0

            if is_overheat:
                event_type, base_wear, multi = "overheat", 20.0, 10.0
            elif is_high_rpm:
                event_type, base_wear, multi = "high_rpm", 5.0, 4.0
            elif is_high_trq:
                event_type, base_wear, multi = "high_torque", 3.0, 3.0
            elif is_long_idl:
                event_type, base_wear, multi = "long_idle", 2.0, 2.0
            else:
                event_type, base_wear, multi = "normal", 1.0, 1.0

            wear_units = round(base_wear * multi, 6)

        if event_type != "normal" or len(events) % 20 == 0:
            total_wear += wear_units
            events.append({
                "vehicle_id": vehicle_id, "trip_id": trip_id, "ts": ts,
                "rpm": rpm, "coolant_temp": temp, "torque_nm": torque, "engine_load": load,
                "fuel_rate": fuel_rate, "idle_minutes": idle_min, "oil_pressure": oil_press,
                "overheat": True if is_overheat else False, "event_type": event_type,
                "severity_multi": multi, "wear_units": wear_units, "dtc_codes": dtc_codes or ""
            })

    if events:
        db.bulk_insert_mappings(EngineWearEvent, events)
        
        state = db.query(ComponentWearState).filter(
            ComponentWearState.vehicle_id == vehicle_id,
            ComponentWearState.component == 'engine'
        ).first()
        if state:
            state.accumulated_wear = float(state.accumulated_wear) + total_wear
            state.last_updated = datetime.utcnow()
            
        db.commit()

    return len(events)


from maintenance_module.model import MaintenanceAlert

# ── 6. Alert Check Engine ─────────────────────────────────────
