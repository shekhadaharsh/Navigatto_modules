import os
import sys
from sqlalchemy import text

sys.path.append(os.path.dirname(__file__))
from database.db import SessionLocal

def inspect_computed_columns():
    db = SessionLocal()
    try:
        print("Checking computed columns on raw_telemetry:")
        res = db.execute(text("""
            SELECT 
                c.name AS ColumnName,
                cc.definition AS ComputedDefinition,
                cc.is_persisted AS IsPersisted
            FROM sys.computed_columns cc
            INNER JOIN sys.columns c ON cc.object_id = c.object_id AND cc.column_id = c.column_id
            WHERE OBJECT_NAME(cc.object_id) = 'raw_telemetry';
        """)).fetchall()
        
        for r in res:
            print(f"  - Column: {r[0]} | Formula: {r[1]} | Persisted: {r[2]}")
            
    except Exception as e:
        print("Failed to check computed columns:", e)
    finally:
        db.close()

if __name__ == "__main__":
    inspect_computed_columns()
