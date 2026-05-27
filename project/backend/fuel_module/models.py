"""
Fuel Module — ORM Models
────────────────────────
Maps to the new 'dbo.fmc_raw_packets' and 'dbo.journey_fuel_logs1' tables.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base
import datetime

class FmcRawPacket(Base):
    __tablename__ = "fmc_raw_packets"
    __table_args__ = {"schema": "dbo"}

    id                = Column(Integer, primary_key=True, autoincrement=True)
    trip_id           = Column(String(20),  nullable=False, index=True)
    vehicle_id        = Column(String,      nullable=False)
    driver_id         = Column(String(20),  nullable=False, index=True)
    event_time        = Column(DateTime,    nullable=False)
    ignition          = Column(Boolean,     nullable=False)
    speed_kmh         = Column(Float)
    fuel_level_liters = Column(Float)
    gps_lat           = Column(Float)
    gps_lng           = Column(Float)
    created_at        = Column(DateTime,    default=datetime.datetime.utcnow)

    # Relationship to processed analytics
    analytics = relationship("JourneyFuelLog1", back_populates="raw_packet", uselist=False)


class JourneyFuelLog1(Base):
    __tablename__ = "journey_fuel_logs1"
    __table_args__ = {"schema": "dbo"}

    id                    = Column(Integer, primary_key=True, autoincrement=True)
    raw_packet_id         = Column(Integer, ForeignKey("dbo.fmc_raw_packets.id"), nullable=False)
    
    fuel_diff_liters      = Column(Float)
    
    is_refuel             = Column(Boolean, default=False)
    refuel_amount_liters  = Column(Float,   default=0)
    
    is_fuel_theft         = Column(Boolean, default=False)
    theft_amount_liters   = Column(Float,   default=0)
    theft_type            = Column(String(30), nullable=True)
    
    receipt_uploaded      = Column(Boolean, default=False)
    receipt_amount_liters = Column(Float,   default=0)
    
    created_at            = Column(DateTime, default=datetime.datetime.utcnow)

    raw_packet = relationship("FmcRawPacket", back_populates="analytics")

# Note: The old JourneyFuelLog model is kept here temporarily in case of legacy dependencies,
# but it should be phased out.
class JourneyFuelLog(Base):
    __tablename__ = "journey_fuel_logs"
    __table_args__ = {"schema": "dbo"}

    id                   = Column(Integer, primary_key=True, autoincrement=True)
    trip_id              = Column(String(20),  nullable=False, index=True)
    vehicle_id           = Column(String,      nullable=False)
    driver_id            = Column(String(20),  nullable=False, index=True)
    event_time           = Column(DateTime,  nullable=False)
    ignition             = Column(Boolean,   nullable=False)
    speed_kmh            = Column(Float)
    gps_lat              = Column(Float)
    gps_lng              = Column(Float)
    fuel_level_liters    = Column(Float)
    fuel_diff_liters     = Column(Float)
    is_refuel            = Column(Boolean, default=False)
    refuel_amount_liters = Column(Float,   default=0)
    receipt_uploaded     = Column(Boolean, default=False)
    receipt_amount_liters= Column(Float,   default=0)
    is_fuel_theft        = Column(Boolean, default=False)
    theft_amount_liters  = Column(Float,   default=0)
    theft_type           = Column(String(30), nullable=True)
