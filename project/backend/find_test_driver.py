"""
Find test driver in DB to know driver_id and vehicle_id before inserting demo trips.
Run from: project/backend/
"""
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.db import SessionLocal
from driver_module.model import Driver, Trip, Vehicle

db = SessionLocal()
try:
    print("=" * 60)
    print("ALL DRIVERS IN DB")
    print("=" * 60)
    drivers = db.query(Driver).all()
    for d in drivers:
        trips = db.query(Trip).filter(Trip.driver_id == d.driver_id).all()
        print(f"  driver_id : {d.driver_id}")
        print(f"  name      : {d.driver_name}")
        print(f"  is_active : {d.is_active}")
        print(f"  trip count: {len(trips)}")
        if trips:
            t = trips[0]
            print(f"  vehicle_id: {t.vehicle_id}")
        print("-" * 60)
    
    print("\nALL VEHICLES IN DB")
    print("=" * 60)
    vehicles = db.query(Vehicle).all()
    for v in vehicles:
        print(f"  id: {v.id}  name: {v.vehicle_name}  type: {v.vehicle_type}  active: {v.is_active}")
finally:
    db.close()
