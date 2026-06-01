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
from sqlalchemy import func, text
import os

from database.db import get_db
from driver_module.model import Trip, Driver, Vehicle
from driver_module.scorer import calculate_trip_score, get_risk_level
from driver_module.ml_scorer import calculate_trip_score_ml
from driver_module.schema import (
    DriverSummary,
    DriverDetail,
    TripSummary,
    TripScoreResponse,
    PenaltyBreakdown,
    LeaderboardItem,
    LeaderboardResponse,
    ScoreSide,
    ScoreComparison,
)

router = APIRouter(prefix="/drivers", tags=["Driver Behaviour"])

# ── Model Version Flag & In-Memory RAM Cache (No DB changes) ──────────
# USE_ML_MODEL=1 → Old model (ml_model/ folder)
# USE_ML_MODEL=2 → New context-aware model (ml_model_v2/ folder)
_ML_MODEL_VERSION = int(os.getenv("USE_ML_MODEL", "1")) if os.getenv("USE_ML_MODEL", "1").strip().isdigit() else (1 if os.getenv("USE_ML_MODEL", "true").lower() in ("true", "yes") else 0)
USE_ML_MODEL = _ML_MODEL_VERSION in (1, 2)
_score_cache: dict = {}

def _dual_score_for_trip(trip: Trip) -> dict:
    """
    Computes both rule-based and ML safety scores for a trip.
    Utilizes in-memory caching to guarantee near 0ms execution on repeating requests.
    """
    if trip.trip_id in _score_cache:
        return _score_cache[trip.trip_id]
        
    rule_result = calculate_trip_score(
        accel_events=trip.accel_events or 0,
        brake_events=trip.brake_events or 0,
        over_speed_count=trip.over_speed_count or 0,
        cornering_events=trip.cornering_events or 0,
        idle_time_min=trip.idle_time_min or 0.0,
        trip_duration_min=trip.trip_duration_min or 1.0,
        distance_km=trip.distance_km or 1.0,
    )
    
    ml_result = calculate_trip_score_ml(
        accel_events=trip.accel_events or 0,
        brake_events=trip.brake_events or 0,
        over_speed_count=trip.over_speed_count or 0,
        cornering_events=trip.cornering_events or 0,
        idle_time_min=trip.idle_time_min or 0.0,
        trip_duration_min=trip.trip_duration_min or 1.0,
        distance_km=trip.distance_km or 1.0,
        route_type=trip.route_type or "Mixed",
        avg_speed_kmh=trip.avg_speed_kmh or 0.0,
        max_speed_kmh=trip.max_speed_kmh or 0.0,
        num_stops=trip.num_stops or 0,
        avg_engine_rpm=trip.avg_engine_rpm or 0.0,
    )
    
    result = {"rule_based": rule_result, "ml": ml_result}
    _score_cache[trip.trip_id] = result
    return result

def _get_active_score_result(dual_result: dict) -> dict:
    """
    Retrieves the score result node designated as active.
    Per client requirements, the active score served for general display
    is always the Geotab event-count Rule-Based score.
    """
    return dual_result["rule_based"]

# ─────────────────────────────────────────
# HELPER
# Calculate avg score for a list of trips
# ─────────────────────────────────────────
def _avg_score_for_trips(trips: list[Trip]) -> float:
    if not trips:
        return 0.0
    scores = []
    for t in trips:
        dual = _dual_score_for_trip(t)
        active = _get_active_score_result(dual)
        scores.append(active["final_score"])
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
        trips = db.query(Trip).filter(Trip.driver_id == row.driver_id).order_by(Trip.trip_start.desc()).all()
        
        # Calculate both ML and Rule-Based averages
        ml_scores = []
        rule_scores = []
        for t in trips:
            dual = _dual_score_for_trip(t)
            ml_scores.append(dual["ml"]["final_score"])
            rule_scores.append(dual["rule_based"]["final_score"])
            
        avg_ml = round(sum(ml_scores) / len(ml_scores), 2) if ml_scores else 0.0
        avg_rule = round(sum(rule_scores) / len(rule_scores), 2) if rule_scores else 0.0
        
        active_score = avg_rule
        
        # Get driver name from Driver table in DB
        driver_obj = db.query(Driver).filter(Driver.driver_id == row.driver_id).first()
        driver_name = driver_obj.driver_name if (driver_obj and driver_obj.driver_name) else f"Driver {row.driver_id.replace('DR', '')}"
        
        # Get vehicle type, vehicle_id, odometer, and engine hours from the latest trip
        latest_trip = trips[0] if trips else None
        vehicle_type = "Unknown"
        vehicle_id = "N/A"
        total_odometer = 0.0
        engine_hours = 0.0
        if latest_trip:
            vehicle_id = latest_trip.vehicle_id or "N/A"
            total_odometer = latest_trip.Total_Odometer or 0.0
            engine_hours = latest_trip.engine_total_hour or 0.0
            if hasattr(latest_trip, "vehicle_type") and latest_trip.vehicle_type:
                vehicle_type = latest_trip.vehicle_type
            elif latest_trip.vehicle and latest_trip.vehicle.vehicle_type:
                vehicle_type = latest_trip.vehicle.vehicle_type

        result.append(
            DriverSummary(
                driver_id=row.driver_id,
                driver_name=driver_name,
                vehicle_type=vehicle_type,
                vehicle_id=vehicle_id,
                total_odometer_km=total_odometer,
                engine_total_hours=engine_hours,
                total_trips=row.total_trips,
                avg_score=active_score,
                risk_level=get_risk_level(active_score),
                total_distance=round(row.total_distance or 0.0, 2),
                ml_score=avg_ml,
                rule_based_score=avg_rule,
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
        
        # Calculate both ML and Rule-Based averages for comparative column display
        ml_scores = []
        rule_scores = []
        for t in trips:
            dual = _dual_score_for_trip(t)
            ml_scores.append(dual["ml"]["final_score"])
            rule_scores.append(dual["rule_based"]["final_score"])
            
        avg_ml = round(sum(ml_scores) / len(ml_scores), 2) if ml_scores else 0.0
        avg_rule = round(sum(rule_scores) / len(rule_scores), 2) if rule_scores else 0.0
        
        active_score = avg_rule
        
        scored.append({
            "driver_id":   row.driver_id,
            "avg_score":   active_score,
            "risk_level":  get_risk_level(active_score),
            "total_trips": row.total_trips,
            "ml_score":    avg_ml,
            "rule_based_score": avg_rule,
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
    trips = db.query(Trip).filter(Trip.driver_id == driver_id).order_by(Trip.trip_start.desc()).all()

    if not trips:
        raise HTTPException(status_code=404, detail=f"Driver '{driver_id}' not found")

    # Fetch driver name from Driver table in DB
    driver_obj = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    driver_name = driver_obj.driver_name if (driver_obj and driver_obj.driver_name) else f"Driver {driver_id.replace('DR', '')}"

    # Get vehicle type, vehicle_id, odometer, and engine hours from the latest trip
    latest_trip = trips[0] if trips else None
    vehicle_type = "Unknown"
    vehicle_id = "N/A"
    total_odometer = 0.0
    engine_hours = 0.0
    if latest_trip:
        vehicle_id = latest_trip.vehicle_id or "N/A"
        total_odometer = latest_trip.Total_Odometer or 0.0
        engine_hours = latest_trip.engine_total_hour or 0.0
        if hasattr(latest_trip, "vehicle_type") and latest_trip.vehicle_type:
            vehicle_type = latest_trip.vehicle_type
        elif latest_trip.vehicle and latest_trip.vehicle.vehicle_type:
            vehicle_type = latest_trip.vehicle.vehicle_type

    total_trips    = len(trips)
    total_distance = sum(t.distance_km or 0.0 for t in trips)

    # Score every trip using active scoring method
    all_results = []
    for t in trips:
        dual = _dual_score_for_trip(t)
        all_results.append(_get_active_score_result(dual))

    def _avg(key): return round(sum(r[key] for r in all_results) / total_trips, 2)

    avg_score = _avg("final_score")

    return DriverDetail(
        driver_id=driver_id,
        driver_name=driver_name,
        vehicle_type=vehicle_type,
        vehicle_id=vehicle_id,
        total_odometer_km=total_odometer,
        engine_total_hours=engine_hours,
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

    from fuel_module.routes import get_fuel_theft_for_trip

    result = []
    for t in trips:
        dual = _dual_score_for_trip(t)
        active = _get_active_score_result(dual)

        theft_data = get_fuel_theft_for_trip(db, driver_id, t.trip_id)

        result.append(
            TripSummary(
                trip_id=t.trip_id,
                route_type=t.route_type or "Unknown",
                trip_start=t.trip_start,
                trip_end=t.trip_end,
                distance_km=t.distance_km or 0.0,
                trip_duration_min=t.trip_duration_min or 0.0,
                final_score=active["final_score"],
                risk_level=active["risk_level"],
                fuel_theft_detected=theft_data["detected"],
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

    dual = _dual_score_for_trip(trip)
    active = _get_active_score_result(dual)
    
    # Build comparison sides
    rule_side = ScoreSide(
        final_score=dual["rule_based"]["final_score"],
        risk_level=dual["rule_based"]["risk_level"],
        penalties=PenaltyBreakdown(**dual["rule_based"]["penalties"])
    )
    
    ml_side = ScoreSide(
        final_score=dual["ml"]["final_score"],
        risk_level=dual["ml"]["risk_level"],
        penalties=PenaltyBreakdown(**dual["ml"]["penalties"]),
        confidence=dual["ml"]["ml_confidence"]
    )
    
    comp_block = ScoreComparison(
        rule_based=rule_side,
        ml=ml_side,
        score_difference=round(dual["ml"]["final_score"] - dual["rule_based"]["final_score"], 2),
        active_method="ML" if USE_ML_MODEL else "Rule-Based"
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
        accel_score=active["accel_score"],
        braking_score=active["braking_score"],
        speeding_score=active["speeding_score"],
        cornering_score=active["cornering_score"],
        idle_score=active["idle_score"],

        # Penalties
        penalties=PenaltyBreakdown(**active["penalties"]),

        # Final
        final_score=active["final_score"],
        risk_level=active["risk_level"],
        
        # ML additions
        scoring_method=active.get("scoring_method", "Rule-Based"),
        ml_confidence=active.get("ml_confidence"),
        score_comparison=comp_block
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

    # ── Driver Score (Dual calculation & active selection) ──
    dual = _dual_score_for_trip(trip)
    scored = _get_active_score_result(dual)

    final_score = scored["final_score"]
    label = (
        "Good" if final_score >= 80
        else "Average" if final_score >= 60
        else "Poor"
    )

    # Build comparison block
    rule_side = {
        "final_score": dual["rule_based"]["final_score"],
        "risk_level":  dual["rule_based"]["risk_level"],
        "penalties":   dual["rule_based"]["penalties"],
    }
    ml_side = {
        "final_score": dual["ml"]["final_score"],
        "risk_level":  dual["ml"]["risk_level"],
        "penalties":   dual["ml"]["penalties"],
        "confidence":  dual["ml"]["ml_confidence"],
        "component_scores": {
            "accel_score":     dual["ml"]["accel_score"],
            "braking_score":   dual["ml"]["braking_score"],
            "speeding_score":  dual["ml"]["speeding_score"],
            "cornering_score": dual["ml"]["cornering_score"],
            "idle_score":      dual["ml"]["idle_score"],
        }
    }
    score_comp = {
        "rule_based": rule_side,
        "ml": ml_side,
        "score_difference": round(dual["ml"]["final_score"] - dual["rule_based"]["final_score"], 2),
        "active_method": "ML" if USE_ML_MODEL else "Rule-Based"
    }

    # ── Fuel Theft Detection (reads from journey_fuel_logs via fuel_module) ──
    from fuel_module.routes import get_fuel_theft_for_trip
    fuel_theft_data = get_fuel_theft_for_trip(db, driver_id, trip_id)

    # ── Fuel Consumption (from journey_scores — Person 2 will upgrade) ──
    # ── Fuel Consumption (ML model prediction — fuel_module/predictor.py) ──
    from fuel_module.predictor import predict_expected_fuel
    actual_fuel   = trip.actual_fuel_used_L or 0.0

    predicted_fuel = predict_expected_fuel(
        distance_km         = trip.distance_km,
        route_type          = trip.route_type,
        load_pct            = trip.load_pct,
        vehicle_type        = trip.vehicle_type,
        engine_total_hour   = trip.engine_total_hour,
        total_odometer      = trip.Total_Odometer,
        temp_celsius        = trip.temp_celsius,
        avg_engine_rpm      = trip.avg_engine_rpm,
        avg_engine_load_pct = trip.avg_engine_load_pct,
        avg_fuel_rate_lhr   = trip.avg_fuel_rate_Lhr,
        avg_speed_kmh       = trip.avg_speed_kmh,
        idle_time_min       = trip.idle_time_min,
    )
    # Fallback to DB value if model fails
    expected_fuel = predicted_fuel if predicted_fuel is not None else (trip.expected_fuel_L or 0.0)

    variance_pct = 0.0
    if expected_fuel > 0:
        variance_pct = round(((actual_fuel - expected_fuel) / expected_fuel) * 100, 2)

    # ── Maintenance signals (Person 3 - Integrated Real DB Calculations) ──
    # Note: Wear engine simulations should run in a background task, not synchronously!
    # They have been disabled here to prevent excessive API load times.

    # Fetch real sensor telemetry for this trip
    telemetry_row = db.execute(
        text("""
            SELECT TOP 1 battery_voltage, coolant_temp 
            FROM raw_telemetry 
            WHERE trip_id = :trip_id 
            ORDER BY ts DESC
        """),
        {"trip_id": trip_id}
    ).fetchone()

    ext_voltage = float(telemetry_row[0]) if telemetry_row and telemetry_row[0] is not None else 12.6
    coolant_temp = float(telemetry_row[1]) if telemetry_row and telemetry_row[1] is not None else (trip.temp_celsius or 85.0)

    # Fetch active (unacknowledged) database alerts for this vehicle
    alerts_rows = db.execute(
        text("""
            SELECT id, component, alert_level, message 
            FROM maintenance_alerts 
            WHERE vehicle_id = :vid AND acknowledged = 0
        """),
        {"vid": trip.vehicle_id}
    ).fetchall()

    maint_alerts = []
    has_critical = False
    has_warning = False

    for r in alerts_rows:
        alert_id, comp, lvl, msg = r
        sev = "Critical" if lvl in ("critical", "urgent") else "Warning"
        if sev == "Critical":
            has_critical = True
        else:
            has_warning = True

        maint_alerts.append({
            "id": str(alert_id),
            "issue": f"{comp.upper()} Issue" if "worn out" not in msg else f"{comp.upper()} Replacement Required",
            "severity": sev,
            "detail": msg
        })

    # Add real-time battery voltage alert check
    if ext_voltage < 11.5:
        if not any(a["issue"] == "Battery Issue" for a in maint_alerts):
            maint_alerts.append({
                "issue": "Battery Issue",
                "severity": "Critical",
                "detail": f"External voltage drop: {ext_voltage:.1f} V (threshold < 11.5 V)"
            })
            has_critical = True

    # Add real-time coolant temp alert check
    if coolant_temp > 100.0:
        if not any(a["issue"] == "Engine Overheating" for a in maint_alerts):
            maint_alerts.append({
                "issue": "Engine Overheating",
                "severity": "Critical",
                "detail": f"Temperature: {coolant_temp:.1f}°C exceeds max threshold of 100°C"
            })
            has_critical = True

    # Set priority based on open alerts
    if has_critical:
        maint_priority = "Critical"
    elif has_warning:
        maint_priority = "Warning"
    else:
        maint_priority = "OK"

    # Query live component wear scores
    components_res = db.execute(
        text("""
            SELECT component, health_score
            FROM component_wear_state
            WHERE vehicle_id = :vid
        """),
        {"vid": trip.vehicle_id}
    ).fetchall()

    health_scores = {c[0]: float(c[1]) if c[1] is not None else 100.0 for c in components_res}
    for comp in ["brake", "clutch", "tire", "battery", "engine"]:
        if comp not in health_scores:
            health_scores[comp] = 100.0

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
            "scoring_method": scored.get("scoring_method", "Rule-Based"),
            "ml_confidence": scored.get("ml_confidence"),
            "score_comparison": score_comp,
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

        # ── Fuel Theft Module (live from journey_fuel_logs) ─
        "fuel_theft": fuel_theft_data,

        # ── Fuel Consumption Module (Person 2) ───────────
        # ── Fuel Consumption Module (ML Predicted) ───────────
        "expected_fuel": {
            "expected_liters":  round(expected_fuel, 2),
            "actual_liters":    round(actual_fuel, 2),
            "variance_pct":     variance_pct,
            "source":           "ml_model" if predicted_fuel is not None else "db_fallback",
        },

        # ── Maintenance Module (Person 3) ─────────────────
        "maintenance": {
            "priority":    maint_priority,
            "alert_count": len(maint_alerts),
            "alerts":      maint_alerts,
            "health_scores": health_scores,
        },

        # ── Speed Profile (placeholder — upgrade with real telemetry) ──
        # Person 3 / telemetry stream can replace this with real data
        "speed_profile": None,
    }