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
# from fuel_module.routes import router as fuel_router          # Person 2
# from maintenance_module.routes import router as maint_router  # Person 3

# ─────────────────────────────────────────
# Create DB tables on startup
# ─────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ─────────────────────────────────────────
# App Init
# ─────────────────────────────────────────
app = FastAPI(
    title="FleetIQ API",
    description="Unified Fleet Intelligence Backend",
    version="1.0.0",
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
# app.include_router(fuel_router)       # uncomment when Person 2 is ready
# app.include_router(maint_router)      # uncomment when Person 3 is ready


# ─────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"status": "FleetIQ API is running"}