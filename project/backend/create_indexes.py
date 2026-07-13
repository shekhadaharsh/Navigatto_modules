import os
import sys
from sqlalchemy import text

sys.path.append(os.path.dirname(__file__))
from database.db import SessionLocal

def create_indexes():
    db = SessionLocal()
    try:
        print("Creating indexes to boost maintenance query performance...")
        
        # 1. Index on brake_wear_events(vehicle_id)
        db.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_brake_wear_events_vehicle_id' AND object_id = OBJECT_ID('dbo.brake_wear_events'))
            CREATE NONCLUSTERED INDEX IX_brake_wear_events_vehicle_id ON dbo.brake_wear_events(vehicle_id);
        """))
        
        # 2. Index on tire_wear_events(vehicle_id)
        db.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_tire_wear_events_vehicle_id' AND object_id = OBJECT_ID('dbo.tire_wear_events'))
            CREATE NONCLUSTERED INDEX IX_tire_wear_events_vehicle_id ON dbo.tire_wear_events(vehicle_id);
        """))
        
        # 3. Index on engine_wear_events(vehicle_id)
        db.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_engine_wear_events_vehicle_id' AND object_id = OBJECT_ID('dbo.engine_wear_events'))
            CREATE NONCLUSTERED INDEX IX_engine_wear_events_vehicle_id ON dbo.engine_wear_events(vehicle_id);
        """))

        # 4. Index on component_wear_state(vehicle_id)
        db.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_component_wear_state_vehicle_id' AND object_id = OBJECT_ID('dbo.component_wear_state'))
            CREATE NONCLUSTERED INDEX IX_component_wear_state_vehicle_id ON dbo.component_wear_state(vehicle_id);
        """))
        
        db.commit()
        print("Successfully created indexes!")
    except Exception as e:
        print("Failed to create indexes:", e)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_indexes()
