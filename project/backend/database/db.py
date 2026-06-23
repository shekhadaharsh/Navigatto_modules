"""
Database Connection - SQL Server (SSMS)
-----------------------------------------
Supports both Windows Authentication and SQL Server Authentication.
Config is loaded from .env file.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# ─────────────────────────────────────────
# Load ENV Variables
# ─────────────────────────────────────────
DB_TYPE             = os.getenv("DB_TYPE", "mssql")
DB_HOST             = os.getenv("DB_HOST", "localhost")
DB_NAME             = os.getenv("DB_NAME", "driver")
DB_TABLE            = os.getenv("DB_TABLE", "dbo.truck_telemetry_MASTER_5500")
DB_TRUSTED          = os.getenv("DB_TRUSTED_CONNECTION", "yes").lower() == "yes"
DB_USER             = os.getenv("DB_USER", "")
DB_PASSWORD         = os.getenv("DB_PASSWORD", "")


# ─────────────────────────────────────────
# Build Connection String & Engine
# ─────────────────────────────────────────
if DB_TYPE.lower() == "sqlite":
    connection_string = "sqlite:///./navigatto.db"
    engine = create_engine(
        connection_string,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    if DB_TRUSTED:
        # Windows Authentication — no username/password needed
        connection_string = (
            f"mssql+pyodbc://{DB_HOST}/{DB_NAME}"
            f"?driver=ODBC+Driver+17+for+SQL+Server"
            f"&trusted_connection=yes"
        )
    else:
        # SQL Server Authentication — username/password
        connection_string = (
            f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD}"
            f"@{DB_HOST}/{DB_NAME}"
            f"?driver=ODBC+Driver+17+for+SQL+Server"
            f"&Encrypt=yes"
            f"&TrustServerCertificate=yes"
        )
    engine = create_engine(
        connection_string,
        echo=False,          # Set True to see raw SQL queries in terminal
        fast_executemany=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# ─────────────────────────────────────────
# DB Dependency — used in routes.py
# ─────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def run_migrations():
    from sqlalchemy import text
    print(f"[Migration] Checking database schema for DB_TYPE: {DB_TYPE}")
    with engine.connect() as conn:
        try:
            # 1. Chatbot persistence tables migration
            if DB_TYPE.lower() == "sqlite":
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id VARCHAR(100) PRIMARY KEY,
                    title VARCHAR(255),
                    created_at DATETIME
                );
                """))
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id VARCHAR(100),
                    role VARCHAR(50),
                    content TEXT,
                    sql TEXT,
                    "columns" TEXT,
                    "rows" TEXT,
                    suggestions TEXT,
                    status VARCHAR(50),
                    timestamp DATETIME,
                    FOREIGN KEY(session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
                );
                """))
                conn.commit()
            else:
                conn.execute(text("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='chat_sessions' and xtype='U')
                BEGIN
                    CREATE TABLE dbo.chat_sessions (
                        session_id VARCHAR(100) PRIMARY KEY,
                        title NVARCHAR(255) NULL,
                        created_at DATETIME DEFAULT GETDATE()
                    );
                END
                """))
                conn.execute(text("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='chat_messages' and xtype='U')
                BEGIN
                    CREATE TABLE dbo.chat_messages (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        session_id VARCHAR(100) FOREIGN KEY REFERENCES dbo.chat_sessions(session_id) ON DELETE CASCADE,
                        role VARCHAR(50) NOT NULL,
                        content NVARCHAR(MAX) NOT NULL,
                        sql NVARCHAR(MAX) NULL,
                        [columns] NVARCHAR(MAX) NULL,
                        [rows] NVARCHAR(MAX) NULL,
                        suggestions NVARCHAR(MAX) NULL,
                        status VARCHAR(50) NULL,
                        timestamp DATETIME DEFAULT GETDATE()
                    );
                END
                """))
                conn.commit()
            print("[Migration] Chat sessions & messages tables checked/created.")

            if DB_TYPE.lower() == "sqlite":
                # Check if last_notified_at column already exists
                result = conn.execute(text("PRAGMA table_info(maintenance_alerts)")).fetchall()
                column_names = [row[1] for row in result]
                if "last_notified_at" not in column_names:
                    print("[Migration] Adding 'last_notified_at' column to 'maintenance_alerts' (SQLite)...")
                    conn.execute(text("ALTER TABLE maintenance_alerts ADD COLUMN last_notified_at DATETIME;"))
                    conn.commit()
                    print("[Migration] Column added successfully.")
                else:
                    print("[Migration] 'last_notified_at' column already exists.")
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
                    print("[Migration] Adding 'last_notified_at' column to 'dbo.maintenance_alerts' (MSSQL)...")
                    conn.execute(text("ALTER TABLE dbo.maintenance_alerts ADD last_notified_at DATETIME NULL;"))
                    conn.commit()
                    print("[Migration] Column added successfully.")
                else:
                    print("[Migration] 'last_notified_at' column already exists.")
        except Exception as e:
            conn.rollback()
            print(f"[Migration] Error executing migration: {e}")
            raise e