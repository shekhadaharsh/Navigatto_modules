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
from maintenance_module.wear_engines import (
    ensure_wear_state_initialized,
    process_vehicle_brakes,
    process_vehicle_clutch,
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

# ── 2. Full Component Health Dashboard ────────────────────────
@router.get("/health/{vehicle_id}", response_model=VehicleHealthResponse)
def get_vehicle_health(vehicle_id: str, db: Session = Depends(get_db)):
    """
    Returns full predictive health and RUL dashboard for a vehicle.
    """
    from driver_module.model import Vehicle
    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # Run the engines dynamically to calculate wear based on existing raw telemetry
    try:
        ensure_wear_state_initialized(db, vehicle_id)
        process_vehicle_brakes(db, vehicle_id, v.reg_no)
        process_vehicle_clutch(db, vehicle_id, v.reg_no)
        process_vehicle_tires(db, vehicle_id, v.reg_no)
        process_vehicle_battery(db, vehicle_id, v.reg_no)
        process_vehicle_engine(db, vehicle_id, v.reg_no)
        run_alert_check(db)
    except Exception as e:
        print(f"Error executing wear engines dynamically for vehicle {v.reg_no}: {e}")

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
    return {"status": "resolved", "vehicle_id": vehicle_id, "component": component}


# ── 7. Fleet Maintenance Health Summary ───────────────────────
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


