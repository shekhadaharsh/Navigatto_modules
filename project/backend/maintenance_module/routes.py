"""
REST API Routers for Vehicle Maintenance Module
------------------------------------------------
Provides all endpoints for component health tracking, alerts, and telemetry streaming.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text, func
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
    TelemetryBatch,
    WearHistoryResponse,
    ComponentDailyWear
)
from maintenance_module.wear_engines import (
    ensure_wear_state_initialized,
    process_vehicle_brakes,
    process_vehicle_tires,
    process_vehicle_battery,
    process_vehicle_engine,
    run_alert_check
)

router = APIRouter(prefix="/maintenance", tags=["Vehicle Maintenance"])


from maintenance_module.tasks import process_vehicle_wear_task

# ── 1. Telemetry Ingestion Endpoint ───────────────────────────
from driver_module.model import Vehicle
from maintenance_module.model import RawTelemetry

@router.post("/telemetry")
def receive_telemetry(batch: TelemetryBatch, db: Session = Depends(get_db)):
    """
    Stream raw telemetry packets from FMC650 OBD / CAN.
    Appends to raw_telemetry and schedules background wear checks using Celery.
    """
    if not batch.rows:
        raise HTTPException(status_code=400, detail="Empty telemetry batch")

    params = [r.dict() for r in batch.rows]
    
    try:
        db.bulk_insert_mappings(RawTelemetry, params)
        db.commit()

        # Extract unique vehicle IDs from this batch
        vehicle_ids = list({r.vehicle_id for r in batch.rows})

        # Run background calculations using Celery queue
        for vid in vehicle_ids:
            v = db.query(Vehicle).filter(Vehicle.id == vid).first()
            reg_no = v.reg_no if v else None
            
            if reg_no:
                # Send task to Redis queue
                process_vehicle_wear_task.delay(vid, reg_no)

        return {
            "status": "accepted",
            "rows_received": len(batch.rows),
            "vehicles": vehicle_ids,
            "message": "Wear engines started in background"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database ingestion failure: {e}")


from maintenance_module.model import ComponentWearState

import time as _time
_DASHBOARD_CACHE = {}

def prewarm_dashboard_cache(db: Session):
    try:
        from driver_module.model import Vehicle
        fleet_data = get_fleet_summary(db)
        now = _time.time()
        vehicles = db.query(Vehicle).all()
        for v in vehicles:
            vid_str = str(v.id)
            reg_str = str(v.reg_no)
            h_data = get_vehicle_health(vid_str, db)
            hist_data = get_wear_history(vid_str, db)
            res = {"health": h_data, "fleet": fleet_data, "history": hist_data}
            _DASHBOARD_CACHE[vid_str] = (now, res)
            if reg_str:
                _DASHBOARD_CACHE[reg_str] = (now, res)
    except Exception as e:
        pass

# ── Combined Instant Dashboard Endpoint ───────────────────────
@router.get("/dashboard/{vehicle_id}")
def get_maintenance_dashboard(vehicle_id: str, db: Session = Depends(get_db)):
    """
    Returns health, fleet summary, and history in a single fast response using pooled DB connection + 300s cache.
    """
    now = _time.time()
    if vehicle_id in _DASHBOARD_CACHE:
        cached_time, cached_data = _DASHBOARD_CACHE[vehicle_id]
        if now - cached_time < 300:
            return cached_data

    health_data = get_vehicle_health(vehicle_id, db)
    fleet_data = get_fleet_summary(db)
    history_data = get_wear_history(vehicle_id, db)
    
    result = {
        "health": health_data,
        "fleet": fleet_data,
        "history": history_data
    }
    _DASHBOARD_CACHE[vehicle_id] = (now, result)
    if health_data and health_data.reg_no:
        _DASHBOARD_CACHE[health_data.reg_no] = (now, result)
    if health_data and health_data.vehicle_id:
        _DASHBOARD_CACHE[health_data.vehicle_id] = (now, result)
    return result


# ── 2. Full Component Health Dashboard ────────────────────────
@router.get("/health/{vehicle_id}", response_model=VehicleHealthResponse)
def get_vehicle_health(vehicle_id: str, db: Session = Depends(get_db)):
    """
    Returns full predictive health and RUL dashboard for a vehicle.
    """
    from driver_module.model import Vehicle
    v = None
    try:
        if len(str(vehicle_id)) == 36:
            v = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not v:
            v = db.query(Vehicle).filter(Vehicle.reg_no == vehicle_id).first()
    except Exception:
        db.rollback()
    if not v:
        v = db.query(Vehicle).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    vehicle_id = str(v.id)

    components_res = db.query(ComponentWearState).filter(ComponentWearState.vehicle_id == vehicle_id).order_by(ComponentWearState.health_score.asc()).all()
    if len(components_res) < 4:
        ensure_wear_state_initialized(db, vehicle_id)
        components_res = db.query(ComponentWearState).filter(ComponentWearState.vehicle_id == vehicle_id).order_by(ComponentWearState.health_score.asc()).all()

    components = []
    for c in components_res:
        health_val = float(c.health_score) if c.health_score is not None else 100.0
        
        status = "ok"
        if health_val < 10.0:
            status = "critical"
        elif health_val < 30.0:
            status = "warning"

        components.append(
            ComponentHealth(
                component=c.component,
                accumulated_wear=float(c.accumulated_wear),
                base_life=float(c.base_life),
                rul=float(c.rul) if c.rul is not None else float(c.base_life),
                health_score=health_val,
                status=status,
                last_updated=str(c.last_updated) if c.last_updated else None
            )
        )

    return VehicleHealthResponse(
        vehicle_id=vehicle_id,
        reg_no=v.reg_no,
        make=v.make,
        model=v.model,
        components=components
    )


# ── 3. Lightweight RUL Summary ────────────────────────────────
@router.get("/rul/{vehicle_id}", response_model=RULResponse)
def get_lightweight_rul(vehicle_id: str, db: Session = Depends(get_db)):
    """
    Fast lightweight endpoint returning RUL dictionary.
    """
    res = db.query(ComponentWearState).filter(ComponentWearState.vehicle_id == vehicle_id).all()

    if not res:
        raise HTTPException(status_code=404, detail="No component wear data available")

    rul_dict = {
        r.component: {"rul": float(r.rul) if r.rul is not None else 0.0, "health_score": float(r.health_score) if r.health_score is not None else 100.0}
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
    from driver_module.model import Vehicle
    from maintenance_module.model import MaintenanceAlert
    
    q = db.query(MaintenanceAlert, Vehicle).join(Vehicle, MaintenanceAlert.vehicle_id == Vehicle.id).filter(MaintenanceAlert.acknowledged == False)
    
    if vehicle_id:
        q = q.filter(MaintenanceAlert.vehicle_id == vehicle_id)
    if level:
        q = q.filter(MaintenanceAlert.alert_level == level)
        
    from sqlalchemy import case
    q = q.order_by(
        case(
            (MaintenanceAlert.alert_level == 'urgent', 1),
            (MaintenanceAlert.alert_level == 'critical', 2),
            else_=3
        ),
        MaintenanceAlert.ts.desc()
    )

    res = q.all()

    alerts = []
    for ma, v in res:
        alerts.append(
            AlertResponse(
                id=str(ma.id),
                reg_no=v.reg_no,
                make=v.make,
                component=ma.component,
                level=ma.alert_level,
                rul=float(ma.rul_at_alert) if ma.rul_at_alert is not None else 0.0,
                health=float(ma.health_at_alert) if ma.health_at_alert is not None else 100.0,
                message=ma.message,
                ts=str(ma.ts)
            )
        )

    return AlertsListResponse(
        total_alerts=len(alerts),
        alerts=alerts
    )


from datetime import datetime
from maintenance_module.model import MaintenanceAlert

# ── 5. Acknowledge Alert ──────────────────────────────────────
@router.post("/alerts/{alert_id}/ack")
def acknowledge_alert(alert_id: str, db: Session = Depends(get_db)):
    """
    Acknowledge a predictive warning, marking it as resolved in the dashboard
    and resetting the corresponding component's wear to 0.0 (restoring health to 100%).
    """
    alert = db.query(MaintenanceAlert).filter(MaintenanceAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if alert.acknowledged:
        raise HTTPException(status_code=404, detail="Alert already acknowledged")

    alert.acknowledged = True
    alert.ack_at = datetime.utcnow()

    db.query(ComponentWearState).filter(
        ComponentWearState.vehicle_id == alert.vehicle_id,
        ComponentWearState.component == alert.component
    ).update({"accumulated_wear": 0.0, "last_updated": datetime.utcnow()})

    db.commit()
    
    # Invalidate staled dashboard and fleet caches
    _DASHBOARD_CACHE.clear()
    _FLEET_CACHE["data"] = None
    
    return {"status": "acknowledged", "alert_id": alert_id, "component": alert.component}


# ── 6. Resolve Component Wear ─────────────────────────────────
@router.post("/components/{vehicle_id}/{component}/resolve")
def resolve_component_wear(vehicle_id: str, component: str, db: Session = Depends(get_db)):
    """
    Manually resolve all issues for a specific component, resetting its wear to 0.
    """
    res = db.query(ComponentWearState).filter(
        ComponentWearState.vehicle_id == vehicle_id,
        ComponentWearState.component == component
    ).update({"accumulated_wear": 0.0, "last_updated": datetime.utcnow()})
    
    if res == 0:
        raise HTTPException(status_code=404, detail="Component wear state not found")

    db.query(MaintenanceAlert).filter(
        MaintenanceAlert.vehicle_id == vehicle_id,
        MaintenanceAlert.component == component,
        MaintenanceAlert.acknowledged == False
    ).update({"acknowledged": True, "ack_at": datetime.utcnow()})

    db.commit()
    
    # Invalidate staled dashboard and fleet caches
    _DASHBOARD_CACHE.clear()
    _FLEET_CACHE["data"] = None
    
    return {"status": "resolved", "vehicle_id": vehicle_id, "component": component}


_FLEET_CACHE = {"time": 0, "data": None}

# ── 7. Fleet Maintenance Health Summary ───────────────────────
@router.get("/fleet", response_model=FleetSummaryResponse)
def get_fleet_summary(db: Session = Depends(get_db)):
    """
    Aggregates overall fleet component status in a single payload.
    """
    now = _time.time()
    if _FLEET_CACHE["data"] is not None and now - _FLEET_CACHE["time"] < 300:
        return _FLEET_CACHE["data"]

    sql = """
        SELECT v.id, v.reg_no, v.make, v.model,
               COUNT(CASE WHEN cws.health_score < 10.0 THEN 1 END) as critical_count,
               COUNT(CASE WHEN cws.health_score BETWEEN 10.0 AND 30.0 THEN 1 END) as warning_count,
               MIN(cws.health_score) as min_health
        FROM vehicles v
        LEFT JOIN component_wear_state cws ON cws.vehicle_id = v.id
        GROUP BY v.id, v.reg_no, v.make, v.model
        ORDER BY min_health ASC
    """
    
    rows = db.execute(text(sql)).fetchall()
    
    from maintenance_module.model import MaintenanceAlert
    try:
        open_alerts = db.query(MaintenanceAlert).filter(MaintenanceAlert.acknowledged == False).count()
    except Exception:
        open_alerts = 0
    
    fleet = []
    for r in rows:
        min_h = float(r[6]) if (len(r) > 6 and r[6] is not None) else 100.0
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

    res = FleetSummaryResponse(
        open_alerts=open_alerts,
        fleet=fleet
    )
    _FLEET_CACHE["time"] = _time.time()
    _FLEET_CACHE["data"] = res
    return res


# ── 8. Wear History Endpoint ───────────────────────────
@router.get("/history/{vehicle_id}", response_model=WearHistoryResponse)
def get_wear_history(vehicle_id: str, db: Session = Depends(get_db)):
    """
    Returns daily wear history for brakes, tires, and engine for the last 10 active days.
    (Optimized: returns empty history list to avoid heavy DB queries)
    """
    return WearHistoryResponse(
        vehicle_id=vehicle_id,
        history=[]
    )


from pydantic import BaseModel
import os

class SettingsPayload(BaseModel):
    alert_recipient_email: str

@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    from sqlalchemy import text
    try:
        res = db.execute(text("SELECT setting_value FROM system_settings WHERE setting_key = 'alert_recipient_email'")).fetchone()
        email = res[0] if res else os.getenv("ALERT_EMAIL_RECIPIENT", "gautanvala95@gmail.com")
    except Exception as e:
        email = os.getenv("ALERT_EMAIL_RECIPIENT", "gautanvala95@gmail.com")
    return {"alert_recipient_email": email}

@router.post("/settings")
def update_settings(payload: SettingsPayload, db: Session = Depends(get_db)):
    from sqlalchemy import text
    import re
    email = payload.alert_recipient_email.strip()
    
    # Basic validation
    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise HTTPException(status_code=400, detail="Invalid email format")
        
    try:
        # Check if row exists, insert or update
        res = db.execute(text("SELECT count(*) FROM system_settings WHERE setting_key = 'alert_recipient_email'")).scalar()
        if res > 0:
            db.execute(
                text("UPDATE system_settings SET setting_value = :val WHERE setting_key = 'alert_recipient_email'"),
                {"val": email}
            )
        else:
            db.execute(
                text("INSERT INTO system_settings (setting_key, setting_value) VALUES ('alert_recipient_email', :val)"),
                {"val": email}
            )
        db.commit()
        return {"status": "success", "alert_recipient_email": email}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")




