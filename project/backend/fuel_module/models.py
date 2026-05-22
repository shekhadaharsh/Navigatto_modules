"""
Fuel Module — ORM Model
────────────────────────
Maps to the existing 'dbo.journey_fuel_logs' table in SQL Server.
Each row is a 30-second telemetry sample per vehicle per journey.
Some rows are flagged as fuel-theft events (is_fuel_theft = 1).
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from database.db import Base


class JourneyFuelLog(Base):
    __tablename__ = "journey_fuel_logs"
    __table_args__ = {"schema": "dbo"}

    # ── Identity / FK ──────────────────────────
    id                   = Column(Integer, primary_key=True, autoincrement=True)
    trip_id              = Column(String(20),  ForeignKey("dbo.journeys.trip_id"), nullable=False, index=True)
    vehicle_id           = Column(String,      ForeignKey("dbo.vehicles.id"),      nullable=False)
    driver_id            = Column(String(20),  ForeignKey("dbo.drivers.driver_id"),nullable=False, index=True)

    # ── Raw AVL telemetry (sampled every 30 s) ─
    event_time           = Column(DateTime,  nullable=False)
    ignition             = Column(Boolean,   nullable=False)
    speed_kmh            = Column(Float)
    gps_lat              = Column(Float)
    gps_lng              = Column(Float)

    # ── Fuel sensor readings ───────────────────
    fuel_level_liters    = Column(Float)
    fuel_diff_liters     = Column(Float)

    # ── Refuel tracking ────────────────────────
    is_refuel            = Column(Boolean, default=False)
    refuel_amount_liters = Column(Float,   default=0)
    receipt_uploaded     = Column(Boolean, default=False)
    receipt_amount_liters= Column(Float,   default=0)

    # ── Theft detection flags ──────────────────
    is_fuel_theft        = Column(Boolean, default=False)
    theft_amount_liters  = Column(Float,   default=0)
    theft_type           = Column(String(30), nullable=True)
    # theft_type values: REFUEL_THEFT | IGNITION_OFF_DROP | RUNNING_THEFT
