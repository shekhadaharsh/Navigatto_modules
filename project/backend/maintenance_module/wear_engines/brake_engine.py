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
from typing import Optional

def process_vehicle_brakes(db: Session, vehicle_id: str, reg_no: str, max_telemetry_ts: Optional[datetime] = None):
    # Ensure wear state rows exist
    ensure_wear_state_initialized(db, vehicle_id)
    
    if max_telemetry_ts is None:
        max_telemetry_ts = db.query(func.max(RawTelemetry.ts)).filter(
            RawTelemetry.vehicle_id == vehicle_id
        ).scalar()
        
    if max_telemetry_ts is None:
        return 0
        
    # 1. Get latest processed timestamp to prevent double counting
    last_ts = db.query(func.max(BrakeWearEvent.ts)).filter(
        BrakeWearEvent.vehicle_id == vehicle_id
    ).scalar()
    
    if last_ts and max_telemetry_ts <= last_ts:
        return 0
        
    # 2. Fetch new telemetry rows
    telemetry_query = db.query(RawTelemetry).filter(RawTelemetry.vehicle_id == vehicle_id)
    if last_ts:
        telemetry_query = telemetry_query.filter(RawTelemetry.ts > last_ts)
        
    rows = telemetry_query.order_by(RawTelemetry.ts.asc()).all()
    if not rows:
        return 0

    # 3. Determine max weight
    gvw_max = float(db.query(func.max(RawTelemetry.gvw)).filter(
        RawTelemetry.vehicle_id == vehicle_id
    ).scalar() or 20000.0)

    prev_brake = 0
    brake_count = db.query(BrakeWearEvent).filter(
        BrakeWearEvent.vehicle_id == vehicle_id
    ).count()
    
    events = []
    total_wear = 0.0

    for row in rows:
        ts, brake_pedal, speed, accel_x, gvw, gps_slope, trip_id = (
            row.ts, row.brake_pedal, row.speed, row.accel_x, row.gvw, row.gps_slope, row.trip_id
        )
        
        brake_pedal = int(brake_pedal) if brake_pedal is not None else 0
        speed       = float(speed)     if speed       is not None else 0.0
        accel_x     = float(accel_x)   if accel_x     is not None else 0.0
        gvw         = float(gvw)       if gvw         is not None else gvw_max * 0.7
        gps_slope   = float(gps_slope) if gps_slope   is not None else 0.0

        # Detect OFF -> ON brake pedal press
        if prev_brake == 0 and brake_pedal == 1:
            brake_count += 1
            
            # Kinetic Energy: E = 0.5 * m * v^2
            v_ms = speed * (1000.0 / 3600.0)
            energy = round(0.5 * gvw * (v_ms ** 2), 2)
            
            # Classify
            model = get_brake_model()
            if model:
                input_df = pd.DataFrame([{
                    'speed': speed,
                    'accel_x': accel_x,
                    'gvw': gvw,
                    'gps_slope': gps_slope
                }])
                event_type = model['event_classifier'].predict(input_df)[0]
                severity_multi = float(model['multi_regressor'].predict(input_df)[0])
                wear_units = float(model['wear_regressor'].predict(input_df)[0])
            else:
                is_harsh    = accel_x < HARSH_BRAKE_G
                is_heavy    = gvw > (gvw_max * HEAVY_LOAD_RATIO)
                is_downhill = gps_slope < DOWNHILL_SLOPE

                if is_harsh and is_downhill:
                    event_type, base_wear = "downhill_harsh", 10.0
                elif is_harsh and is_heavy:
                    event_type, base_wear = "heavy_harsh", 8.0
                elif is_harsh:
                    event_type, base_wear = "harsh", 5.0
                elif speed > 40:
                    event_type, base_wear = "medium", 2.0
                else:
                    event_type, base_wear = "light", 1.0

                raw_multiplier = 1.0 + (abs(accel_x) * 2.0) + (speed / 100.0)
                severity_multi = min(round(raw_multiplier, 2), MAX_MULTIPLIER)
                wear_units     = round(base_wear * severity_multi, 4)
                
            total_wear    += wear_units

            events.append({
                "vehicle_id": vehicle_id, "trip_id": trip_id, "ts": ts,
                "brake_count": brake_count, "event_type": event_type, "speed_kmh": speed,
                "gvw_kg": gvw, "gps_slope": gps_slope, "accel_x": accel_x,
                "energy_joules": energy, "severity_multi": severity_multi, "wear_units": wear_units
            })
            
        prev_brake = brake_pedal

    if events:
        # Bulk Insert Events
        db.bulk_insert_mappings(BrakeWearEvent, events)
        
        # Update Wear State
        state = db.query(ComponentWearState).filter(
            ComponentWearState.vehicle_id == vehicle_id,
            ComponentWearState.component == 'brake'
        ).first()
        if state:
            state.accumulated_wear = float(state.accumulated_wear) + total_wear
            state.last_updated = datetime.utcnow()
            
        db.commit()

    return len(events)


