import os
import sys
from sqlalchemy import text

sys.path.append(os.path.dirname(__file__))
from database.db import SessionLocal

def inspect_triggers():
    db = SessionLocal()
    try:
        print("Checking SQL Server triggers on raw_telemetry:")
        res = db.execute(text("""
            SELECT 
                t.name AS TriggerName,
                OBJECT_NAME(t.parent_id) AS TableName,
                m.definition AS TriggerDefinition
            FROM sys.triggers t
            INNER JOIN sys.sql_modules m ON t.object_id = m.object_id
            WHERE OBJECT_NAME(t.parent_id) = 'raw_telemetry';
        """)).fetchall()
        
        if not res:
            print("No triggers found on raw_telemetry. Checking all triggers in DB:")
            res2 = db.execute(text("""
                SELECT 
                    t.name AS TriggerName,
                    OBJECT_NAME(t.parent_id) AS TableName
                FROM sys.triggers t;
            """)).fetchall()
            for r in res2:
                print(f"  - Trigger: {r[0]} on Table: {r[1]}")
        else:
            for r in res:
                print(f"\n================ TRIGGER: {r[0]} ================")
                print(r[2])
                print("==================================================")
                
    except Exception as e:
        print("Failed to check triggers:", e)
    finally:
        db.close()

if __name__ == "__main__":
    inspect_triggers()
