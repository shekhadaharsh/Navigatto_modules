import os
import sys
from sqlalchemy import text

sys.path.append(os.path.dirname(__file__))
from database.db import SessionLocal

def check_fleet_stats():
    db = SessionLocal()
    try:
        # Fleet Size
        fleet_size = db.execute(text("SELECT COUNT(*) FROM dbo.vehicles")).scalar()
        
        # Warning Components (health_score between 10 and 30)
        warning_components = db.execute(text("""
            SELECT COUNT(*) 
            FROM dbo.component_wear_state 
            WHERE health_score >= 10.0 AND health_score <= 30.0
        """)).scalar()
        
        # Critical Components (health_score < 10)
        critical_components = db.execute(text("""
            SELECT COUNT(*) 
            FROM dbo.component_wear_state 
            WHERE health_score < 10.0
        """)).scalar()
        
        # Open alerts (acknowledged = 0)
        open_alerts = db.execute(text("""
            SELECT COUNT(*) 
            FROM dbo.maintenance_alerts 
            WHERE acknowledged = 0
        """)).scalar()
        
        print("DATABASE COUNTS:")
        print(f"  - Fleet Size: {fleet_size}")
        print(f"  - Warning Components: {warning_components}")
        print(f"  - Critical Components: {critical_components}")
        print(f"  - Open Database Alerts: {open_alerts}")
        
    except Exception as e:
        print("Verification failed:", e)
    finally:
        db.close()

if __name__ == "__main__":
    check_fleet_stats()
