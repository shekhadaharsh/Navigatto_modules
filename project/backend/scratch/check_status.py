import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import SessionLocal
from maintenance_module.model import MaintenanceAlert, ComponentWearState
from driver_module.model import Vehicle

db = SessionLocal()
try:
    print("--- VEHICLES IN DATABASE ---")
    vehicles = db.query(Vehicle).all()
    for v in vehicles:
        print(f"ID: {v.id} | Reg No: {v.reg_no} | Make: {v.make} | Model: {v.model}")

    print("\n--- WEAR STATES ---")
    wear_states = db.query(ComponentWearState).all()
    for ws in wear_states:
        print(f"Vehicle: {ws.vehicle_id} | Component: {ws.component} | Health: {ws.health_score}% | RUL: {ws.rul} km | Accumulated Wear: {ws.accumulated_wear}")

    print("\n--- OPEN ALERTS (Unacknowledged) ---")
    alerts = db.query(MaintenanceAlert).filter(MaintenanceAlert.acknowledged == False).all()
    for a in alerts:
        print(f"ID: {a.id} | Vehicle: {a.vehicle_id} | Component: {a.component} | Level: {a.alert_level} | Health: {a.health_at_alert}% | Msg: {a.message}")

    print("\n--- ACKNOWLEDGED ALERTS ---")
    ack_alerts = db.query(MaintenanceAlert).filter(MaintenanceAlert.acknowledged == True).all()
    for a in ack_alerts:
        print(f"ID: {a.id} | Vehicle: {a.vehicle_id} | Component: {a.component} | Level: {a.alert_level} | Health: {a.health_at_alert}% | Msg: {a.message}")

except Exception as e:
    print(f"Error checking DB: {e}")
finally:
    db.close()
