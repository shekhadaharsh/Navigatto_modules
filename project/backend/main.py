# Main FastAPI entry
"""
FleetIQ Backend - Main Entry Point
------------------------------------
FastAPI application with all module routers included.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.db import Base, engine

# ── Import Routers ──
from driver_module.routes import router as driver_router
from fuel_module.routes import router as fuel_router
from maintenance_module.routes import router as maint_router
from simulation_module.routes import router as sim_router
# from chatbot_module.routes import router as chatbot_router

# ─────────────────────────────────────────
# Create DB tables on startup
# ─────────────────────────────────────────
from database.db import DB_TYPE

if DB_TYPE.lower() == "sqlite":
    for table_name, table in Base.metadata.tables.items():
        table.schema = None

# Base.metadata.create_all(bind=engine)

import os
import asyncio
from contextlib import asynccontextmanager
from sqlalchemy import text
from database.db import SessionLocal, DB_TYPE
from fastapi import APIRouter

# Load settings from environment
REPLAY_INTERVAL = int(os.getenv("TELEMETRY_REPLAY_INTERVAL_SEC", "30"))
ENABLE_MANUAL_REPLAY_CONTROL = os.getenv("ENABLE_MANUAL_REPLAY_CONTROL", "false").lower() == "true"

RESET_TIME = "2024-03-15 05:59:30"

# ─────────────────────────────────────────
# Singleton Replay Manager
# ─────────────────────────────────────────
class ReplayManager:
    def __init__(self):
        self._task = None
        self._running = False
        self._lock = asyncio.Lock()

    @property
    def is_running(self):
        return self._running and self._task is not None and not self._task.done()

    def _ensure_null_safe(self, db):
        if DB_TYPE.lower() == "sqlite":
            return
        result = db.execute(text("SELECT last_historical_time FROM dbo.replay_tracker WHERE id = 1")).fetchone()
        if result is None or result[0] is None:
            db.execute(text(f"UPDATE dbo.replay_tracker SET last_historical_time = '{RESET_TIME}' WHERE id = 1"))
            db.commit()
            print("[ReplayManager] NULL detected — reset last_historical_time to default")

    async def _loop(self):
        print(f"▶ Replay loop started (Interval: {REPLAY_INTERVAL}s)...")
        self._running = True
        while self._running:
            try:
                if DB_TYPE.lower() == "sqlite":
                    print("[ReplayManager] Skiping ReplayLiveTelemetry on SQLite")
                else:
                    db = SessionLocal()
                    self._ensure_null_safe(db)
                    db.execute(text("EXEC ReplayLiveTelemetry;"))
                    db.commit()
                    db.close()
                    print(f"[ReplayManager] Executed ReplayLiveTelemetry")
            except Exception as e:
                print(f"[ReplayManager] Error: {e}")
            await asyncio.sleep(REPLAY_INTERVAL)

    async def start(self):
        async with self._lock:
            if self.is_running:
                return {"status": "already_running"}
            self._task = asyncio.create_task(self._loop())
            return {"status": "started"}

    async def stop(self):
        async with self._lock:
            self._running = False
            if self._task:
                self._task.cancel()
                self._task = None
            return {"status": "stopped"}

    async def fresh_start(self):
        await self.stop()
        try:
            if DB_TYPE.lower() != "sqlite":
                db = SessionLocal()

                # Step 1: delete child table FIRST (FK constraint)
                db.execute(text("DELETE FROM dbo.journey_fuel_logs1;"))
                db.commit()

                # Step 2: now safe to delete parent table
                db.execute(text("DELETE FROM dbo.fmc_raw_packets;"))
                db.commit()

                # Step 3: reset tracker
                db.execute(text(f"UPDATE dbo.replay_tracker SET last_historical_time = '{RESET_TIME}' WHERE id = 1;"))
                db.commit()

                db.close()
                print("[ReplayManager] Fresh start — tables cleared, tracker reset")
            else:
                print("[ReplayManager] Fresh start skipped for SQLite")

        except Exception as e:
            print(f"[ReplayManager] Fresh start DB error: {e}")
            # ── KEY FIX: reset running state so button never gets stuck ──
            self._running = False
            self._task = None
            return {"status": "error", "detail": str(e)}

        return await self.start()

replay_manager = ReplayManager()

# ─────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run database schema migrations
    try:
        from database.db import run_migrations
        run_migrations()
    except Exception as e:
        print(f"[Lifespan] Database migration failed: {e}")

    # Pre-load chatbot schema and embedding models on startup
    # try:
    #     from chatbot_module.schema_service import load_schema
    #     load_schema()
    # except Exception as e:
    #     print(f"[Lifespan] Error pre-loading schema & models: {e}")

    # Start background reminder scheduler for critical vehicle alerts
    reminder_task = None
    try:
        from maintenance_module.reminder_service import start_reminder_scheduler
        reminder_task = asyncio.create_task(start_reminder_scheduler())
    except Exception as e:
        print(f"[Lifespan] Failed to start reminder scheduler: {e}")

    if not ENABLE_MANUAL_REPLAY_CONTROL:
        await replay_manager.start()
    else:
        print("[ReplayManager] Manual control mode — waiting for UI trigger")
    yield
    if reminder_task:
        reminder_task.cancel()
    await replay_manager.stop()

# ─────────────────────────────────────────
# App Init
# ─────────────────────────────────────────
app = FastAPI(
    title="FleetIQ API",
    description="Unified Fleet Intelligence Backend",
    version="1.0.0",
    lifespan=lifespan
)

# ─────────────────────────────────────────
# CORS — allow React frontend to connect
# ─────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server (React)
        "http://localhost:3000",  # fallback CRA
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────
# Include Routers
# ─────────────────────────────────────────
app.include_router(driver_router)
app.include_router(fuel_router)
app.include_router(maint_router)
app.include_router(sim_router)
# app.include_router(chatbot_router)



# ─────────────────────────────────────────
# Replay Control Endpoints
# ─────────────────────────────────────────
@app.post("/replay/start", tags=["Replay"])
async def replay_start():
    return await replay_manager.start()

@app.post("/replay/fresh-start", tags=["Replay"])
async def replay_fresh_start():
    return await replay_manager.fresh_start()

@app.get("/replay/status", tags=["Replay"])
async def replay_status():
    return {"running": replay_manager.is_running, "manual_control": ENABLE_MANUAL_REPLAY_CONTROL}

@app.post("/replay/stop", tags=["Replay"])
async def replay_stop():
    return await replay_manager.stop()

# ─────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"status": "FleetIQ API is running"}