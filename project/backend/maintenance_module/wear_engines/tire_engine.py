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

def process_vehicle_tires(db: Session, vehicle_id: str, reg_no: str, max_telemetry_ts: Optional[datetime] = None):
    ensure_wear_state_initialized(db, vehicle_id)
    
    if max_telemetry_ts is None:
        max_telemetry_ts = db.query(func.max(RawTelemetry.ts)).filter(
            RawTelemetry.vehicle_id == vehicle_id
        ).scalar()
        
    if max_telemetry_ts is None:
        return 0
        
    last_ts = db.query(func.max(TireWearEvent.ts)).filter(
        TireWearEvent.vehicle_id == vehicle_id
    ).scalar()
    
    if last_ts and max_telemetry_ts <= last_ts:
        return 0
        
    telemetry_query = db.query(RawTelemetry).filter(RawTelemetry.vehicle_id == vehicle_id)
    if last_ts:
        telemetry_query = telemetry_query.filter(RawTelemetry.ts > last_ts)
        
    rows = telemetry_query.order_by(RawTelemetry.ts.asc()).all()
    if not rows:
        return 0

    # Fetch tire coefficients - using raw SQL here since tire_profiles isn't an ORM model yet
    coeffs = db.execute(
        text("SELECT coeff_a, coeff_b, coeff_c, coeff_d FROM tire_profiles WHERE tire_type = 'michelin_x'")
    ).fetchone()
    a, b, c, d = (float(coeffs[0]), float(coeffs[1]), float(coeffs[2]), float(coeffs[3])) if coeffs else (1.0, 1.2, 1.1, 0.8)

    gvw_max = float(db.query(func.max(RawTelemetry.gvw)).filter(
        RawTelemetry.vehicle_id == vehicle_id
    ).scalar() or 20000.0)

    events = []
    total_wear = 0.0

    for row in rows:
        ts, speed, lateral_g, accel_z, gvw, odometer, trip_id = (
            row.ts, row.speed, row.accel_y, row.accel_z, row.gvw, row.odometer, row.trip_id
        )
        
        speed     = float(speed)     if speed     is not None else 0.0
        lateral_g = float(lateral_g) if lateral_g is not None else 0.0
        accel_z   = float(accel_z)   if accel_z   is not None else 0.0
        gvw       = float(gvw)       if gvw       is not None else gvw_max * 0.7

        if speed < 1.0:
            continue

        # Segment distance (approx 1 second interval representation)
        dist_km = speed * (1.0 / 3600.0)
        vibration_rms = abs(accel_z)

        model = get_tire_model()
        if model:
            input_df = pd.DataFrame([{
                'speed': speed,
                'lateral_g': lateral_g,
                'accel_z': accel_z,
                'gvw': gvw
            }])
            event_type = model['event_classifier'].predict(input_df)[0]
            multiplier = float(model['multi_regressor'].predict(input_df)[0])
            wear_units = float(model['wear_regressor'].predict(input_df)[0])
        else:
            is_high_speed   = speed > HIGH_SPEED_KMH
            is_harsh_corner = abs(lateral_g) > HARSH_CORNER_G
            is_overload     = gvw > (gvw_max * OVERLOAD_RATIO)
            is_rough        = vibration_rms > ROUGH_ROAD_RMS

            if is_rough:
                event_type, multiplier = "rough_road", 3.0
            elif is_overload:
                event_type, multiplier = "overload", 2.5
            elif is_harsh_corner:
                event_type, multiplier = "harsh_corner", 2.0
            elif is_high_speed:
                event_type, multiplier = "high_speed", 1.5
            else:
                event_type, multiplier = "normal", 1.0

            load_factor = gvw / gvw_max
            raw_wear = (
                a * dist_km +
                b * abs(lateral_g) +
                c * load_factor +
                d * vibration_rms
            )
            wear_units = round(raw_wear * multiplier, 6)

        if event_type != "normal" or len(events) % 15 == 0:
            total_wear += wear_units
            events.append({
                "vehicle_id": vehicle_id, "trip_id": trip_id, "ts": ts,
                "distance_km": dist_km, "speed_kmh": speed, "lateral_g": lateral_g,
                "gvw_kg": gvw, "vibration_rms": vibration_rms, "event_type": event_type,
                "severity_multi": multiplier, "wear_units": wear_units
            })

    if events:
        db.bulk_insert_mappings(TireWearEvent, events)
        
        state = db.query(ComponentWearState).filter(
            ComponentWearState.vehicle_id == vehicle_id,
            ComponentWearState.component == 'tire'
        ).first()
        if state:
            state.accumulated_wear = float(state.accumulated_wear) + total_wear
            state.last_updated = datetime.utcnow()
            
        db.commit()

    return len(events)


