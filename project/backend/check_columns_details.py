import os
import sys
from sqlalchemy import text

sys.path.append(os.path.dirname(__file__))
from database.db import SessionLocal

def inspect_columns():
    db = SessionLocal()
    try:
        print("Checking column definitions and defaults for raw_telemetry:")
        res = db.execute(text("""
            SELECT 
                c.name AS ColumnName,
                TYPE_NAME(c.user_type_id) AS DataType,
                c.is_nullable AS IsNullable,
                d.definition AS DefaultConstraint,
                cc.definition AS ComputedFormula
            FROM sys.columns c
            INNER JOIN sys.objects o ON c.object_id = o.object_id
            LEFT JOIN sys.default_constraints d ON c.default_object_id = d.object_id
            LEFT JOIN sys.computed_columns cc ON c.object_id = cc.object_id AND c.column_id = cc.column_id
            WHERE o.name = 'raw_telemetry' AND o.schema_id = SCHEMA_ID('dbo')
            ORDER BY c.column_id;
        """)).fetchall()
        
        for r in res:
            print(f"  - {r[0]} ({r[1]}): Nullable={r[2]} | Default={r[3]} | Computed={r[4]}")
            
    except Exception as e:
        print("Failed to check columns:", e)
    finally:
        db.close()

if __name__ == "__main__":
    inspect_columns()
