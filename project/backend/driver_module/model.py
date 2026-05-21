from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base


class Driver(Base):
    """
    Represents a driver record.
    Maps directly to 'dbo.drivers' table.
    """
    __tablename__ = "drivers"
    __table_args__ = {"schema": "dbo"}

    driver_id   = Column(String, primary_key=True)
    driver_name = Column(String)
    is_active   = Column(Boolean)

    # Relationships
    trips = relationship("Trip", back_populates="driver")

    # Backward compatibility properties
    @property
    def DriverName(self):
        return self.driver_name


class Vehicle(Base):
    """
    Represents a vehicle record.
    Maps directly to 'dbo.vehicles' table.
    """
    __tablename__ = "vehicles"
    __table_args__ = {"schema": "dbo"}

    id           = Column(String, primary_key=True) # uniqueidentifier stored as string
    vehicle_name = Column(String)
    vehicle_type = Column(String)
    is_active    = Column(Boolean)

    # Relationships
    trips = relationship("Trip", back_populates="vehicle")

    # Backward compatibility properties
    @property
    def name(self):
        return self.vehicle_name


class JourneyScore(Base):
    """
    Represents a journey's scoring and fuel telemetry calculations.
    Maps directly to 'dbo.journey_scores' table.
    """
    __tablename__ = "journey_scores"
    __table_args__ = {"schema": "dbo"}

    trip_id            = Column(String, ForeignKey("dbo.journeys.trip_id"), primary_key=True)
    vehicle_id         = Column(String, ForeignKey("dbo.vehicles.id"))
    driver_id          = Column(String, ForeignKey("dbo.drivers.driver_id"))
    actual_fuel_used_L = Column(Float)
    expected_fuel_L    = Column(Float)
    theft_occurred     = Column(String)
    theft_type         = Column(String)
    theft_amount_L     = Column(Float)
    driver_score       = Column(Float)
    created_at         = Column(DateTime)

    # Relationships
    trip = relationship("Trip", back_populates="score_relation")


class Trip(Base):
    """
    Represents a single trip record from the fleet database.
    Maps to 'dbo.journeys' table, dynamically joining related models.
    """
    __tablename__ = "journeys"
    __table_args__ = {"schema": "dbo"}

    # --- Primary Identifiers ---
    trip_id         = Column(String, primary_key=True, index=True)
    vehicle_id      = Column(String, ForeignKey("dbo.vehicles.id"), index=True)
    driver_id       = Column(String, ForeignKey("dbo.drivers.driver_id"), index=True)
    route_type      = Column(String)   # e.g. Highway, City, Mountain, Rural

    # --- Trip Time Info ---
    trip_start          = Column(DateTime)
    trip_end            = Column(DateTime)
    trip_duration_min   = Column(Float)

    # --- Vehicle Info ---
    engine_total_hour   = Column("engine_total_hours", Float)
    Total_Odometer      = Column("total_odometer", Float)

    # --- Trip Distance & Conditions ---
    distance_km         = Column(Float)
    load_pct            = Column(Float)
    temp_celsius        = Column(Float)
    hour_of_day         = Column(Integer)
    day_of_week         = Column(String)

    # --- Speed Data ---
    avg_speed_kmh       = Column(Float)
    max_speed_kmh       = Column(Float)

    # --- Driving Behaviour Events (used for scoring) ---
    idle_time_min       = Column(Float)
    num_stops           = Column(Integer)
    accel_events        = Column(Integer)   # Harsh acceleration count
    brake_events        = Column(Integer)   # Harsh braking count
    over_speed_count    = Column(Integer)   # Overspeed event count
    cornering_events    = Column(Integer)   # Harsh cornering count

    # --- Engine Data ---
    avg_engine_rpm      = Column(Float)
    avg_engine_load_pct = Column(Float)
    avg_fuel_rate_Lhr   = Column(Float)

    # --- Fuel Data ---
    P86_fuel_start_L    = Column(Float)
    P86_fuel_end_L      = Column(Float)
    P86_trip_diff_L     = Column(Float)
    P87_fuel_start_pct  = Column(Float)
    P87_fuel_end_pct    = Column(Float)
    P87_fuel_start_L    = Column(Float)
    P87_fuel_end_L      = Column(Float)
    fuel_efficiency_kmpl= Column(Float)
    refuel_L            = Column(Float)

    # Eager relationships to minimize database roundtrips
    driver = relationship("Driver", back_populates="trips", lazy="joined")
    vehicle = relationship("Vehicle", back_populates="trips", lazy="joined")
    score_relation = relationship("JourneyScore", back_populates="trip", lazy="joined", uselist=False)

    # --- Dynamic properties to keep API routes 100% backward compatible ---

    @property
    def vehicle_type(self):
        return self.vehicle.vehicle_type if self.vehicle else "Unknown"

    @property
    def actual_fuel_used_L(self):
        return self.score_relation.actual_fuel_used_L if self.score_relation else 0.0

    @property
    def expected_fuel_L(self):
        return self.score_relation.expected_fuel_L if self.score_relation else 0.0

    @property
    def theft_occurred(self):
        if not self.score_relation or not self.score_relation.theft_occurred:
            return False
        # Normalize varchar representation (e.g. "Yes", "No", "1", "0")
        val = str(self.score_relation.theft_occurred).strip().lower()
        return val in ("yes", "true", "1")

    @property
    def theft_type(self):
        return self.score_relation.theft_type if self.score_relation else None

    @property
    def theft_amount_L(self):
        return self.score_relation.theft_amount_L if self.score_relation else 0.0

    @property
    def Driver_score(self):
        return self.score_relation.driver_score if self.score_relation else None