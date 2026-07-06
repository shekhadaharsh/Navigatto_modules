import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import SessionLocal
from sqlalchemy import text

def test():
    print("Opening database session...")
    db = SessionLocal()
    try:
        print("Executing SELECT count(*) on system_settings...")
        res = db.execute(text("SELECT count(*) FROM system_settings WHERE setting_key = 'alert_recipient_email'")).scalar()
        print(f"SELECT completed. Result count: {res}")
        
        print("Attempting to UPDATE system_settings...")
        db.execute(
            text("UPDATE system_settings SET setting_value = 'test_check@gmail.com' WHERE setting_key = 'alert_recipient_email'")
        )
        print("UPDATE statement sent, now committing...")
        db.commit()
        print("SUCCESS: Transaction committed successfully!")
    except Exception as e:
        db.rollback()
        print(f"ERROR occurred: {e}")
    finally:
        db.close()
        print("Session closed.")

if __name__ == "__main__":
    test()
