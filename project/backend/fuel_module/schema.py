"""
Fuel Module — Pydantic Schemas
───────────────────────────────
Response models used by the fuel-theft API endpoints.
"""

from typing import List, Optional
from pydantic import BaseModel


class FuelTheftEvent(BaseModel):
    """One individual theft record from journey_fuel_logs."""
    id: int
    event_time: str
    fuel_level_liters: Optional[float] = None
    fuel_diff_liters: Optional[float] = None
    theft_amount_liters: Optional[float] = None
    theft_type: Optional[str] = None
    ignition: bool = False
    speed_kmh: Optional[float] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None


class FuelTheftResponse(BaseModel):
    """
    Shape consumed by the React frontend's Fuel Theft card.
    Matches: journeyDetails.fuel_theft
    """
    detected: bool = False
    confidence: float = 0.0
    status: str = "NORMAL"
    total_theft_liters: float = 0.0
    theft_type: Optional[str] = None
    reasons: List[str] = []
    events: List[FuelTheftEvent] = []
