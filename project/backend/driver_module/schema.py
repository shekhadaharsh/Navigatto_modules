from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ─────────────────────────────────────────
# PENALTY BREAKDOWN
# Shows how many points deducted per component
# Used in: TripScoreResponse
# ─────────────────────────────────────────
class PenaltyBreakdown(BaseModel):
    accel_penalty:    float   # points deducted for harsh acceleration
    braking_penalty:  float   # points deducted for harsh braking
    speeding_penalty: float   # points deducted for overspeeding
    cornering_penalty:float   # points deducted for harsh cornering
    idle_penalty:     float   # points deducted for excessive idling
    baseline:         int = 100


# ─────────────────────────────────────────
# TRIP SCORE RESPONSE
# Score result for a single trip
# Used in: GET /drivers/{driver_id}/trips/{trip_id}/score
# ─────────────────────────────────────────
class TripScoreResponse(BaseModel):
    trip_id:          str
    driver_id:        str
    route_type:       str
    distance_km:      float
    trip_duration_min:float

    # Raw event counts
    accel_events:     int
    brake_events:     int
    over_speed_count: int
    cornering_events: int
    idle_time_min:    float

    # Component scores (0-100 each)
    accel_score:      float
    braking_score:    float
    speeding_score:   float
    cornering_score:  float
    idle_score:       float

    # Final result
    penalties:        PenaltyBreakdown
    final_score:      float
    risk_level:       str   # Low Risk / Mild Risk / Poor Classification / High Risk


# ─────────────────────────────────────────
# TRIP SUMMARY
# Lightweight trip info for journey history list
# Used in: GET /drivers/{driver_id}/trips
# ─────────────────────────────────────────
class TripSummary(BaseModel):
    trip_id:          str
    route_type:       str
    trip_start:       Optional[datetime]
    trip_end:         Optional[datetime]
    distance_km:      float
    trip_duration_min:float
    final_score:      float
    risk_level:       str

    class Config:
        from_attributes = True


# ─────────────────────────────────────────
# DRIVER SUMMARY
# Single driver card info (left sidebar)
# Used in: GET /drivers/ and GET /drivers/{driver_id}
# ─────────────────────────────────────────
class DriverSummary(BaseModel):
    driver_id:      str
    total_trips:    int
    avg_score:      float
    risk_level:     str
    total_distance: float   # total km driven


# ─────────────────────────────────────────
# DRIVER DETAIL
# Full driver profile with stats breakdown
# Used in: GET /drivers/{driver_id}
# ─────────────────────────────────────────
class DriverDetail(BaseModel):
    driver_id:        str
    total_trips:      int
    avg_score:        float
    risk_level:       str
    total_distance:   float

    # Avg event counts across all trips
    avg_accel_events:    float
    avg_brake_events:    float
    avg_over_speed:      float
    avg_cornering_events:float
    avg_idle_time:       float

    # Component avg scores
    avg_accel_score:     float
    avg_braking_score:   float
    avg_speeding_score:  float
    avg_cornering_score: float
    avg_idle_score:      float


# ─────────────────────────────────────────
# LEADERBOARD ITEM
# Used in: GET /drivers/leaderboard
# ─────────────────────────────────────────
class LeaderboardItem(BaseModel):
    rank:        int
    driver_id:   str
    avg_score:   float
    risk_level:  str
    total_trips: int


# ─────────────────────────────────────────
# LEADERBOARD RESPONSE
# Top and bottom performers
# Used in: GET /drivers/leaderboard
# ─────────────────────────────────────────
class LeaderboardResponse(BaseModel):
    top_performers:    list[LeaderboardItem]
    bottom_performers: list[LeaderboardItem]