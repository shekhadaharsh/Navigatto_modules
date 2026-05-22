"""
SQLAlchemy Models for Predictive Vehicle Maintenance
------------------------------------------------------
Maps to navigatto_new database tables under the 'dbo' schema.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from database.db import Base


class ComponentWearState(Base):
    """
    Represents the live state (RUL & health score) of a vehicle component.
    Maps to 'dbo.component_wear_state'.
    """
    __tablename__ = "component_wear_state"
    __table_args__ = {"schema": "dbo"}

    id               = Column(String, primary_key=True)  # UNIQUEIDENTIFIER as String
    vehicle_id       = Column(String, ForeignKey("dbo.vehicles.id"), nullable=False)
    component        = Column(String(20), nullable=False)
    accumulated_wear = Column(Numeric(14, 4), nullable=False, default=0.0)
    base_life        = Column(Numeric(14, 4), nullable=False)
    
    # Computed columns on DB level (treated as read-only in Python)
    rul              = Column(Numeric(14, 4), read_only=True)
    health_score     = Column(Numeric(5, 2), read_only=True)
    
    last_updated     = Column(DateTime, default=None)

    # Relationships
    vehicle = relationship("driver_module.model.Vehicle")


class MaintenanceAlert(Base):
    """
    Represents proactive maintenance alerts generated when component health is low.
    Maps to 'dbo.maintenance_alerts'.
    """
    __tablename__ = "maintenance_alerts"
    __table_args__ = {"schema": "dbo"}

    id              = Column(String, primary_key=True)  # UNIQUEIDENTIFIER as String
    vehicle_id      = Column(String, ForeignKey("dbo.vehicles.id"), nullable=False)
    component       = Column(String(20), nullable=False)
    ts              = Column(DateTime, nullable=False)
    rul_at_alert    = Column(Numeric(14, 4))
    health_at_alert = Column(Numeric(5, 2))
    alert_level     = Column(String(10))  # warning | critical | urgent
    message         = Column(String(500))
    acknowledged    = Column(Boolean, default=False)
    ack_at          = Column(DateTime)

    # Relationships
    vehicle = relationship("driver_module.model.Vehicle")


class TireProfile(Base):
    """
    Tire configuration profile.
    Maps to 'dbo.tire_profiles'.
    """
    __tablename__ = "tire_profiles"
    __table_args__ = {"schema": "dbo"}

    id        = Column(String, primary_key=True)
    tire_type = Column(String(50), nullable=False, unique=True)
    base_km   = Column(Integer, nullable=False)
    coeff_a   = Column(Numeric(8, 4), nullable=False, default=1.0)
    coeff_b   = Column(Numeric(8, 4), nullable=False, default=1.0)
    coeff_c   = Column(Numeric(8, 4), nullable=False, default=1.0)
    coeff_d   = Column(Numeric(8, 4), nullable=False, default=1.0)


class ComponentBaseLife(Base):
    """
    Configuration for base component life limits.
    Maps to 'dbo.component_base_life'.
    """
    __tablename__ = "component_base_life"
    __table_args__ = {"schema": "dbo"}

    id             = Column(String, primary_key=True)
    vehicle_id     = Column(String, ForeignKey("dbo.vehicles.id"), nullable=False)
    component      = Column(String(20), nullable=False)
    base_life      = Column(Numeric(12, 2), nullable=False)
    wear_unit_type = Column(String(30))
    created_at     = Column(DateTime, nullable=False)

    # Relationships
    vehicle = relationship("driver_module.model.Vehicle")


class BrakeWearEvent(Base):
    """
    Braking events recording kinematic energy & wear units.
    Maps to 'dbo.brake_wear_events'.
    """
    __tablename__ = "brake_wear_events"
    __table_args__ = {"schema": "dbo"}

    id             = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id     = Column(String, ForeignKey("dbo.vehicles.id"), nullable=False)
    trip_id        = Column(String, ForeignKey("dbo.journeys.trip_id"), nullable=True)
    ts             = Column(DateTime, nullable=False)
    brake_count    = Column(Integer)
    event_type     = Column(String(20))
    speed_kmh      = Column(Numeric(6, 2))
    gvw_kg         = Column(Numeric(8, 2))
    gps_slope      = Column(Numeric(6, 3))
    accel_x        = Column(Numeric(6, 4))
    energy_joules  = Column(Numeric(14, 2))
    severity_multi = Column(Numeric(4, 2))
    wear_units     = Column(Numeric(8, 2))


class ClutchWearEvent(Base):
    """
    Clutch slip & start wear events.
    Maps to 'dbo.clutch_wear_events'.
    """
    __tablename__ = "clutch_wear_events"
    __table_args__ = {"schema": "dbo"}

    id             = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id     = Column(String, ForeignKey("dbo.vehicles.id"), nullable=False)
    trip_id        = Column(String, ForeignKey("dbo.journeys.trip_id"), nullable=True)
    ts             = Column(DateTime, nullable=False)
    event_type     = Column(String(20))
    rpm            = Column(Integer)
    speed_kmh      = Column(Numeric(6, 2))
    slip_ratio     = Column(Numeric(8, 4))
    torque_nm      = Column(Numeric(7, 2))
    gvw_kg         = Column(Numeric(8, 2))
    gps_slope      = Column(Numeric(6, 3))
    severity_multi = Column(Numeric(4, 2))
    wear_units     = Column(Numeric(8, 2))


class TireWearEvent(Base):
    """
    Tire wear events calculated via Section 11 math.
    Maps to 'dbo.tire_wear_events'.
    """
    __tablename__ = "tire_wear_events"
    __table_args__ = {"schema": "dbo"}

    id             = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id     = Column(String, ForeignKey("dbo.vehicles.id"), nullable=False)
    trip_id        = Column(String, ForeignKey("dbo.journeys.trip_id"), nullable=True)
    ts             = Column(DateTime, nullable=False)
    distance_km    = Column(Numeric(10, 3))
    speed_kmh      = Column(Numeric(6, 2))
    lateral_g      = Column(Numeric(6, 4))
    gvw_kg         = Column(Numeric(8, 2))
    vibration_rms  = Column(Numeric(8, 4))
    event_type     = Column(String(20))
    severity_multi = Column(Numeric(4, 2))
    wear_units     = Column(Numeric(10, 4))


class BatteryWearEvent(Base):
    """
    Battery crank & idle wear events.
    Maps to 'dbo.battery_wear_events'.
    """
    __tablename__ = "battery_wear_events"
    __table_args__ = {"schema": "dbo"}

    id             = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id     = Column(String, ForeignKey("dbo.vehicles.id"), nullable=False)
    trip_id        = Column(String, ForeignKey("dbo.journeys.trip_id"), nullable=True)
    ts             = Column(DateTime, nullable=False)
    startup_cycle  = Column(Integer)
    event_type     = Column(String(20))
    v_nominal      = Column(Numeric(5, 2))
    v_under_load   = Column(Numeric(5, 2))
    soh_percent    = Column(Numeric(5, 2))
    idle_minutes   = Column(Numeric(8, 2))
    severity_multi = Column(Numeric(4, 2))
    wear_units     = Column(Numeric(8, 2))


class EngineWearEvent(Base):
    """
    Engine thermal & load wear events.
    Maps to 'dbo.engine_wear_events'.
    """
    __tablename__ = "engine_wear_events"
    __table_args__ = {"schema": "dbo"}

    id             = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id     = Column(String, ForeignKey("dbo.vehicles.id"), nullable=False)
    trip_id        = Column(String, ForeignKey("dbo.journeys.trip_id"), nullable=True)
    ts             = Column(DateTime, nullable=False)
    rpm            = Column(Integer)
    coolant_temp   = Column(Numeric(5, 2))
    torque_nm      = Column(Numeric(7, 2))
    engine_load    = Column(Numeric(5, 2))
    fuel_rate      = Column(Numeric(7, 3))
    idle_minutes   = Column(Numeric(8, 2))
    oil_pressure   = Column(Numeric(6, 2))
    overheat       = Column(Boolean, default=False)
    event_type     = Column(String(30))
    severity_multi = Column(Numeric(4, 2))
    wear_units     = Column(Numeric(10, 4))
    dtc_codes      = Column(String(500))


class HarshEvent(Base):
    """
    HARSH EVENTS from FMC650 accelerometers and overspeed triggers.
    Maps to 'dbo.harsh_events'.
    """
    __tablename__ = "harsh_events"
    __table_args__ = {"schema": "dbo"}

    id         = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String, ForeignKey("dbo.vehicles.id"), nullable=False)
    trip_id    = Column(String, ForeignKey("dbo.journeys.trip_id"), nullable=True)
    ts         = Column(DateTime, nullable=False)
    event_type = Column(String(20))
    accel_x    = Column(Numeric(6, 4))
    lateral_g  = Column(Numeric(6, 4))
    speed_kmh  = Column(Numeric(6, 2))
    severity   = Column(String(10))
