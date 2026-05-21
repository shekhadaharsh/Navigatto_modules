from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from database.db import Base


class Trip(Base):
    """
    Represents a single trip record from the fleet database.
    Maps directly to the existing DB table columns.
    """
    __tablename__ = "truck_telemetry_MASTER_55000"
    __table_args__ = {"schema": "dbo"}

    # --- Primary Identifiers ---
    trip_id         = Column(String, primary_key=True, index=True)
    vehicle_id      = Column(String, index=True)
    vehicle_type    = Column(String)
    driver_id       = Column(String, index=True)
    route_type      = Column(String)   # e.g. Highway, City, Mountain, Rural

    # --- Trip Time Info ---
    trip_start          = Column(DateTime)
    trip_end            = Column(DateTime)
    trip_duration_min   = Column(Float)

    # --- Vehicle Info ---
    engine_total_hour   = Column(Float)
    Total_Odometer      = Column(Float)

    # --- Trip Distance & Conditions ---
    distance_km         = Column(Float)
    load_pct            = Column(Float)
    temp_celsius        = Column(Float)
    hour_of_day         = Column(Integer)
    day_of_week         = Column(Integer)

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
    actual_fuel_used_L  = Column(Float)
    expected_fuel_L     = Column(Float)
    fuel_efficiency_kmpl= Column(Float)
    refuel_L            = Column(Float)

    # --- Theft Info ---
    theft_occurred      = Column(Boolean, default=False)
    theft_type          = Column(String, nullable=True)
    theft_amount_L      = Column(Float, nullable=True)

    # --- Original DB Score (ignored for our calculation) ---
    Driver_score        = Column(Float, nullable=True)  