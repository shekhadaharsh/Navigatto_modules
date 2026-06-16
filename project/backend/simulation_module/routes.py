"""
Simulation Module Routes
--------------------------
Provides API endpoints for the DeviceSimulator UI panel.

Endpoints:
    POST /api/simulation/inject-trip    → Inject a manual trip into DB + auto ML score
    POST /api/simulation/add-driver     → Register a new driver in DB
    POST /api/simulation/add-vehicle    → Register a new vehicle in DB
    GET  /api/simulation/vehicles       → List all vehicles (for UI dropdowns)
"""

import datetime
import random
import string

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from database.db import get_db
from driver_module.model import Driver, Vehicle, Trip, JourneyScore
from driver_module.ml_scorer import calculate_trip_score_ml
from driver_module.scorer import calculate_trip_score

router = APIRouter(prefix="/simulation", tags=["Simulator & Manual Inputs"])


# ─────────────────────────────────────────
# Pydantic Schemas
# ─────────────────────────────────────────

class InjectTripRequest(BaseModel):
    driver_id:          str
    vehicle_id:         str
    route_type:         str = "Mixed"
    distance_km:        float
    duration_min:       float
    avg_speed_kmh:      float
    max_speed_kmh:      float
    num_stops:          int   = 0
    avg_engine_rpm:     float = 1800.0
    accel_events:       int   = 0
    brake_events:       int   = 0
    over_speed_count:   int   = 0
    cornering_events:   int   = 0
    idle_time_min:      float = 0.0
    actual_fuel_used_l: float = 0.0
    battery_voltage:    float = 14.1
    coolant_temp:       float = 85.0


class AddDriverRequest(BaseModel):
    driver_id:    str
    name:         str
    is_active:    bool = True


class AddVehicleRequest(BaseModel):
    vehicle_id:   str
    reg_no:       str
    vehicle_name: Optional[str] = None
    vehicle_type: str = "Mini Truck"
    make:         Optional[str] = None
    model:        Optional[str] = None
    is_active:    bool = True


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────

def _generate_trip_id(db: Session) -> str:
    """Generate a unique trip ID that doesn't clash with existing ones."""
    for _ in range(20):
        suffix = "".join(random.choices(string.digits, k=5))
        trip_id = f"SIM{suffix}"
        exists = db.query(Trip.trip_id).filter(Trip.trip_id == trip_id).first()
        if not exists:
            return trip_id
    raise RuntimeError("Could not generate unique trip ID after 20 attempts")


# ─────────────────────────────────────────
# POST /api/simulation/inject-trip
# ─────────────────────────────────────────

@router.post("/inject-trip")
def inject_trip(payload: InjectTripRequest, db: Session = Depends(get_db)):
    """
    Injects a manually crafted trip telemetry record directly into the database.
    - Validates driver and vehicle exist.
    - Saves Trip row in dbo.journeys.
    - Runs ML scorer and saves JourneyScore row in dbo.journey_scores.
    - Returns the new trip_id and computed ML safety score.
    """

    # 1. Validate driver exists
    driver = db.query(Driver).filter(Driver.driver_id == payload.driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=404,
            detail=f"Driver '{payload.driver_id}' not found in DB. Register the driver first."
        )

    # 2. Validate vehicle exists
    vehicle = db.query(Vehicle).filter(Vehicle.id == payload.vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=404,
            detail=f"Vehicle '{payload.vehicle_id}' not found in DB. Add the vehicle first."
        )

    # 3. Generate unique trip ID
    trip_id = _generate_trip_id(db)
    now = datetime.datetime.now()

    # 4. Create Trip record
    trip = Trip(
        trip_id             = trip_id,
        driver_id           = payload.driver_id,
        vehicle_id          = payload.vehicle_id,
        route_type          = payload.route_type,
        trip_start          = now - datetime.timedelta(minutes=payload.duration_min),
        trip_end            = now,
        trip_duration_min   = payload.duration_min,
        distance_km         = payload.distance_km,
        avg_speed_kmh       = payload.avg_speed_kmh,
        max_speed_kmh       = payload.max_speed_kmh,
        idle_time_min       = payload.idle_time_min,
        num_stops           = payload.num_stops,
        accel_events        = payload.accel_events,
        brake_events        = payload.brake_events,
        over_speed_count    = payload.over_speed_count,
        cornering_events    = payload.cornering_events,
        avg_engine_rpm      = payload.avg_engine_rpm,
        avg_engine_load_pct = 58.0,
        avg_fuel_rate_Lhr   = 8.4,
        # Fuel sensors
        P86_fuel_start_L    = 100.0,
        P86_fuel_end_L      = max(0.0, 100.0 - payload.actual_fuel_used_l),
        P86_trip_diff_L     = payload.actual_fuel_used_l,
        P87_fuel_start_pct  = 94.5,
        P87_fuel_end_pct    = max(0.0, 94.5 - (payload.actual_fuel_used_l / 2.0)),
        P87_fuel_start_L    = 100.0,
        P87_fuel_end_L      = max(0.0, 100.0 - payload.actual_fuel_used_l),
        fuel_efficiency_kmpl= round(payload.distance_km / payload.actual_fuel_used_l, 2) if payload.actual_fuel_used_l > 0 else 0.0,
        refuel_L            = 0.0,
        # Odometer/engine hours — carry forward from latest vehicle trip
        engine_total_hour   = 0.0,
        Total_Odometer      = 0.0,
        # Additional data
        load_pct            = 68.0,
        temp_celsius        = payload.coolant_temp,
        hour_of_day         = now.hour,
        day_of_week         = str(now.weekday()),
    )
    db.add(trip)

    # 5. Compute ML safety score
    try:
        ml_result = calculate_trip_score_ml(
            accel_events     = payload.accel_events,
            brake_events     = payload.brake_events,
            over_speed_count = payload.over_speed_count,
            cornering_events = payload.cornering_events,
            idle_time_min    = payload.idle_time_min,
            trip_duration_min= payload.duration_min,
            distance_km      = payload.distance_km,
            route_type       = payload.route_type,
            avg_speed_kmh    = payload.avg_speed_kmh,
            max_speed_kmh    = payload.max_speed_kmh,
            num_stops        = payload.num_stops,
            avg_engine_rpm   = payload.avg_engine_rpm,
        )
        ml_score = ml_result["final_score"]
    except Exception as e:
        print(f"[SimulatorAPI] ML scorer failed, falling back to rule-based: {e}")
        rule_result = calculate_trip_score(
            accel_events     = payload.accel_events,
            brake_events     = payload.brake_events,
            over_speed_count = payload.over_speed_count,
            cornering_events = payload.cornering_events,
            idle_time_min    = payload.idle_time_min,
            trip_duration_min= payload.duration_min,
            distance_km      = payload.distance_km,
        )
        ml_score = rule_result["final_score"]

    # 6. Fuel theft detection heuristic
    expected_fuel_rough = payload.distance_km * 0.15
    theft_occurred = payload.actual_fuel_used_l > (expected_fuel_rough * 1.30)
    theft_amount   = round(payload.actual_fuel_used_l - expected_fuel_rough, 2) if theft_occurred else 0.0

    # 7. Save JourneyScore record
    journey_score = JourneyScore(
        trip_id            = trip_id,
        vehicle_id         = payload.vehicle_id,
        driver_id          = payload.driver_id,
        actual_fuel_used_L = payload.actual_fuel_used_l,
        expected_fuel_L    = round(expected_fuel_rough, 2),
        theft_occurred     = "Yes" if theft_occurred else "No",
        theft_type         = "Siphon" if theft_occurred else None,
        theft_amount_L     = theft_amount,
        driver_score       = ml_score,
        created_at         = now,
    )
    db.add(journey_score)

    # 8. Commit everything
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB commit failed: {str(e)}")

    print(f"[SimulatorAPI] Injected trip {trip_id} for driver {payload.driver_id} | ML Score: {ml_score} | Theft: {theft_occurred}")

    return {
        "status":           "success",
        "trip_id":          trip_id,
        "driver_id":        payload.driver_id,
        "vehicle_id":       payload.vehicle_id,
        "ml_score":         ml_score,
        "fuel_theft":       theft_occurred,
        "theft_amount_l":   theft_amount,
        "message":          f"Trip {trip_id} injected successfully. ML Safety Score: {ml_score}"
    }


# ─────────────────────────────────────────
# POST /api/simulation/add-driver
# ─────────────────────────────────────────

@router.post("/add-driver")
def add_driver(payload: AddDriverRequest, db: Session = Depends(get_db)):
    """
    Register a new driver in the dbo.drivers table.
    Returns 409 Conflict if driver_id already exists.
    """

    # Check for duplicate
    existing = db.query(Driver).filter(Driver.driver_id == payload.driver_id).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Driver '{payload.driver_id}' already exists in DB."
        )

    new_driver = Driver(
        driver_id   = payload.driver_id,
        driver_name = payload.name,
        is_active   = payload.is_active,
    )
    db.add(new_driver)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB commit failed: {str(e)}")

    print(f"[SimulatorAPI] Registered new driver: {payload.driver_id} — {payload.name}")

    return {
        "status":    "success",
        "driver_id": payload.driver_id,
        "name":      payload.name,
        "message":   f"Driver {payload.name} ({payload.driver_id}) registered successfully."
    }


# ─────────────────────────────────────────
# POST /api/simulation/add-vehicle
# ─────────────────────────────────────────

@router.post("/add-vehicle")
def add_vehicle(payload: AddVehicleRequest, db: Session = Depends(get_db)):
    """
    Register a new vehicle in the dbo.vehicles table.
    Returns 409 Conflict if vehicle_id already exists.
    """

    # Check for duplicate
    existing = db.query(Vehicle).filter(Vehicle.id == payload.vehicle_id).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Vehicle '{payload.vehicle_id}' already exists in DB."
        )

    new_vehicle = Vehicle(
        id           = payload.vehicle_id,
        reg_no       = payload.reg_no,
        vehicle_name = payload.vehicle_name or f"{payload.make or 'Vehicle'} {payload.model or ''}".strip(),
        vehicle_type = payload.vehicle_type,
        make         = payload.make,
        model        = payload.model,
        is_active    = payload.is_active,
    )
    db.add(new_vehicle)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB commit failed: {str(e)}")

    print(f"[SimulatorAPI] Registered new vehicle: {payload.vehicle_id} [{payload.vehicle_type}]")

    return {
        "status":     "success",
        "vehicle_id": payload.vehicle_id,
        "reg_no":     payload.reg_no,
        "message":    f"Vehicle {payload.vehicle_id} ({payload.reg_no}) registered successfully."
    }


# ─────────────────────────────────────────
# GET /api/simulation/vehicles
# List all vehicles for UI dropdown
# ─────────────────────────────────────────

@router.get("/vehicles")
def get_vehicles(db: Session = Depends(get_db)):
    """
    Returns all vehicles from DB for use in the DeviceSimulator dropdown.
    """
    vehicles = db.query(Vehicle).filter(Vehicle.is_active == True).all()
    return [
        {
            "vehicle_id":   v.id,
            "reg_no":       v.reg_no or "",
            "vehicle_name": v.vehicle_name or v.id,
            "vehicle_type": v.vehicle_type or "Mini Truck",
            "make":         v.make or "",
            "model":        v.model or "",
            "is_active":    v.is_active,
        }
        for v in vehicles
    ]
