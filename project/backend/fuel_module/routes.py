"""
Fuel Module — Routes & Helpers
───────────────────────────────
1. get_fuel_theft_for_trip()  — reusable helper (called by driver_module too)
2. GET /fuel/theft/{driver_id}/{trip_id}  — standalone endpoint

All theft detection reads from the 'journey_fuel_logs' table.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.db import get_db
from fuel_module.models import JourneyFuelLog
from fuel_module.schema import FuelTheftResponse, FuelTheftEvent

router = APIRouter(prefix="/fuel", tags=["Fuel Theft Detection"])


# ─────────────────────────────────────────
# REUSABLE HELPER — called from here AND
# from driver_module's /details endpoint
# ─────────────────────────────────────────
def get_fuel_theft_for_trip(db: Session, driver_id: str, trip_id: str) -> dict:
    """
    Query journey_fuel_logs for all theft-flagged rows
    for the given driver + trip.  Returns a dict that
    matches the 'fuel_theft' key in the details response.
    """
    theft_rows = (
        db.query(JourneyFuelLog)
        .filter(
            JourneyFuelLog.driver_id == driver_id,
            JourneyFuelLog.trip_id == trip_id,
            JourneyFuelLog.is_fuel_theft == True,
        )
        .order_by(JourneyFuelLog.event_time)
        .all()
    )

    if not theft_rows:
        return {
            "detected": False,
            "confidence": 5.0,
            "status": "NORMAL",
            "total_theft_liters": 0.0,
            "theft_type": None,
            "reasons": [],
            "events": [],
        }

    # ── Aggregate across all theft rows ──
    total_theft = round(sum(r.theft_amount_liters or 0.0 for r in theft_rows), 2)

    # Determine the predominant theft type
    type_counts: dict[str, int] = {}
    for r in theft_rows:
        t = r.theft_type or "UNKNOWN"
        type_counts[t] = type_counts.get(t, 0) + 1
    primary_type = max(type_counts, key=type_counts.get)

    # Build human-readable reasons
    reasons = []
    if "IGNITION_OFF_DROP" in type_counts:
        count = type_counts["IGNITION_OFF_DROP"]
        reasons.append(
            f"Fuel dropped {total_theft:.1f} L across {count} readings while ignition was OFF"
        )
    if "RUNNING_THEFT" in type_counts:
        running_amt = round(
            sum(r.theft_amount_liters or 0 for r in theft_rows if r.theft_type == "RUNNING_THEFT"), 2
        )
        reasons.append(
            f"Running theft detected: {running_amt:.1f} L siphoned while vehicle was moving"
        )
    if "REFUEL_THEFT" in type_counts:
        refuel_amt = round(
            sum(r.theft_amount_liters or 0 for r in theft_rows if r.theft_type == "REFUEL_THEFT"), 2
        )
        reasons.append(
            f"Refuel theft: {refuel_amt:.1f} L discrepancy between receipt and sensor during refueling"
        )
    if not reasons:
        reasons.append(f"Anomalous fuel drop of {total_theft:.1f} L detected")

    # Confidence heuristic: more events & larger amounts = higher confidence
    confidence = min(95.0, 60.0 + len(theft_rows) * 5.0)

    # Build per-event detail list
    events = [
        {
            "id": r.id,
            "event_time": str(r.event_time),
            "fuel_level_liters": r.fuel_level_liters,
            "fuel_diff_liters": r.fuel_diff_liters,
            "theft_amount_liters": r.theft_amount_liters,
            "theft_type": r.theft_type,
            "ignition": bool(r.ignition),
            "speed_kmh": r.speed_kmh,
            "gps_lat": r.gps_lat,
            "gps_lng": r.gps_lng,
        }
        for r in theft_rows
    ]

    return {
        "detected": True,
        "confidence": confidence,
        "status": "ALERT",
        "total_theft_liters": total_theft,
        "theft_type": primary_type,
        "reasons": reasons,
        "events": events,
    }


# ─────────────────────────────────────────
# STANDALONE ENDPOINT
# GET /fuel/theft/{driver_id}/{trip_id}
# ─────────────────────────────────────────
@router.get(
    "/theft/{driver_id}/{trip_id}",
    response_model=FuelTheftResponse,
    summary="Fuel theft detection for a driver + trip",
)
def fuel_theft_endpoint(
    driver_id: str,
    trip_id: str,
    db: Session = Depends(get_db),
):
    return get_fuel_theft_for_trip(db, driver_id, trip_id)
