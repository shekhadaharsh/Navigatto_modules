"""
Fuel Module — Routes & Helpers
───────────────────────────────
1. get_fuel_theft_for_trip()  — reusable helper (called by driver_module too)
2. GET /fuel/theft/{driver_id}/{trip_id}  — standalone endpoint
3. GET /fuel/stream  — SSE endpoint for real-time fuel theft alerts
"""

import asyncio
import json
from fastapi import APIRouter, Depends, Request, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.db import get_db, SessionLocal
from fuel_module.models import JourneyFuelLog1, FmcRawPacket
from driver_module.model import Driver
from fuel_module.schema import FuelTheftResponse, FuelTheftEvent
from fuel_module.predictor import predict_expected_fuel
from driver_module.model import Trip



router = APIRouter(prefix="/fuel", tags=["Fuel Theft Detection"])

# ─────────────────────────────────────────
# REUSABLE HELPER — called from here AND
# from driver_module's /details endpoint
# ─────────────────────────────────────────
def get_fuel_theft_for_trip(db: Session, driver_id: str, trip_id: str) -> dict:
    """
    Query journey_fuel_logs1 JOIN fmc_raw_packets for all theft-flagged or refuel rows
    for the given driver + trip.  Returns a dict that
    matches the 'fuel_theft' key in the details response.
    """
    all_fuel_rows = (
        db.query(JourneyFuelLog1, FmcRawPacket)
        .join(FmcRawPacket, JourneyFuelLog1.raw_packet_id == FmcRawPacket.id)
        .filter(
            FmcRawPacket.driver_id == driver_id,
            FmcRawPacket.trip_id == trip_id,
            (JourneyFuelLog1.is_fuel_theft == True) | (JourneyFuelLog1.is_refuel == True),
        )
        .order_by(FmcRawPacket.event_time)
        .all()
    )
            
    theft_rows = [r for r in all_fuel_rows if r[0].is_fuel_theft]
    refuel_rows = [r for r in all_fuel_rows if r[0].is_refuel]

    refuel_events = [
        {
            "id": log.id,
            "event_time": str(pkt.event_time),
            "refuel_amount_liters": log.refuel_amount_liters or 0.0,
            "receipt_uploaded": bool(log.receipt_uploaded),
            "receipt_amount_liters": log.receipt_amount_liters or 0.0,
            "is_fuel_theft": bool(log.is_fuel_theft),
            "theft_amount_liters": log.theft_amount_liters or 0.0,
            "theft_type": log.theft_type,
        }
        for log, pkt in refuel_rows
    ]

    if not theft_rows:
        return {
            "detected": False,
            "confidence": 5.0,
            "status": "NORMAL",
            "total_theft_liters": 0.0,
            "theft_type": None,
            "reasons": [],
            "events": [],
            "refuel_stops": refuel_events,
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
    if "INVALID_RECEIPT_DATE" in type_counts:
        reasons.append(
            "Receipt Fraud: Receipt date does not match vehicle refuel date"
        )
    if "INVALID_RECEIPT_TIME" in type_counts:
        reasons.append(
            "Receipt Fraud: Receipt time does not match vehicle refuel time"
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
        "refuel_stops": refuel_events,
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


# ─────────────────────────────────────────
# ML PREDICTION ENDPOINT
# GET /fuel/predict/{driver_id}/{trip_id}
# Returns ML-predicted expected fuel for a trip
# ─────────────────────────────────────────
@router.get(
    "/predict/{driver_id}/{trip_id}",
    summary="ML-predicted expected fuel consumption for a trip",
)
def predict_fuel_endpoint(
    driver_id: str,
    trip_id: str,
    db: Session = Depends(get_db),
):
    from fastapi import HTTPException

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

    predicted = predict_expected_fuel(
        distance_km       = trip.distance_km,
        route_type        = trip.route_type,
        load_pct          = trip.load_pct,
        vehicle_type      = trip.vehicle_type,
        engine_total_hour = trip.engine_total_hour,
        total_odometer    = trip.Total_Odometer,
        temp_celsius      = trip.temp_celsius,
        avg_engine_rpm    = trip.avg_engine_rpm,
        avg_engine_load_pct = trip.avg_engine_load_pct,
        avg_fuel_rate_lhr = trip.avg_fuel_rate_Lhr,
        avg_speed_kmh     = trip.avg_speed_kmh,
        idle_time_min     = trip.idle_time_min,
    )

    actual_fuel = trip.actual_fuel_used_L or 0.0
    variance_pct = 0.0
    if predicted and predicted > 0:
        variance_pct = round(((actual_fuel - predicted) / predicted) * 100, 2)

    return {
        "trip_id":           trip_id,
        "driver_id":         driver_id,
        "predicted_fuel_L":  predicted,
        "actual_fuel_L":     round(actual_fuel, 2),
        "variance_pct":      variance_pct,
        "model":             "xgboost_fuel_prediction_model",
    }


# ─────────────────────────────────────────
# RECEIPT UPLOAD & RECONCILIATION ENDPOINT
# POST /fuel/upload-receipt/{log_id}
# ─────────────────────────────────────────
@router.post(
    "/upload-receipt/{log_id}",
    summary="Upload a fuel receipt and reconcile with telematics refuel event",
)
async def upload_receipt_endpoint(
    log_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    from fuel_module.receipt_service import extract_receipt_details
    
    # 1. Fetch the specific refuel log entry
    log = db.query(JourneyFuelLog1).filter(JourneyFuelLog1.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail=f"Refuel log entry with ID {log_id} not found.")

    if not log.is_refuel:
        raise HTTPException(status_code=400, detail="This log entry is not a refueling stop event.")

    # 2. Read file bytes and parse using Groq Vision API
    image_bytes = await file.read()
    mime_type = file.content_type or "image/jpeg"
    
    extracted = extract_receipt_details(image_bytes, mime_type=mime_type)
    
    # Loud and clear console logs for debugging
    print("\n" + "="*60)
    print("🔥 [AI OCR RECEIPT PARSING RESULT]")
    print(f"   - Raw Response Data: {extracted}")
    print(f"   - Extracted Liters: {extracted.get('liters')} L")
    print(f"   - Extracted Price: {extracted.get('price')}")
    print(f"   - Station Name: {extracted.get('station_name')}")
    print(f"   - Transaction Time: {extracted.get('refuel_time')}")
    print("="*60 + "\n")

    receipt_liters = extracted.get("liters")
    if receipt_liters is None:
        raise HTTPException(
            status_code=422,
            detail="Failed to extract fuel quantity from receipt. Please ensure the receipt image is clear."
        )

    # 3. Time-Stamp Verification (Anti-Fraud Check)
    refuel_time_str = extracted.get("refuel_time")
    time_fraud_detected = False
    date_fraud_detected = False
    
    if refuel_time_str and log.raw_packet:
        try:
            from datetime import datetime
            # Clean and normalize raw timestamp from LLM
            clean_time_str = refuel_time_str.replace("T", " ").split(".")[0].strip()
            
            # Try parsing with various common formats
            receipt_time = None
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M", "%Y/%m/%d %H:%M:%S"):
                try:
                    receipt_time = datetime.strptime(clean_time_str, fmt)
                    break
                except ValueError:
                    continue
            
            if receipt_time:
                sensor_time = log.raw_packet.event_time
                time_diff_sec = abs((sensor_time - receipt_time).total_seconds())
                
                # Check if dates differ
                if sensor_time.date() != receipt_time.date():
                    date_fraud_detected = True
                    print(f"⚠️ [ANTI-FRAUD DETECTED] Receipt Date ({receipt_time.date()}) mismatch with Sensor Date ({sensor_time.date()})")
                elif time_diff_sec > 3600:
                    # Dates match, but time difference > 1 hour
                    time_fraud_detected = True
                    print(f"⚠️ [ANTI-FRAUD DETECTED] Receipt Time ({receipt_time}) mismatch with Sensor Time ({sensor_time}). Diff: {time_diff_sec}s")
        except Exception as e:
            print(f"[RECONCILE ERROR] Failed to parse timestamps: {e}")

    # 4. Calculate difference (Reconciliation)
    sensor_refuel = log.refuel_amount_liters or 0.0
    discrepancy = float(receipt_liters) - float(sensor_refuel)
    
    # 5. Save updates to DB
    log.receipt_uploaded = True
    log.receipt_amount_liters = float(receipt_liters)
    
    if date_fraud_detected:
        log.is_fuel_theft = True
        log.theft_amount_liters = float(receipt_liters)
        log.theft_type = "INVALID_RECEIPT_DATE"
    elif time_fraud_detected:
        log.is_fuel_theft = True
        log.theft_amount_liters = float(receipt_liters)
        log.theft_type = "INVALID_RECEIPT_TIME"
    elif discrepancy > 5.0:
        log.is_fuel_theft = True
        log.theft_amount_liters = round(discrepancy, 2)
        log.theft_type = "REFUEL_THEFT"
    else:
        # If mismatch is within threshold, clear any prior theft flags for this specific log
        log.is_fuel_theft = False
        log.theft_amount_liters = 0.0
        log.theft_type = None

    db.commit()
    db.refresh(log)

    return {
        "status": "THEFT_DETECTED" if log.is_fuel_theft else "RECONCILED",
        "receipt_liters": receipt_liters,
        "sensor_refuel_liters": sensor_refuel,
        "discrepancy_liters": round(discrepancy, 2),
        "theft_type": log.theft_type,
        "station_name": extracted.get("station_name"),
        "refuel_time": extracted.get("refuel_time")
    }

