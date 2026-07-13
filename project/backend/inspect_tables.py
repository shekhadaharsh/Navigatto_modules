import os
import sys
from sqlalchemy import text

sys.path.append(os.path.dirname(__file__))
from database.db import SessionLocal

def inspect():
    db = SessionLocal()
    try:
        # Inspect columns of dbo.journey_fuel_logs
        print("Columns in dbo.journey_fuel_logs:")
        res = db.execute(text("""
            SELECT COLUMN_NAME, DATA_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'journey_fuel_logs';
        """)).fetchall()
        for r in res:
            print(f"  - {r[0]} ({r[1]})")

        # Inspect columns of dbo.journey_fuel_logs1
        print("\nColumns in dbo.journey_fuel_logs1:")
        res1 = db.execute(text("""
            SELECT COLUMN_NAME, DATA_TYPE 
            WHERE TABLE_NAME = 'journey_fuel_logs1';
        """), execution_options={"autocommit": True}) # wait, simple query
        res1 = db.execute(text("""
            SELECT COLUMN_NAME, DATA_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'journey_fuel_logs1';
        """)).fetchall()
        for r in res1:
            print(f"  - {r[0]} ({r[1]})")

    except Exception as e:
        print("Inspection failed:", e)
    finally:
        db.close()

if __name__ == "__main__":
    inspect()
