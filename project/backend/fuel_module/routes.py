"""
Fuel Module — Routes & Helpers
───────────────────────────────
1. get_fuel_theft_for_trip()  — reusable helper (called by driver_module too)
2. GET /fuel/theft/{driver_id}/{trip_id}  — standalone endpoint
3. GET /fuel/stream  — SSE endpoint for real-time fuel theft alerts
"""

import asyncio
import json
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.db import get_db, SessionLocal
from fuel_module.models import JourneyFuelLog1, FmcRawPacket
from driver_module.model import Driver
from fuel_module.schema import FuelTheftResponse, FuelTheftEvent

router = APIRouter(prefix="/fuel", tags=["Fuel Theft Detection"])


# ─────────────────────────────────────────
# REUSABLE HELPER — called from here AND
# from driver_module's /details endpoint
# ─────────────────────────────────────────
def get_fuel_theft_for_trip(db: Session, driver_id: str, trip_id: str) -> dict:
    """
    Query journey_fuel_logs1 JOIN fmc_raw_packets for all theft-flagged rows
    for the given driver + trip.  Returns a dict that
    matches the 'fuel_theft' key in the details response.
    """
    theft_rows = (
        db.query(JourneyFuelLog1, FmcRawPacket)
        .join(FmcRawPacket, JourneyFuelLog1.raw_packet_id == FmcRawPacket.id)
        .filter(
            FmcRawPacket.driver_id == driver_id,
            FmcRawPacket.trip_id == trip_id,
            JourneyFuelLog1.is_fuel_theft == True,
        )
        .order_by(FmcRawPacket.event_time)
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
    total_theft = round(sum(log.theft_amount_liters or 0.0 for log, pkt in theft_rows), 2)

    # Determine the predominant theft type
    type_counts: dict[str, int] = {}
    for log, pkt in theft_rows:
        t = log.theft_type or "UNKNOWN"
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
            sum(log.theft_amount_liters or 0 for log, pkt in theft_rows if log.theft_type == "RUNNING_THEFT"), 2
        )
        reasons.append(
            f"Running theft detected: {running_amt:.1f} L siphoned while vehicle was moving"
        )
    if "REFUEL_THEFT" in type_counts:
        refuel_amt = round(
            sum(log.theft_amount_liters or 0 for log, pkt in theft_rows if log.theft_type == "REFUEL_THEFT"), 2
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
            "id": log.id,
            "event_time": str(pkt.event_time),
            "fuel_level_liters": pkt.fuel_level_liters,
            "fuel_diff_liters": log.fuel_diff_liters,
            "theft_amount_liters": log.theft_amount_liters,
            "theft_type": log.theft_type,
            "ignition": bool(pkt.ignition),
            "speed_kmh": pkt.speed_kmh,
            "gps_lat": pkt.gps_lat,
            "gps_lng": pkt.gps_lng,
        }
        for log, pkt in theft_rows
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


# ─────────────────────────────────────────
# REAL-TIME SSE STREAM ENDPOINT
# GET /fuel/stream
# ─────────────────────────────────────────
async def event_generator(request: Request):
    """
    Polls the database for new fuel theft records every few seconds
    and yields them to the client.
    """
    import os
    resume_from_latest = os.getenv("STREAM_RESUME_FROM_LATEST", "true").lower() == "true"
    
    last_checked_id = None
    last_event_id = request.headers.get("last-event-id")

    while True:
        if await request.is_disconnected():
            break

        try:
            db = SessionLocal()
            
            # Initialization logic
            if last_checked_id is None:
                if resume_from_latest:
                    if last_event_id and last_event_id.isdigit():
                        last_checked_id = int(last_event_id)
                    else:
                        max_id = db.query(func.max(JourneyFuelLog1.id)).scalar()
                        last_checked_id = max_id or 0
                else:
                    last_checked_id = 0 # Start from the very beginning
                
                db.close()
                await asyncio.sleep(5)
                continue

            # Poll for new records that indicate fuel theft
            new_thefts = (
                db.query(JourneyFuelLog1, FmcRawPacket)
                .join(FmcRawPacket, JourneyFuelLog1.raw_packet_id == FmcRawPacket.id)
                .filter(
                    JourneyFuelLog1.id > last_checked_id,
                    JourneyFuelLog1.is_fuel_theft == True
                )
                .order_by(JourneyFuelLog1.id.asc())
                .all()
            )

            if new_thefts:
                for log, pkt in new_thefts:
                    # Look up driver name from drivers table
                    driver_obj = db.query(Driver).filter(Driver.driver_id == pkt.driver_id).first()
                    driver_name = driver_obj.driver_name if (driver_obj and driver_obj.driver_name) else pkt.driver_id

                    # Construct the event payload
                    payload = {
                        "alert_id": log.id,
                        "driver_id": pkt.driver_id,
                        "driver_name": driver_name,                        # ← NEW
                        "trip_id": pkt.trip_id,
                        "vehicle_id": pkt.vehicle_id,
                        "event_time": str(pkt.event_time),
                        "theft_type": log.theft_type,
                        "theft_amount_liters": log.theft_amount_liters,
                        "fuel_diff_liters": log.fuel_diff_liters,
                        "speed_kmh": pkt.speed_kmh,
                        "gps_lat": pkt.gps_lat,
                        "gps_lng": pkt.gps_lng,
                        "message": f"Fuel Theft Detected! {driver_name} lost {log.theft_amount_liters}L ({log.theft_type})"
                    }
                    
                    # Print the warning to the backend CMD/console so you can check it manually
                    print(f"🚨 WARNING [Real-Time]: {payload['message']}")
                    
                    yield f"id: {log.id}\ndata: {json.dumps(payload)}\n\n"
                    last_checked_id = log.id

            db.close()
        except Exception as e:
            print(f"SSE Error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            if 'db' in locals():
                db.close()
            
        # Wait before next poll
        await asyncio.sleep(5)

@router.get("/stream")
async def sse_fuel_alerts(request: Request):
    """
    Server-Sent Events endpoint for real-time fuel theft alerts.
    The client will receive an event whenever a new theft is detected.
    """
    return StreamingResponse(event_generator(request), media_type="text/event-stream")
