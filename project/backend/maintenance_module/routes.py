"""
REST API Routers for Vehicle Maintenance Module
------------------------------------------------
Provides all endpoints for component health tracking, alerts, and telemetry streaming.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
from database.db import get_db

from maintenance_module.schema import (
    VehicleHealthResponse,
    ComponentHealth,
    RULResponse,
    AlertsListResponse,
    AlertResponse,
    FleetSummaryResponse,
    FleetVehicle,
    TelemetryBatch
)
from maintenance_module.engines import (
    process_vehicle_brakes,
    process_vehicle_clutch,
    process_vehicle_tires,
    process_vehicle_battery,
    process_vehicle_engine,
    run_alert_check
)

router = APIRouter(prefix="/maintenance", tags=["Vehicle Maintenance"])


# ── Background Task Runner ────────────────────────────────────
def run_all_wear_engines(vehicle_id: str, reg_no: str, db_session: Session):
    """
    Background worker that runs all wear modules and checks for alerts.
    """
    try:
        process_vehicle_brakes(db_session, vehicle_id, reg_no)
        process_vehicle_clutch(db_session, vehicle_id, reg_no)
        process_vehicle_tires(db_session, vehicle_id, reg_no)
        process_vehicle_battery(db_session, vehicle_id, reg_no)
        process_vehicle_engine(db_session, vehicle_id, reg_no)
        run_alert_check(db_session)
    except Exception as e:
        print(f"Error executing wear engines for vehicle {reg_no}: {e}")
    finally:
        db_session.close()


# ── 1. Telemetry Ingestion Endpoint ───────────────────────────
@router.post("/telemetry")
def receive_telemetry(batch: TelemetryBatch, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Stream raw telemetry packets from FMC650 OBD / CAN.
    Appends to raw_telemetry and schedules background wear checks.
    """
    if not batch.rows:
        raise HTTPException(status_code=400, detail="Empty telemetry batch")

    sql = """
        INSERT INTO raw_telemetry (
            vehicle_id, trip_id, ts, speed, rpm, engine_load, coolant_temp,
            fuel_rate, fuel_used, fuel_level, oil_pressure, engine_torque,
            engine_hours, idle_time, brake_pedal, gvw, odometer, dtc_codes,
            accel_x, accel_y, accel_z, gps_slope, latitude, longitude,
            battery_voltage, ignition, harsh_brake, harsh_accel,
            harsh_corner, overspeeding
        ) VALUES (
            :vehicle_id, :trip_id, :ts, :speed, :rpm, :engine_load, :coolant_temp,
            :fuel_rate, :fuel_used, :fuel_level, :oil_pressure, :engine_torque,
            :engine_hours, :idle_time, :brake_pedal, :gvw, :odometer, :dtc_codes,
            :accel_x, :accel_y, :accel_z, :gps_slope, :latitude, :longitude,
            :battery_voltage, :ignition, :harsh_brake, :harsh_accel,
            :harsh_corner, :overspeeding
        )
    """
    
    params = [r.dict() for r in batch.rows]
    
    try:
        db.execute(text(sql), params)
        db.commit()

        # Extract unique vehicle IDs from this batch
        vehicle_ids = list({r.vehicle_id for r in batch.rows})

        # Run background calculations using a dedicated session clone
        from database.db import SessionLocal
        for vid in vehicle_ids:
            reg_no = db.execute(
                text("SELECT reg_no FROM vehicles WHERE id = :vid"),
                {"vid": vid}
            ).scalar()
            
            if reg_no:
                bg_session = SessionLocal()
                background_tasks.add_task(run_all_wear_engines, vid, reg_no, bg_session)

        return {
            "status": "accepted",
            "rows_received": len(batch.rows),
            "vehicles": vehicle_ids,
            "message": "Wear engines started in background"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database ingestion failure: {e}")


# ── 2. Full Component Health Dashboard ────────────────────────
@router.get("/health/{vehicle_id}", response_model=VehicleHealthResponse)
def get_vehicle_health(vehicle_id: str, db: Session = Depends(get_db)):
    """
    Returns full predictive health and RUL dashboard for a vehicle.
    """
    vrow = db.execute(
        text("SELECT reg_no, make, model FROM vehicles WHERE id = :vid"),
        {"vid": vehicle_id}
    ).fetchone()

    if not vrow:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    components_res = db.execute(
        text("""
            SELECT component, accumulated_wear, base_life, rul, health_score, last_updated
            FROM component_wear_state
            WHERE vehicle_id = :vid
            ORDER BY health_score ASC
        """),
        {"vid": vehicle_id}
    ).fetchall()

    components = []
    for c in components_res:
        comp, acc, base, rul, health, updated = c
        health_val = float(health) if health is not None else 100.0
        
        status = "ok"
        if health_val < 10.0:
            status = "critical"
        elif health_val < 30.0:
            status = "warning"

        components.append(
            ComponentHealth(
                component=comp,
                accumulated_wear=float(acc),
                base_life=float(base),
                rul=float(rul) if rul is not None else float(base),
                health_score=health_val,
                status=status,
                last_updated=str(updated) if updated else None
            )
        )

    return VehicleHealthResponse(
        vehicle_id=vehicle_id,
        reg_no=vrow[0],
        make=vrow[1],
        model=vrow[2],
        components=components
    )


# ── 3. Lightweight RUL Summary ────────────────────────────────
@router.get("/rul/{vehicle_id}", response_model=RULResponse)
def get_lightweight_rul(vehicle_id: str, db: Session = Depends(get_db)):
    """
    Fast lightweight endpoint returning RUL dictionary.
    """
    res = db.execute(
        text("SELECT component, rul, health_score FROM component_wear_state WHERE vehicle_id = :vid"),
        {"vid": vehicle_id}
    ).fetchall()

    if not res:
        raise HTTPException(status_code=404, detail="No component wear data available")

    rul_dict = {
        r[0]: {"rul": float(r[1]) if r[1] is not None else 0.0, "health_score": float(r[2]) if r[2] is not None else 100.0}
        for r in res
    }

    return RULResponse(
        vehicle_id=vehicle_id,
        rul=rul_dict
    )


# ── 4. Open Maintenance Alerts ────────────────────────────────
@router.get("/alerts", response_model=AlertsListResponse)
def get_maintenance_alerts(vehicle_id: Optional[str] = None, level: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Fetch active unacknowledged predictive maintenance warnings.
    Supports optional filtering by vehicle or severity level.
    """
    query = """
        SELECT ma.id, v.reg_no, v.make, ma.component,
               ma.alert_level, ma.rul_at_alert,
               ma.health_at_alert, ma.message, ma.ts
        FROM maintenance_alerts ma
        JOIN vehicles v ON v.id = ma.vehicle_id
        WHERE ma.acknowledged = 0
    """
    params = {}
    if vehicle_id:
        query += " AND ma.vehicle_id = :vid"
        params["vid"] = vehicle_id
    if level:
        query += " AND ma.alert_level = :lvl"
        params["lvl"] = level
        
    query += " ORDER BY CASE ma.alert_level WHEN 'urgent' THEN 1 WHEN 'critical' THEN 2 ELSE 3 END, ma.ts DESC"

    res = db.execute(text(query), params).fetchall()

    alerts = []
    for r in res:
        alerts.append(
            AlertResponse(
                id=str(r[0]),
                reg_no=r[1],
                make=r[2],
                component=r[3],
                level=r[4],
                rul=float(r[5]) if r[5] is not None else 0.0,
                health=float(r[6]) if r[6] is not None else 100.0,
                message=r[7],
                ts=str(r[8])
            )
        )

    return AlertsListResponse(
        total_alerts=len(alerts),
        alerts=alerts
    )


# ── 5. Acknowledge Alert ──────────────────────────────────────
@router.post("/alerts/{alert_id}/ack")
def acknowledge_alert(alert_id: str, db: Session = Depends(get_db)):
    """
    Acknowledge a predictive warning, marking it as resolved in the dashboard.
    """
    res = db.execute(
        text("""
            UPDATE maintenance_alerts
            SET acknowledged = 1, ack_at = SYSUTCDATETIME()
            WHERE id = :alert_id
        """),
        {"alert_id": alert_id}
    )
    
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Alert not found or already acknowledged")

    db.commit()
    return {"status": "acknowledged", "alert_id": alert_id}


# ── 6. Fleet Maintenance Health Summary ───────────────────────
@router.get("/fleet", response_model=FleetSummaryResponse)
def get_fleet_summary(db: Session = Depends(get_db)):
    """
    Aggregates overall fleet component status in a single payload.
    """
    # Open alerts total count
    open_alerts = db.execute(
        text("SELECT COUNT(*) FROM maintenance_alerts WHERE acknowledged = 0")
    ).scalar() or 0

    # Group metrics per vehicle
    sql = """
        SELECT v.id, v.reg_no, v.make, v.model,
               COUNT(CASE WHEN cws.health_score < 10.0 THEN 1 END) as critical_count,
               COUNT(CASE WHEN cws.health_score BETWEEN 10.0 AND 30.0 THEN 1 END) as warning_count,
               MIN(cws.health_score) as min_health
        FROM vehicles v
        JOIN component_wear_state cws ON cws.vehicle_id = v.id
        GROUP BY v.id, v.reg_no, v.make, v.model
        ORDER BY min_health ASC
    """
    
    rows = db.execute(text(sql)).fetchall()
    
    fleet = []
    for r in rows:
        min_h = float(r[6]) if r[6] is not None else 100.0
        status = "ok"
        if r[4] > 0:
            status = "critical"
        elif r[5] > 0:
            status = "warning"

        fleet.append(
            FleetVehicle(
                vehicle_id=str(r[0]),
                reg_no=r[1],
                make=r[2],
                model=r[3],
                critical_count=r[4],
                warning_count=r[5],
                min_health=min_h,
                overall_status=status
            )
        )

    return FleetSummaryResponse(
        open_alerts=open_alerts,
        fleet=fleet
    )
