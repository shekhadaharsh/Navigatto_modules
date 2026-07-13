import os
import sys
from sqlalchemy import text

sys.path.append(os.path.dirname(__file__))
from database.db import SessionLocal

def inspect_procedures():
    db = SessionLocal()
    try:
        print("Checking SQL Server stored procedures:")
        res = db.execute(text("""
            SELECT 
                name AS ProcedureName,
                OBJECT_DEFINITION(object_id) AS Definition
            FROM sys.procedures;
        """)).fetchall()
        
        if not res:
            print("No stored procedures found.")
        else:
            for r in res:
                print(f"\n================ PROCEDURE: {r[0]} ================")
                print(r[1])
                print("==================================================")
                
    except Exception as e:
        print("Failed to check procedures:", e)
    finally:
        db.close()

if __name__ == "__main__":
    inspect_procedures()
