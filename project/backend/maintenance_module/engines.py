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

try:
    AI_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'engine_wear_model.pkl')
    ENGINE_AI_MODELS = joblib.load(AI_MODEL_PATH)
except Exception as e:
    ENGINE_AI_MODELS = None
    logging.warning(f"Could not load AI model for engine wear: {e}")

# ── Wear Thresholds & Constants ──────────────────────────────
HARSH_BRAKE_G     = -0.35
HEAVY_LOAD_RATIO  = 0.85
DOWNHILL_SLOPE    = -3.0

SLIP_RPM_RISE    = 200
SPEED_STABLE     = 5.0
HILL_SLOPE       = 3.0

HIGH_SPEED_KMH   = 80.0
HARSH_CORNER_G   = 0.4
OVERLOAD_RATIO   = 0.90
ROUGH_ROAD_RMS   = 0.15

V_NOMINAL        = 12.6
LONG_IDLE_MIN    = 30.0
DEEP_DISCHARGE_V = 11.0
COLD_CRANK_V     = 9.5

MAX_MULTIPLIER   = 5.0

# ── Base Life Defaults (Self-Healing Backup) ──────────────────
DEFAULT_BASE_LIFE = {
    "brake":   20000.0,
    "clutch":  30000.0,
    "tire":    120000.0,
    "battery": 5000.0,
    "engine":  50000.0
}


# ── Helper: Ensure Wear State Initialized ─────────────────────
def ensure_wear_state_initialized(db: Session, vehicle_id: str):
    """
    Checks if component_wear_state is populated for all components.
    If not, reads from component_base_life or inserts defaults.
    """
    for component, def_life in DEFAULT_BASE_LIFE.items():
        res = db.execute(
            text("SELECT COUNT(*) FROM component_wear_state WHERE vehicle_id = :vid AND component = :comp"),
            {"vid": vehicle_id, "comp": component}
        ).scalar()
        
        if res == 0:
            # Check base life config
            base_life = db.execute(
                text("SELECT base_life FROM component_base_life WHERE vehicle_id = :vid AND component = :comp"),
                {"vid": vehicle_id, "comp": component}
            ).scalar()
            
            if not base_life:
                base_life = def_life
                
            db.execute(
                text("""
                    INSERT INTO component_wear_state (id, vehicle_id, component, accumulated_wear, base_life, last_updated)
                    VALUES (NEWID(), :vid, :comp, 0.0, :life, SYSUTCDATETIME())
                """),
                {"vid": vehicle_id, "comp": component, "life": base_life}
            )
    db.commit()


# ── 1. Brake Wear Engine ──────────────────────────────────────
def process_vehicle_brakes(db: Session, vehicle_id: str, reg_no: str):
    # Ensure wear state rows exist
    ensure_wear_state_initialized(db, vehicle_id)
    
    # 1. Get latest processed timestamp to prevent double counting
    last_ts = db.execute(
        text("SELECT MAX(ts) FROM brake_wear_events WHERE vehicle_id = :vid"),
        {"vid": vehicle_id}
    ).scalar()
    
    # 2. Fetch new telemetry rows
    if last_ts:
        result = db.execute(
            text("""
                SELECT id, ts, brake_pedal, speed, accel_x, gvw, gps_slope, trip_id
                FROM raw_telemetry
                WHERE vehicle_id = :vid AND ts > :last_ts
                ORDER BY ts ASC
            """),
            {"vid": vehicle_id, "last_ts": last_ts}
        )
    else:
        result = db.execute(
            text("""
                SELECT id, ts, brake_pedal, speed, accel_x, gvw, gps_slope, trip_id
                FROM raw_telemetry
                WHERE vehicle_id = :vid
                ORDER BY ts ASC
            """),
            {"vid": vehicle_id}
        )
        
    rows = result.fetchall()
    if not rows:
        return 0

    # 3. Determine max weight
    gvw_max = float(db.execute(
        text("SELECT MAX(gvw) FROM raw_telemetry WHERE vehicle_id = :vid"),
        {"vid": vehicle_id}
    ).scalar() or 20000.0)

    prev_brake = 0
    brake_count = db.execute(
        text("SELECT COUNT(*) FROM brake_wear_events WHERE vehicle_id = :vid"),
        {"vid": vehicle_id}
    ).scalar() or 0
    
    events = []
    total_wear = 0.0

    for row in rows:
        _, ts, brake_pedal, speed, accel_x, gvw, gps_slope, trip_id = row
        
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
                "vid": vehicle_id, "trip_id": trip_id, "ts": ts,
                "cnt": brake_count, "type": event_type, "speed": speed,
                "gvw": gvw, "slope": gps_slope, "accel": accel_x,
                "energy": energy, "multi": severity_multi, "wear": wear_units
            })
            
        prev_brake = brake_pedal

    if events:
        # Bulk Insert Events
        db.execute(
            text("""
                INSERT INTO brake_wear_events (
                    vehicle_id, trip_id, ts, brake_count, event_type,
                    speed_kmh, gvw_kg, gps_slope, accel_x,
                    energy_joules, severity_multi, wear_units
                ) VALUES (:vid, :trip_id, :ts, :cnt, :type, :speed, :gvw, :slope, :accel, :energy, :multi, :wear)
            """),
            events
        )
        
        # Update Wear State
        db.execute(
            text("""
                UPDATE component_wear_state
                SET accumulated_wear = accumulated_wear + :wear,
                    last_updated     = SYSUTCDATETIME()
                WHERE vehicle_id = :vid AND component = 'brake'
            """),
            {"wear": total_wear, "vid": vehicle_id}
        )
        db.commit()

    return len(events)


# ── 2. Clutch Wear Engine ─────────────────────────────────────
def process_vehicle_clutch(db: Session, vehicle_id: str, reg_no: str):
    ensure_wear_state_initialized(db, vehicle_id)
    
    last_ts = db.execute(
        text("SELECT MAX(ts) FROM clutch_wear_events WHERE vehicle_id = :vid"),
        {"vid": vehicle_id}
    ).scalar()
    
    if last_ts:
        result = db.execute(
            text("""
                SELECT ts, rpm, speed, engine_torque, gvw, gps_slope, trip_id
                FROM raw_telemetry
                WHERE vehicle_id = :vid AND ts > :last_ts
                ORDER BY ts ASC
            """),
            {"vid": vehicle_id, "last_ts": last_ts}
        )
    else:
        result = db.execute(
            text("""
                SELECT ts, rpm, speed, engine_torque, gvw, gps_slope, trip_id
                FROM raw_telemetry
                WHERE vehicle_id = :vid
                ORDER BY ts ASC
            """),
            {"vid": vehicle_id}
        )
        
    rows = result.fetchall()
    if not rows:
        return 0

    gvw_max = float(db.execute(
        text("SELECT MAX(gvw) FROM raw_telemetry WHERE vehicle_id = :vid"),
        {"vid": vehicle_id}
    ).scalar() or 20000.0)

    prev_rpm = 0
    prev_speed = 0.0
    events = []
    total_wear = 0.0

    for row in rows:
        ts, rpm, speed, torque, gvw, gps_slope, trip_id = row
        
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
                    "vid": vehicle_id, "trip_id": trip_id, "ts": ts,
                    "type": event_type, "rpm": rpm, "speed": speed,
                    "slip": slip_ratio, "torque": torque, "gvw": gvw,
                    "slope": gps_slope, "multi": severity_multi, "wear": wear_units
                })

        prev_rpm   = rpm
        prev_speed = speed

    if events:
        db.execute(
            text("""
                INSERT INTO clutch_wear_events (
                    vehicle_id, trip_id, ts, event_type, rpm, speed_kmh,
                    slip_ratio, torque_nm, gvw_kg, gps_slope,
                    severity_multi, wear_units
                ) VALUES (:vid, :trip_id, :ts, :type, :rpm, :speed, :slip, :torque, :gvw, :slope, :multi, :wear)
            """),
            events
        )
        
        db.execute(
            text("""
                UPDATE component_wear_state
                SET accumulated_wear = accumulated_wear + :wear,
                    last_updated     = SYSUTCDATETIME()
                WHERE vehicle_id = :vid AND component = 'clutch'
            """),
            {"wear": total_wear, "vid": vehicle_id}
        )
        db.commit()

    return len(events)


# ── 3. Tire Wear Engine ───────────────────────────────────────
def process_vehicle_tires(db: Session, vehicle_id: str, reg_no: str):
    ensure_wear_state_initialized(db, vehicle_id)
    
    last_ts = db.execute(
        text("SELECT MAX(ts) FROM tire_wear_events WHERE vehicle_id = :vid"),
        {"vid": vehicle_id}
    ).scalar()
    
    if last_ts:
        result = db.execute(
            text("""
                SELECT ts, speed, accel_y, accel_z, gvw, odometer, trip_id
                FROM raw_telemetry
                WHERE vehicle_id = :vid AND ts > :last_ts
                ORDER BY ts ASC
            """),
            {"vid": vehicle_id, "last_ts": last_ts}
        )
    else:
        result = db.execute(
            text("""
                SELECT ts, speed, accel_y, accel_z, gvw, odometer, trip_id
                FROM raw_telemetry
                WHERE vehicle_id = :vid
                ORDER BY ts ASC
            """),
            {"vid": vehicle_id}
        )
        
    rows = result.fetchall()
    if not rows:
        return 0

    # Fetch tire coefficients
    coeffs = db.execute(
        text("SELECT coeff_a, coeff_b, coeff_c, coeff_d FROM tire_profiles WHERE tire_type = 'michelin_x'")
    ).fetchone()
    a, b, c, d = (float(coeffs[0]), float(coeffs[1]), float(coeffs[2]), float(coeffs[3])) if coeffs else (1.0, 1.2, 1.1, 0.8)

    gvw_max = float(db.execute(
        text("SELECT MAX(gvw) FROM raw_telemetry WHERE vehicle_id = :vid"),
        {"vid": vehicle_id}
    ).scalar() or 20000.0)

    events = []
    total_wear = 0.0

    for row in rows:
        ts, speed, lateral_g, accel_z, gvw, odometer, trip_id = row
        
        speed     = float(speed)     if speed     is not None else 0.0
        lateral_g = float(lateral_g) if lateral_g is not None else 0.0
        accel_z   = float(accel_z)   if accel_z   is not None else 0.0
        gvw       = float(gvw)       if gvw       is not None else gvw_max * 0.7

        if speed < 1.0:
            continue

        # Segment distance (approx 1 second interval representation)
        dist_km = speed * (1.0 / 3600.0)
        vibration_rms = abs(accel_z)

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
                "vid": vehicle_id, "trip_id": trip_id, "ts": ts,
                "dist": dist_km, "speed": speed, "latg": lateral_g,
                "gvw": gvw, "vib": vibration_rms, "type": event_type,
                "multi": multiplier, "wear": wear_units
            })

    if events:
        db.execute(
            text("""
                INSERT INTO tire_wear_events (
                    vehicle_id, trip_id, ts, distance_km, speed_kmh,
                    lateral_g, gvw_kg, vibration_rms,
                    event_type, severity_multi, wear_units
                ) VALUES (:vid, :trip_id, :ts, :dist, :speed, :latg, :gvw, :vib, :type, :multi, :wear)
            """),
            events
        )
        
        db.execute(
            text("""
                UPDATE component_wear_state
                SET accumulated_wear = accumulated_wear + :wear,
                    last_updated     = SYSUTCDATETIME()
                WHERE vehicle_id = :vid AND component = 'tire'
            """),
            {"wear": total_wear, "vid": vehicle_id}
        )
        db.commit()

    return len(events)


# ── 4. Battery Wear Engine ────────────────────────────────────
def process_vehicle_battery(db: Session, vehicle_id: str, reg_no: str):
    ensure_wear_state_initialized(db, vehicle_id)
    
    last_ts = db.execute(
        text("SELECT MAX(ts) FROM battery_wear_events WHERE vehicle_id = :vid"),
        {"vid": vehicle_id}
    ).scalar()
    
    if last_ts:
        result = db.execute(
            text("""
                SELECT ts, ignition, battery_voltage, idle_time, trip_id
                FROM raw_telemetry
                WHERE vehicle_id = :vid AND ts > :last_ts
                ORDER BY ts ASC
            """),
            {"vid": vehicle_id, "last_ts": last_ts}
        )
    else:
        result = db.execute(
            text("""
                SELECT ts, ignition, battery_voltage, idle_time, trip_id
                FROM raw_telemetry
                WHERE vehicle_id = :vid
                ORDER BY ts ASC
            """),
            {"vid": vehicle_id}
        )
        
    rows = result.fetchall()
    if not rows:
        return 0

    prev_ignition = 1
    startup_cycle = db.execute(
        text("SELECT COUNT(*) FROM battery_wear_events WHERE vehicle_id = :vid"),
        {"vid": vehicle_id}
    ).scalar() or 0
    
    events = []
    total_wear = 0.0

    for row in rows:
        ts, ignition, batt_v, idle_time, trip_id = row
        
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
                "vid": vehicle_id, "trip_id": trip_id, "ts": ts,
                "cycle": startup_cycle, "type": event_type,
                "v_nom": V_NOMINAL, "v_load": v_under_load, "soh": soh,
                "idle": idle_time, "multi": severity_multi, "wear": wear_units
            })

        prev_ignition = ignition

    if events:
        db.execute(
            text("""
                INSERT INTO battery_wear_events (
                    vehicle_id, trip_id, ts, startup_cycle, event_type,
                    v_nominal, v_under_load, soh_percent, idle_minutes,
                    severity_multi, wear_units
                ) VALUES (:vid, :trip_id, :ts, :cycle, :type, :v_nom, :v_load, :soh, :idle, :multi, :wear)
            """),
            events
        )
        
        db.execute(
            text("""
                UPDATE component_wear_state
                SET accumulated_wear = accumulated_wear + :wear,
                    last_updated     = SYSUTCDATETIME()
                WHERE vehicle_id = :vid AND component = 'battery'
            """),
            {"wear": total_wear, "vid": vehicle_id}
        )
        db.commit()

    return len(events)


# ── 5. Engine Wear Engine ─────────────────────────────────────
def process_vehicle_engine(db: Session, vehicle_id: str, reg_no: str):
    ensure_wear_state_initialized(db, vehicle_id)
    
    last_ts = db.execute(
        text("SELECT MAX(ts) FROM engine_wear_events WHERE vehicle_id = :vid"),
        {"vid": vehicle_id}
    ).scalar()
    
    if last_ts:
        result = db.execute(
            text("""
                SELECT ts, rpm, coolant_temp, engine_torque, engine_load, fuel_rate, idle_time, oil_pressure, dtc_codes, trip_id
                FROM raw_telemetry
                WHERE vehicle_id = :vid AND ts > :last_ts
                ORDER BY ts ASC
            """),
            {"vid": vehicle_id, "last_ts": last_ts}
        )
    else:
        result = db.execute(
            text("""
                SELECT ts, rpm, coolant_temp, engine_torque, engine_load, fuel_rate, idle_time, oil_pressure, dtc_codes, trip_id
                FROM raw_telemetry
                WHERE vehicle_id = :vid
                ORDER BY ts ASC
            """),
            {"vid": vehicle_id}
        )
        
    rows = result.fetchall()
    if not rows:
        return 0

    events = []
    total_wear = 0.0

    for row in rows:
        ts, rpm, temp, torque, load, fuel_rate, idle_min, oil_press, dtc_codes, trip_id = row
        
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
        
        if ENGINE_AI_MODELS:
            # Use AI Model for inference
            # features: 'rpm', 'coolant_temp', 'engine_load', 'fuel_rate', 'idle_time'
            input_df = pd.DataFrame([{
                'rpm': rpm, 
                'coolant_temp': temp, 
                'engine_load': load, 
                'fuel_rate': fuel_rate, 
                'idle_time': idle_min
            }])
            
            event_type = ENGINE_AI_MODELS['event_classifier'].predict(input_df)[0]
            multi = float(ENGINE_AI_MODELS['multi_regressor'].predict(input_df)[0])
            wear_units = float(ENGINE_AI_MODELS['wear_regressor'].predict(input_df)[0])
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
                "vid": vehicle_id, "trip_id": trip_id, "ts": ts,
                "rpm": rpm, "temp": temp, "torque": torque, "load": load,
                "fuel": fuel_rate, "idle": idle_min, "oil": oil_press,
                "overheat": 1 if is_overheat else 0, "type": event_type,
                "multi": multi, "wear": wear_units, "dtc": dtc_codes or ""
            })

    if events:
        db.execute(
            text("""
                INSERT INTO engine_wear_events (
                    vehicle_id, trip_id, ts, rpm, coolant_temp, torque_nm,
                    engine_load, fuel_rate, idle_minutes, oil_pressure,
                    overheat, event_type, severity_multi, wear_units, dtc_codes
                ) VALUES (:vid, :trip_id, :ts, :rpm, :temp, :torque, :load, :fuel, :idle, :oil, :overheat, :type, :multi, :wear, :dtc)
            """),
            events
        )
        
        db.execute(
            text("""
                UPDATE component_wear_state
                SET accumulated_wear = accumulated_wear + :wear,
                    last_updated     = SYSUTCDATETIME()
                WHERE vehicle_id = :vid AND component = 'engine'
            """),
            {"wear": total_wear, "vid": vehicle_id}
        )
        db.commit()

    return len(events)


# ── 6. Alert Check Engine ─────────────────────────────────────
def run_alert_check(db: Session):
    """
    Scans component_wear_state and checks health thresholds:
    health < 30% -> WARNING alert
    health < 10% or RUL=0 -> CRITICAL/URGENT alert
    """
    result = db.execute(
        text("""
            SELECT vehicle_id, component, rul, health_score
            FROM component_wear_state
        """)
    )
    rows = result.fetchall()
    alerts_created = 0

    for row in rows:
        vid, component, rul, health = row
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
        already_open = db.execute(
            text("""
                SELECT COUNT(*) FROM maintenance_alerts
                WHERE vehicle_id = :vid AND component = :comp AND alert_level = :lvl AND acknowledged = 0
            """),
            {"vid": vid, "comp": component, "lvl": level}
        ).scalar()

        if already_open == 0:
            db.execute(
                text("""
                    INSERT INTO maintenance_alerts (id, vehicle_id, component, ts, rul_at_alert, health_at_alert, alert_level, message, acknowledged)
                    VALUES (NEWID(), :vid, :comp, SYSUTCDATETIME(), :rul, :health, :lvl, :msg, 0)
                """),
                {"vid": vid, "comp": component, "rul": rul, "health": health, "lvl": level, "msg": message}
            )
            alerts_created += 1

    if alerts_created > 0:
        db.commit()

    return alerts_created
