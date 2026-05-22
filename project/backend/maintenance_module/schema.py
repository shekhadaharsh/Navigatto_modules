"""
Pydantic Schemas for Vehicle Maintenance Module
-------------------------------------------------
Provides validation and serialization structures for REST API payloads.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ── Telemetry Input Schemas ──────────────────────────────────
class TelemetryRow(BaseModel):
    vehicle_id:      str
    ts:              str
    trip_id:         Optional[str] = None
    speed:           Optional[float] = 0.0
    rpm:             Optional[int]   = 0
    engine_load:     Optional[float] = 0.0
    coolant_temp:    Optional[float] = 0.0
    fuel_rate:       Optional[float] = 0.0
    fuel_used:       Optional[float] = 0.0
    fuel_level:      Optional[float] = 0.0
    oil_pressure:    Optional[float] = 0.0
    engine_torque:   Optional[float] = 0.0
    engine_hours:    Optional[float] = 0.0
    idle_time:       Optional[float] = 0.0
    brake_pedal:     Optional[int]   = 0
    gvw:             Optional[float] = 0.0
    odometer:        Optional[float] = 0.0
    dtc_codes:       Optional[str]   = ""
    accel_x:         Optional[float] = 0.0
    accel_y:         Optional[float] = 0.0
    accel_z:         Optional[float] = 0.0
    gps_slope:       Optional[float] = 0.0
    latitude:        Optional[float] = 0.0
    longitude:       Optional[float] = 0.0
    battery_voltage: Optional[float] = 12.6
    ignition:        Optional[int]   = 0
    harsh_brake:     Optional[int]   = 0
    harsh_accel:     Optional[int]   = 0
    harsh_corner:    Optional[int]   = 0
    overspeeding:    Optional[int]   = 0


class TelemetryBatch(BaseModel):
    rows: List[TelemetryRow]


# ── Health Response Schemas ──────────────────────────────────
class ComponentHealth(BaseModel):
    component:        str
    accumulated_wear: float
    base_life:        float
    rul:              float
    health_score:     float
    status:           str
    last_updated:     Optional[str] = None

    class Config:
        orm_mode = True


class VehicleHealthResponse(BaseModel):
    vehicle_id: str
    reg_no:     str
    make:       Optional[str] = None
    model:      Optional[str] = None
    components: List[ComponentHealth]


class RULDetail(BaseModel):
    rul:          float
    health_score: float


class RULResponse(BaseModel):
    vehicle_id: str
    rul:        dict  # Maps component_name -> RULDetail


# ── Alert Response Schemas ───────────────────────────────────
class AlertResponse(BaseModel):
    id:           str
    reg_no:       str
    make:         Optional[str] = None
    component:    str
    level:        str
    rul:          float
    health:       float
    message:      str
    ts:           str


class AlertsListResponse(BaseModel):
    total_alerts: int
    alerts:       List[AlertResponse]


# ── Fleet Summary Schemas ────────────────────────────────────
class FleetVehicle(BaseModel):
    vehicle_id:     str
    reg_no:         str
    make:           Optional[str] = None
    model:          Optional[str] = None
    critical_count: int
    warning_count:  int
    min_health:     float
    overall_status: str


class FleetSummaryResponse(BaseModel):
    open_alerts: int
    fleet:       List[FleetVehicle]
