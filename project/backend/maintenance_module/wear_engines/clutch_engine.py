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

def process_vehicle_clutch(db: Session, vehicle_id: str, reg_no: str, max_telemetry_ts: Optional[datetime] = None):
    ensure_wear_state_initialized(db, vehicle_id)
    
    if max_telemetry_ts is None:
        max_telemetry_ts = db.query(func.max(RawTelemetry.ts)).filter(
            RawTelemetry.vehicle_id == vehicle_id
        ).scalar()
        
    if max_telemetry_ts is None:
        return 0
        
    last_ts = db.query(func.max(ClutchWearEvent.ts)).filter(
        ClutchWearEvent.vehicle_id == vehicle_id
    ).scalar()
    
    if last_ts and max_telemetry_ts <= last_ts:
        return 0
        
    telemetry_query = db.query(RawTelemetry).filter(RawTelemetry.vehicle_id == vehicle_id)
    if last_ts:
        telemetry_query = telemetry_query.filter(RawTelemetry.ts > last_ts)
        
    rows = telemetry_query.order_by(RawTelemetry.ts.asc()).all()
    if not rows:
        return 0

    gvw_max = float(db.query(func.max(RawTelemetry.gvw)).filter(
        RawTelemetry.vehicle_id == vehicle_id
    ).scalar() or 20000.0)

    prev_rpm = 0
    prev_speed = 0.0
    events = []
    total_wear = 0.0

    for row in rows:
        ts, rpm, speed, torque, gvw, gps_slope, trip_id = (
            row.ts, row.rpm, row.speed, row.engine_torque, row.gvw, row.gps_slope, row.trip_id
        )
        
        rpm       = int(rpm)         if rpm       is not None else 0
        speed     = float(speed)     if speed     is not None else 0.0
        torque    = float(torque)    if torque    is not None else 0.0
        gvw       = float(gvw)       if gvw       is not None else gvw_max * 0.7
        gps_slope = float(gps_slope) if gps_slope is not None else 0.0

        # Slip condition: RPM rise, but speed remains stable
        rpm_rose      = (rpm - prev_rpm) > SLIP_RPM_RISE
        speed_stable  = abs(speed - prev_speed) < SPEED_STABLE
        slip_detected = rpm_rose and speed_stable and speed > 1.0

        if rpm > 800 and (speed > 2.0 or gps_slope > HILL_SLOPE):
            is_hill  = gps_slope > HILL_SLOPE
            is_heavy = gvw > (gvw_max * HEAVY_LOAD_RATIO)
            is_aggr  = (rpm - prev_rpm) > 400 and speed > 5.0

            if slip_detected and is_hill and is_heavy:
                event_type, base_wear = "overloaded_hill", 12.0
            elif is_hill and speed < 15.0:
                event_type, base_wear = "hill_start", 5.0
            elif slip_detected:
                event_type, base_wear = "slip", 8.0
            elif is_aggr:
                event_type, base_wear = "aggressive", 3.0
            else:
                event_type, base_wear = "normal", 1.0

            slip_ratio = round(rpm / speed, 4) if speed > 1.0 else round(rpm / 1.0, 4)
            raw_multi  = 1.0 + (slip_ratio / 100.0) + (torque / 1000.0)
            severity_multi = min(round(raw_multi, 2), MAX_MULTIPLIER)
            wear_units     = round(base_wear * severity_multi, 4)

            # Log meaningful events
            if event_type != "normal" or len(events) % 10 == 0:
                total_wear += wear_units
                events.append({
                    "vehicle_id": vehicle_id, "trip_id": trip_id, "ts": ts,
                    "event_type": event_type, "rpm": rpm, "speed_kmh": speed,
                    "slip_ratio": slip_ratio, "torque_nm": torque, "gvw_kg": gvw,
                    "gps_slope": gps_slope, "severity_multi": severity_multi, "wear_units": wear_units
                })

        prev_rpm   = rpm
        prev_speed = speed

    if events:
        db.bulk_insert_mappings(ClutchWearEvent, events)
        
        state = db.query(ComponentWearState).filter(
            ComponentWearState.vehicle_id == vehicle_id,
            ComponentWearState.component == 'clutch'
        ).first()
        if state:
            state.accumulated_wear = float(state.accumulated_wear) + total_wear
            state.last_updated = datetime.utcnow()
            
        db.commit()

    return len(events)


