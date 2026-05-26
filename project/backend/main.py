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

# ─────────────────────────────────────────
# Create DB tables on startup
# ─────────────────────────────────────────
Base.metadata.create_all(bind=engine)

import os
import asyncio
from contextlib import asynccontextmanager
from sqlalchemy import text
from database.db import SessionLocal

# Load setting from environment (defaulting to 30)
REPLAY_INTERVAL = int(os.getenv("TELEMETRY_REPLAY_INTERVAL_SEC", "30"))

# ─────────────────────────────────────────
# Background Task
# ─────────────────────────────────────────
async def replay_telemetry_task():
    print(f"▶ Starting background telemetry replay task (Interval: {REPLAY_INTERVAL}s)...")
    while True:
        try:
            db = SessionLocal()
            db.execute(text("EXEC ReplayLiveTelemetry;"))
            db.commit()
            db.close()
            print(f"[{asyncio.get_running_loop().time()}] Executed ReplayLiveTelemetry")
        except Exception as e:
            print(f"Error running replay telemetry: {e}")
        await asyncio.sleep(REPLAY_INTERVAL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    task = asyncio.create_task(replay_telemetry_task())
    yield
    # Shutdown
    task.cancel()

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


# ─────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"status": "FleetIQ API is running"}