"""
Database Connection - SQL Server (SSMS)
-----------------------------------------
Supports both Windows Authentication and SQL Server Authentication.
Config is loaded from .env file.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
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
# Build Connection String
# ─────────────────────────────────────────
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
    )


# ─────────────────────────────────────────
# SQLAlchemy Engine & Session
# ─────────────────────────────────────────
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