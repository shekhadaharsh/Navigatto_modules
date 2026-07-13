import os
import sys
from sqlalchemy import text

sys.path.append(os.path.dirname(__file__))
from database.db import SessionLocal

def check_wear_rows():
    db = SessionLocal()
    try:
        brakes = db.execute(text("SELECT COUNT(*) FROM dbo.brake_wear_events")).scalar()
        tires = db.execute(text("SELECT COUNT(*) FROM dbo.tire_wear_events")).scalar()
        engine = db.execute(text("SELECT COUNT(*) FROM dbo.engine_wear_events")).scalar()
        
        print(f"Brake Wear Events Row Count: {brakes}")
        print(f"Tire Wear Events Row Count: {tires}")
        print(f"Engine Wear Events Row Count: {engine}")
    except Exception as e:
        print("Error:", e)
    finally:
        db.close()

if __name__ == "__main__":
    check_wear_rows()
