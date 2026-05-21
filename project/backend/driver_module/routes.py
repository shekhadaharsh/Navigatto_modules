"""
Driver Module Routes
---------------------
All API endpoints for driver behaviour & scoring.

Endpoints:
    GET /drivers/                               → All drivers list with avg score
    GET /drivers/leaderboard                    → Top & bottom performers
    GET /drivers/{driver_id}                    → Driver full profile
    GET /drivers/{driver_id}/trips              → Driver journey history
    GET /drivers/{driver_id}/trips/{trip_id}/score → Single trip score breakdown
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.db import get_db
from driver_module.model import Trip
from driver_module.scorer import calculate_trip_score, get_risk_level
from driver_module.schema import (
    DriverSummary,
    DriverDetail,
    TripSummary,
    TripScoreResponse,
    PenaltyBreakdown,
    LeaderboardItem,
    LeaderboardResponse,
)

router = APIRouter(prefix="/drivers", tags=["Driver Behaviour"])


# ─────────────────────────────────────────
# HELPER
# Calculate avg score for a list of trips
# ─────────────────────────────────────────
def _avg_score_for_trips(trips: list[Trip]) -> float:
    if not trips:
        return 0.0
    scores = []
    for t in trips:
        result = calculate_trip_score(
            accel_events=t.accel_events or 0,
            brake_events=t.brake_events or 0,
            over_speed_count=t.over_speed_count or 0,
            cornering_events=t.cornering_events or 0,
            idle_time_min=t.idle_time_min or 0.0,
            trip_duration_min=t.trip_duration_min or 1.0,
            distance_km=t.distance_km or 1.0,
        )
        scores.append(result["final_score"])
    return round(sum(scores) / len(scores), 2)


# ─────────────────────────────────────────
# GET /drivers/
# All drivers with avg score & trip count
# ─────────────────────────────────────────
@router.get("/", response_model=list[DriverSummary])
def get_all_drivers(db: Session = Depends(get_db)):
    # Get unique driver_ids with aggregated trip info
    rows = (
        db.query(
            Trip.driver_id,
            func.count(Trip.trip_id).label("total_trips"),
            func.sum(Trip.distance_km).label("total_distance"),
        )
        .group_by(Trip.driver_id)
        .all()
    )

    result = []
    for row in rows:
        trips = db.query(Trip).filter(Trip.driver_id == row.driver_id).all()
        avg_score = _avg_score_for_trips(trips)
        result.append(
            DriverSummary(
                driver_id=row.driver_id,
                total_trips=row.total_trips,
                avg_score=avg_score,
                risk_level=get_risk_level(avg_score),
                total_distance=round(row.total_distance or 0.0, 2),
            )
        )

    # Sort by avg_score descending
    result.sort(key=lambda x: x.avg_score, reverse=True)
    return result


# ─────────────────────────────────────────
# GET /drivers/leaderboard
# Top 10 & Bottom 10 performers
# ─────────────────────────────────────────
@router.get("/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(db: Session = Depends(get_db)):
    rows = (
        db.query(
            Trip.driver_id,
            func.count(Trip.trip_id).label("total_trips"),
        )
        .group_by(Trip.driver_id)
        .all()
    )

    scored = []
    for row in rows:
        trips = db.query(Trip).filter(Trip.driver_id == row.driver_id).all()
        avg_score = _avg_score_for_trips(trips)
        scored.append({
            "driver_id":   row.driver_id,
            "avg_score":   avg_score,
            "risk_level":  get_risk_level(avg_score),
            "total_trips": row.total_trips,
        })

    scored.sort(key=lambda x: x["avg_score"], reverse=True)

    top = [
        LeaderboardItem(rank=i + 1, **scored[i])
        for i in range(min(10, len(scored)))
    ]
    bottom = [
        LeaderboardItem(rank=i + 1, **scored[-(i + 1)])
        for i in range(min(10, len(scored)))
    ]

    return LeaderboardResponse(top_performers=top, bottom_performers=bottom)


# ─────────────────────────────────────────
# GET /drivers/{driver_id}
# Full driver profile with component averages
# ─────────────────────────────────────────
@router.get("/{driver_id}", response_model=DriverDetail)
def get_driver_detail(driver_id: str, db: Session = Depends(get_db)):
    trips = db.query(Trip).filter(Trip.driver_id == driver_id).all()

    if not trips:
        raise HTTPException(status_code=404, detail=f"Driver '{driver_id}' not found")

    total_trips    = len(trips)
    total_distance = sum(t.distance_km or 0.0 for t in trips)

    # Score every trip
    all_results = [
        calculate_trip_score(
            accel_events=t.accel_events or 0,
            brake_events=t.brake_events or 0,
            over_speed_count=t.over_speed_count or 0,
            cornering_events=t.cornering_events or 0,
            idle_time_min=t.idle_time_min or 0.0,
            trip_duration_min=t.trip_duration_min or 1.0,
            distance_km=t.distance_km or 1.0,
        )
        for t in trips
    ]

    def _avg(key): return round(sum(r[key] for r in all_results) / total_trips, 2)

    avg_score = _avg("final_score")

    return DriverDetail(
        driver_id=driver_id,
        total_trips=total_trips,
        avg_score=avg_score,
        risk_level=get_risk_level(avg_score),
        total_distance=round(total_distance, 2),

        # Avg raw events
        avg_accel_events=round(sum(t.accel_events or 0 for t in trips) / total_trips, 2),
        avg_brake_events=round(sum(t.brake_events or 0 for t in trips) / total_trips, 2),
        avg_over_speed=round(sum(t.over_speed_count or 0 for t in trips) / total_trips, 2),
        avg_cornering_events=round(sum(t.cornering_events or 0 for t in trips) / total_trips, 2),
        avg_idle_time=round(sum(t.idle_time_min or 0.0 for t in trips) / total_trips, 2),

        # Avg component scores
        avg_accel_score=_avg("accel_score"),
        avg_braking_score=_avg("braking_score"),
        avg_speeding_score=_avg("speeding_score"),
        avg_cornering_score=_avg("cornering_score"),
        avg_idle_score=_avg("idle_score"),
    )


# ─────────────────────────────────────────
# GET /drivers/{driver_id}/trips
# Journey history — lightweight list
# ─────────────────────────────────────────
@router.get("/{driver_id}/trips", response_model=list[TripSummary])
def get_driver_trips(driver_id: str, db: Session = Depends(get_db)):
    trips = (
        db.query(Trip)
        .filter(Trip.driver_id == driver_id)
        .order_by(Trip.trip_start.desc())
        .all()
    )

    if not trips:
        raise HTTPException(status_code=404, detail=f"No trips found for driver '{driver_id}'")

    result = []
    for t in trips:
        scored = calculate_trip_score(
            accel_events=t.accel_events or 0,
            brake_events=t.brake_events or 0,
            over_speed_count=t.over_speed_count or 0,
            cornering_events=t.cornering_events or 0,
            idle_time_min=t.idle_time_min or 0.0,
            trip_duration_min=t.trip_duration_min or 1.0,
            distance_km=t.distance_km or 1.0,
        )
        result.append(
            TripSummary(
                trip_id=t.trip_id,
                route_type=t.route_type or "Unknown",
                trip_start=t.trip_start,
                trip_end=t.trip_end,
                distance_km=t.distance_km or 0.0,
                trip_duration_min=t.trip_duration_min or 0.0,
                final_score=scored["final_score"],
                risk_level=scored["risk_level"],
            )
        )
    return result


# ─────────────────────────────────────────
# GET /drivers/{driver_id}/trips/{trip_id}/score
# Full score breakdown for a single trip
# ─────────────────────────────────────────
@router.get("/{driver_id}/trips/{trip_id}/score", response_model=TripScoreResponse)
def get_trip_score(driver_id: str, trip_id: str, db: Session = Depends(get_db)):
    trip = (
        db.query(Trip)
        .filter(Trip.driver_id == driver_id, Trip.trip_id == trip_id)
        .first()
    )

    if not trip:
        raise HTTPException(
            status_code=404,
            detail=f"Trip '{trip_id}' not found for driver '{driver_id}'"
        )

    scored = calculate_trip_score(
        accel_events=trip.accel_events or 0,
        brake_events=trip.brake_events or 0,
        over_speed_count=trip.over_speed_count or 0,
        cornering_events=trip.cornering_events or 0,
        idle_time_min=trip.idle_time_min or 0.0,
        trip_duration_min=trip.trip_duration_min or 1.0,
        distance_km=trip.distance_km or 1.0,
    )

    return TripScoreResponse(
        trip_id=trip.trip_id,
        driver_id=trip.driver_id,
        route_type=trip.route_type or "Unknown",
        distance_km=trip.distance_km or 0.0,
        trip_duration_min=trip.trip_duration_min or 0.0,

        # Raw events
        accel_events=trip.accel_events or 0,
        brake_events=trip.brake_events or 0,
        over_speed_count=trip.over_speed_count or 0,
        cornering_events=trip.cornering_events or 0,
        idle_time_min=trip.idle_time_min or 0.0,

        # Component scores
        accel_score=scored["accel_score"],
        braking_score=scored["braking_score"],
        speeding_score=scored["speeding_score"],
        cornering_score=scored["cornering_score"],
        idle_score=scored["idle_score"],

        # Penalties
        penalties=PenaltyBreakdown(**scored["penalties"]),

        # Final
        final_score=scored["final_score"],
        risk_level=scored["risk_level"],
    )


# ─────────────────────────────────────────
# GET /drivers/{driver_id}/trips/{trip_id}/details
# Combined payload — exact shape the React frontend needs.
# Combines: journey info + driver score + fuel + maintenance
# Person 2 (fuel) and Person 3 (maintenance) will replace
# the placeholder sections below with their real module calls.
# ─────────────────────────────────────────
@router.get("/{driver_id}/trips/{trip_id}/details")
def get_trip_details(driver_id: str, trip_id: str, db: Session = Depends(get_db)):
    trip = (
        db.query(Trip)
        .filter(Trip.driver_id == driver_id, Trip.trip_id == trip_id)
        .first()
    )

    if not trip:
        raise HTTPException(
            status_code=404,
            detail=f"Trip '{trip_id}' not found for driver '{driver_id}'"
        )

    # ── Driver Score ────────────────────────────
    scored = calculate_trip_score(
        accel_events=trip.accel_events or 0,
        brake_events=trip.brake_events or 0,
        over_speed_count=trip.over_speed_count or 0,
        cornering_events=trip.cornering_events or 0,
        idle_time_min=trip.idle_time_min or 0.0,
        trip_duration_min=trip.trip_duration_min or 1.0,
        distance_km=trip.distance_km or 1.0,
    )

    final_score = scored["final_score"]
    label = (
        "Good" if final_score >= 80
        else "Average" if final_score >= 60
        else "Poor"
    )

    # ── Fuel Theft Detection (Person 2 will upgrade this) ──
    actual_fuel   = trip.actual_fuel_used_L or 0.0
    expected_fuel = trip.expected_fuel_L or 0.0
    theft_occurred = bool(trip.theft_occurred)
    theft_amount   = trip.theft_amount_L or 0.0

    variance_pct = 0.0
    if expected_fuel > 0:
        variance_pct = round(((actual_fuel - expected_fuel) / expected_fuel) * 100, 2)

    # ── Maintenance signals (Person 3 will upgrade this) ──
    # Using real sensor data from DB where available
    ext_voltage   = getattr(trip, "external_voltage", None)
    coolant_temp  = getattr(trip, "temp_celsius", None)

    maint_alerts = []
    maint_priority = "OK"
    if ext_voltage is not None and ext_voltage < 11.5:
        maint_alerts.append({
            "issue": "Battery Issue",
            "severity": "Critical",
            "detail": f"External voltage drop: {ext_voltage:.1f} V (threshold < 11.5 V)"
        })
        maint_priority = "Critical"
    if coolant_temp is not None and coolant_temp > 100:
        maint_alerts.append({
            "issue": "Engine Overheating",
            "severity": "Critical",
            "detail": f"Temperature: {coolant_temp:.1f}°C exceeds max threshold of 100°C"
        })
        maint_priority = "Critical"

    if not maint_alerts and final_score < 60:
        maint_alerts.append({
            "issue": "Brake Wear",
            "severity": "Warning",
            "detail": "Harsh braking frequency suggests high wear rates"
        })
        maint_priority = "Warning"

    # ── Combined Response ─────────────────────────────────
    return {
        # ── Journey Info ──────────────────────────────────
        "journey": {
            "journey_id":           trip.trip_id,
            "driver_id":            trip.driver_id,
            "vehicle_id":           trip.vehicle_id or "N/A",
            "start_time":           str(trip.trip_start) if trip.trip_start else None,
            "end_time":             str(trip.trip_end)   if trip.trip_end   else None,
            "route_type":           trip.route_type or "Unknown",
            "distance_km":          trip.distance_km or 0.0,
            "duration_min":         trip.trip_duration_min or 0.0,
            "avg_speed_kmh":        trip.avg_speed_kmh or 0.0,
            "max_speed_kmh":        trip.max_speed_kmh or 0.0,
            "load_pct":             trip.load_pct or 0.0,
            "idle_time_min":        trip.idle_time_min or 0.0,
            "stops":                trip.num_stops or 0,
            # Behaviour events
            "acceleration_events":  trip.accel_events or 0,
            "brake_events":         trip.brake_events or 0,
            "overspeed_count":      trip.over_speed_count or 0,
            "cornering_events":     trip.cornering_events or 0,
            # Engine
            "avg_engine_rpm":       trip.avg_engine_rpm or 0.0,
            "avg_engine_load_pct":  trip.avg_engine_load_pct or 0.0,
            "avg_fuel_rate_lhr":    trip.avg_fuel_rate_Lhr or 0.0,
            # Fuel
            "fuel_consumed_liters": actual_fuel,
            "fuel_level_start":     trip.P87_fuel_start_pct or 0.0,
            "fuel_level_end":       trip.P87_fuel_end_pct or 0.0,
            # Sensors
            "external_voltage":     ext_voltage,
            "dallas_temp_celsius":  coolant_temp,
        },

        # ── Driver Score Module ───────────────────────────
        "driver_score": {
            "score": final_score,
            "label": label,
            "risk_level": scored["risk_level"],
            "breakdown": {
                "acceleration": -scored["penalties"]["accel_penalty"],
                "braking":      -scored["penalties"]["braking_penalty"],
                "overspeed":    -scored["penalties"]["speeding_penalty"],
                "cornering":    -scored["penalties"]["cornering_penalty"],
                "idle_time":    -scored["penalties"]["idle_penalty"],
            },
            "component_scores": {
                "accel_score":     scored["accel_score"],
                "braking_score":   scored["braking_score"],
                "speeding_score":  scored["speeding_score"],
                "cornering_score": scored["cornering_score"],
                "idle_score":      scored["idle_score"],
            }
        },

        # ── Fuel Theft Module (Person 2 will upgrade) ────
        "fuel_theft": {
            "detected":   theft_occurred,
            "amount_L":   theft_amount,
            "confidence": 90.0 if theft_occurred else 5.0,
            "status":     "ALERT" if theft_occurred else "NORMAL",
            "reasons":    [
                f"Theft amount detected: {theft_amount:.1f} L",
                f"Fuel variance: {variance_pct:.1f}% above expected"
            ] if theft_occurred else [],
        },

        # ── Fuel Consumption Module (Person 2) ───────────
        "expected_fuel": {
            "expected_liters": round(expected_fuel, 2),
            "actual_liters":   round(actual_fuel, 2),
            "variance_pct":    variance_pct,
        },

        # ── Maintenance Module (Person 3) ─────────────────
        "maintenance": {
            "priority":    maint_priority,
            "alert_count": len(maint_alerts),
            "alerts":      maint_alerts,
        },

        # ── Speed Profile (placeholder — upgrade with real telemetry) ──
        # Person 3 / telemetry stream can replace this with real data
        "speed_profile": None,
    }