import os
import sys
from sqlalchemy import text

sys.path.append(os.path.dirname(__file__))
from database.db import SessionLocal

def create_remaining_indexes():
    db = SessionLocal()
    try:
        print("Creating remaining database indexes to optimize retrieval speeds across all active tables...")
        
        # 1. raw_telemetry(trip_id)
        db.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_raw_telemetry_trip_id' AND object_id = OBJECT_ID('dbo.raw_telemetry'))
            CREATE NONCLUSTERED INDEX IX_raw_telemetry_trip_id ON dbo.raw_telemetry(trip_id);
        """))
        
        # 2. raw_telemetry(vehicle_id)
        db.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_raw_telemetry_vehicle_id' AND object_id = OBJECT_ID('dbo.raw_telemetry'))
            CREATE NONCLUSTERED INDEX IX_raw_telemetry_vehicle_id ON dbo.raw_telemetry(vehicle_id);
        """))
        
        # 3. fmc_raw_packets(trip_id)
        db.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_fmc_raw_packets_trip_id' AND object_id = OBJECT_ID('dbo.fmc_raw_packets'))
            CREATE NONCLUSTERED INDEX IX_fmc_raw_packets_trip_id ON dbo.fmc_raw_packets(trip_id);
        """))
        
        # 4. journey_fuel_logs1(raw_packet_id)
        db.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_journey_fuel_logs1_raw_packet_id' AND object_id = OBJECT_ID('dbo.journey_fuel_logs1'))
            CREATE NONCLUSTERED INDEX IX_journey_fuel_logs1_raw_packet_id ON dbo.journey_fuel_logs1(raw_packet_id);
        """))
        
        # 6. journeys(driver_id)
        db.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_journeys_driver_id' AND object_id = OBJECT_ID('dbo.journeys'))
            CREATE NONCLUSTERED INDEX IX_journeys_driver_id ON dbo.journeys(driver_id);
        """))
        
        # 7. journeys(vehicle_id)
        db.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_journeys_vehicle_id' AND object_id = OBJECT_ID('dbo.journeys'))
            CREATE NONCLUSTERED INDEX IX_journeys_vehicle_id ON dbo.journeys(vehicle_id);
        """))
        
        # 8. maintenance_alerts(vehicle_id)
        db.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_maintenance_alerts_vehicle_id' AND object_id = OBJECT_ID('dbo.maintenance_alerts'))
            CREATE NONCLUSTERED INDEX IX_maintenance_alerts_vehicle_id ON dbo.maintenance_alerts(vehicle_id);
        """))
        
        db.commit()
        print("All active tables have been successfully indexed on their foreign keys!")
    except Exception as e:
        print("Failed to create indexes:", e)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_remaining_indexes()
