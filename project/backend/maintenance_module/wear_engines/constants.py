HARSH_BRAKE_G     = -0.35
HEAVY_LOAD_RATIO  = 0.85
DOWNHILL_SLOPE    = -3.0

SLIP_RPM_RISE    = 200
SPEED_STABLE     = 5.0
HILL_SLOPE       = 3.0

HIGH_SPEED_KMH   = 80.0
HARSH_CORNER_G   = 0.4
OVERLOAD_RATIO   = 0.90
ROUGH_ROAD_RMS   = 0.15

V_NOMINAL        = 12.6
LONG_IDLE_MIN    = 30.0
DEEP_DISCHARGE_V = 11.0
COLD_CRANK_V     = 9.5

MAX_MULTIPLIER   = 5.0

# ── Base Life Defaults (Self-Healing Backup) ──────────────────
DEFAULT_BASE_LIFE = {
    "brake":   20000.0,
    "clutch":  30000.0,
    "tire":    120000.0,
    "battery": 5000.0,
    "engine":  50000.0
}


from maintenance_module.model import ComponentWearState, ComponentBaseLife
import uuid

# ── Helper: Ensure Wear State Initialized ─────────────────────
