"""
Driver Safety Scorer
---------------------
Geotab-inspired rule-based scoring system.
No ML. Pure math — event count method + idle percentage method.

Formula (Geotab Event Count Method):
    component_score = 100 - (event_count x 1000) / distance_km

Weights:
    Harsh Braking    → 30%
    Speeding         → 30%
    Harsh Accel      → 20%
    Harsh Cornering  → 10%
    Idle Time        → 10%
"""

# ─────────────────────────────────────────
# WEIGHTS
# ─────────────────────────────────────────
WEIGHTS = {
    "braking":   0.30,
    "speeding":  0.30,
    "accel":     0.20,
    "cornering": 0.10,
    "idle":      0.10,
}

# ─────────────────────────────────────────
# RISK CLASSIFICATION
# ─────────────────────────────────────────
RISK_LEVELS = [
    (80, 100, "Low Risk"),
    (60,  79, "Mild Risk"),
    (40,  59, "Poor Classification"),
    (0,   39, "High Risk"),
]


# ─────────────────────────────────────────
# HELPER: Clamp score between 0 and 100
# ─────────────────────────────────────────
def _clamp(score: float) -> float:
    return max(0.0, min(100.0, score))


# ─────────────────────────────────────────
# HELPER: Event Count Method (Geotab)
# score = 100 - (event_count x 1000) / distance_km
# ─────────────────────────────────────────
def _event_count_score(event_count: int, distance_km: float) -> float:
    if distance_km <= 0:
        return 100.0  # no distance = no penalty
    score = 100 - (event_count * 1000) / distance_km
    return _clamp(score)


# ─────────────────────────────────────────
# HELPER: Idle Percentage Method
# idle_pct = idle_time_min / trip_duration_min
# score = 100 - (idle_pct x 100)
# ─────────────────────────────────────────
def _idle_score(idle_time_min: float, trip_duration_min: float) -> float:
    if trip_duration_min <= 0:
        return 100.0
    idle_pct = idle_time_min / trip_duration_min
    score = 100 - (idle_pct * 100)
    return _clamp(score)


# ─────────────────────────────────────────
# HELPER: Get Risk Level from final score
# ─────────────────────────────────────────
def get_risk_level(score: float) -> str:
    for low, high, label in RISK_LEVELS:
        if low <= score <= high:
            return label
    return "High Risk"


# ─────────────────────────────────────────
# MAIN SCORER FUNCTION
# Input  → raw trip data (7 columns)
# Output → full score breakdown dict
# ─────────────────────────────────────────
def calculate_trip_score(
    accel_events:     int,
    brake_events:     int,
    over_speed_count: int,
    cornering_events: int,
    idle_time_min:    float,
    trip_duration_min:float,
    distance_km:      float,
) -> dict:

    # ── Step 1: Calculate each component score ──
    accel_score     = _event_count_score(accel_events,     distance_km)
    braking_score   = _event_count_score(brake_events,     distance_km)
    speeding_score  = _event_count_score(over_speed_count, distance_km)
    cornering_score = _event_count_score(cornering_events, distance_km)
    idle_score      = _idle_score(idle_time_min, trip_duration_min)

    # ── Step 2: Calculate penalty points (deducted from 100) ──
    accel_penalty     = round(100 - accel_score,     2)
    braking_penalty   = round(100 - braking_score,   2)
    speeding_penalty  = round(100 - speeding_score,  2)
    cornering_penalty = round(100 - cornering_score, 2)
    idle_penalty      = round(100 - idle_score,      2)

    # ── Step 3: Weighted final score ──
    final_score = (
        braking_score   * WEIGHTS["braking"]   +
        speeding_score  * WEIGHTS["speeding"]  +
        accel_score     * WEIGHTS["accel"]     +
        cornering_score * WEIGHTS["cornering"] +
        idle_score      * WEIGHTS["idle"]
    )
    final_score = round(_clamp(final_score), 2)

    # ── Step 4: Risk classification ──
    risk_level = get_risk_level(final_score)

    return {
        # Component scores
        "accel_score":      round(accel_score,     2),
        "braking_score":    round(braking_score,   2),
        "speeding_score":   round(speeding_score,  2),
        "cornering_score":  round(cornering_score, 2),
        "idle_score":       round(idle_score,      2),

        # Penalty points
        "penalties": {
            "accel_penalty":    accel_penalty,
            "braking_penalty":  braking_penalty,
            "speeding_penalty": speeding_penalty,
            "cornering_penalty":cornering_penalty,
            "idle_penalty":     idle_penalty,
            "baseline":         100,
        },

        # Final result
        "final_score": final_score,
        "risk_level":  risk_level,
    }