import sys
import os
from sqlalchemy import text

# Ensure backend directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import engine, DB_TYPE

def run_migration():
    print(f"Starting database migration for DB_TYPE: {DB_TYPE}")
    
    with engine.connect() as conn:
        try:
            if DB_TYPE.lower() == "sqlite":
                # Check if last_notified_at column already exists
                result = conn.execute(text("PRAGMA table_info(maintenance_alerts)")).fetchall()
                column_names = [row[1] for row in result]
                
                if "last_notified_at" not in column_names:
                    print("Adding 'last_notified_at' column to 'maintenance_alerts' (SQLite)...")
                    conn.execute(text("ALTER TABLE maintenance_alerts ADD COLUMN last_notified_at DATETIME;"))
                    conn.commit()
                    print("Column added successfully.")
                else:
                    print("'last_notified_at' column already exists in 'maintenance_alerts' (SQLite).")
            else:
                # MSSQL check and alter
                check_sql = """
                SELECT COUNT(*) 
                FROM sys.columns c
                JOIN sys.tables t ON c.object_id = t.object_id
                JOIN sys.schemas s ON t.schema_id = s.schema_id
                WHERE t.name = 'maintenance_alerts' 
                  AND s.name = 'dbo' 
                  AND c.name = 'last_notified_at';
                """
                exists = conn.execute(text(check_sql)).scalar()
                
                if not exists:
                    print("Adding 'last_notified_at' column to 'dbo.maintenance_alerts' (MSSQL)...")
                    conn.execute(text("ALTER TABLE dbo.maintenance_alerts ADD last_notified_at DATETIME NULL;"))
                    conn.commit()
                    print("Column added successfully.")
                else:
                    print("'last_notified_at' column already exists in 'dbo.maintenance_alerts' (MSSQL).")
            
            print("Migration completed successfully!")
            
        except Exception as e:
            conn.rollback()
            print(f"Migration failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    run_migration()
