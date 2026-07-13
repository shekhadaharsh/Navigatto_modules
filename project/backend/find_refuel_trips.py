import os
import sys
from sqlalchemy import text

# Add backend directory to sys.path so we can import modules
sys.path.append(os.path.dirname(__file__))

from database.db import SessionLocal

def find_trips():
    db = SessionLocal()
    try:
        # Check if there are any refueling events
        query = """
            SELECT DISTINCT f.trip_id, f.driver_id, d.driver_name, v.reg_no, l.id as log_id, l.refuel_amount_liters
            FROM dbo.journey_fuel_logs1 l
            JOIN dbo.fmc_raw_packets f ON l.raw_packet_id = f.id
            LEFT JOIN dbo.drivers d ON f.driver_id = d.driver_id
            LEFT JOIN dbo.vehicles v ON f.vehicle_id = v.id
            WHERE l.is_refuel = 1;
        """
        rows = db.execute(text(query)).fetchall()
        if not rows:
            print("No existing refueling stops found. Finding any available trip instead...")
            # If no refuels exist, find any trip in fmc_raw_packets
            query_any = """
                SELECT DISTINCT TOP 10 trip_id, driver_id
                FROM dbo.fmc_raw_packets
                WHERE trip_id IS NOT NULL;
            """
            any_rows = db.execute(text(query_any)).fetchall()
            for r in any_rows:
                print(f"Any Trip ID: {r[0]} | Driver ID: {r[1]}")
            return

        print("SUCCESS_FOUND_REFUELS")
        for r in rows:
            print(f"- Trip ID: {r[0]} | Driver ID: {r[1]} | Driver Name: {r[2]} | Vehicle: {r[3]} | Log ID: {r[4]} | Refuel: {r[5]} L")
    except Exception as e:
        print("Database query failed:", e)
    finally:
        db.close()

if __name__ == "__main__":
    find_trips()
