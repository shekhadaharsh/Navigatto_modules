"""
db_executor.py — SQL Server query executor utilizing the application's SQLAlchemy engine.

Responsibilities:
  - Reuse the central SQLAlchemy engine from database.db
  - Execute read-only SELECT queries safely
  - Serialize result types (datetime, Decimal, UUID) to JSON-safe types
  - Return structured results for the pipeline
"""

import re
import asyncio
import decimal
import datetime
import uuid
from typing import Dict, Any, Optional

from sqlalchemy import text
from database.db import engine

# ─────────────────────────────────────────────────────────────────────────────
# Serialization helpers
# ─────────────────────────────────────────────────────────────────────────────

def _serialize_value(val: Any) -> Any:
    """Convert a DB value to a JSON-safe Python type."""
    if val is None:
        return None
    if isinstance(val, decimal.Decimal):
        return float(val)
    if isinstance(val, (datetime.datetime, datetime.date)):
        return val.isoformat()
    if isinstance(val, uuid.UUID):
        return str(val)
    if isinstance(val, bytes):
        try:
            return str(uuid.UUID(bytes_le=val))
        except Exception:
            return val.hex()
    return val


def _serialize_rows(rows) -> list:
    """Serialize all rows from a query result."""
    return [
        [_serialize_value(cell) for cell in row]
        for row in rows
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Security Guard
# ─────────────────────────────────────────────────────────────────────────────

_BLOCKED_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE",
    "ALTER", "CREATE", "EXEC", "EXECUTE", "MERGE",
    "REPLACE", "GRANT", "REVOKE", "DENY", "RENAME",
    "BACKUP", "RESTORE", "BULK INSERT", "OPENROWSET",
]


def validate_sql_safety(sql: str) -> tuple[bool, Optional[str]]:
    """
    Blocks any destructive or unauthorized SQL keyword.

    Returns:
        (True, None)          — safe to execute
        (False, "KEYWORD")    — blocked; returns the offending keyword
    """
    normalized = re.sub(r"\s+", " ", sql.strip().upper())
    for kw in _BLOCKED_KEYWORDS:
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, normalized):
            return False, kw
    return True, None


# ─────────────────────────────────────────────────────────────────────────────
# Query Execution
# ─────────────────────────────────────────────────────────────────────────────

def _execute_sync(sql: str) -> Dict[str, Any]:
    """
    Synchronous query executor (called from asyncio thread pool).

    Returns a result dict:
    {
        "success": bool,
        "columns": list[str],
        "rows": list[list],
        "row_count": int,
        "error": str | None
    }
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            
            if result.returns_rows:
                columns = list(result.keys())
                raw_rows = result.fetchall()
                rows = _serialize_rows(raw_rows)
                return {
                    "success": True,
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows),
                    "error": None,
                }
            else:
                # E.g. non-SELECT query
                return {
                    "success": True,
                    "columns": [],
                    "rows": [],
                    "row_count": result.rowcount,
                    "error": None,
                }

    except Exception as e:
        error_msg = str(e)
        print(f"[DBExecutor] SQL Error: {error_msg}")
        return {
            "success": False,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "error": error_msg,
        }


async def execute_query(sql: str) -> Dict[str, Any]:
    """
    Async wrapper — runs the blocking SQLAlchemy call in a thread pool
    so the FastAPI event loop is never blocked.
    """
    return await asyncio.to_thread(_execute_sync, sql)


# ─────────────────────────────────────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────────────────────────────────────

def test_connection() -> Dict[str, Any]:
    """
    Test the DB connection and return version info.
    Called by the /health endpoint.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT @@VERSION"))
            version = result.fetchone()[0].split("\n")[0].strip()
            db_name = engine.url.database or "unknown"
            return {"status": "ok", "version": version, "database": db_name}
    except Exception as e:
        db_name = getattr(engine.url, "database", "unknown") if engine.url else "unknown"
        return {"status": "error", "error": str(e), "database": db_name}
