import os
import joblib
import numpy as np
import pandas as pd
from driver_module.scorer import calculate_trip_score, get_risk_level

# Module-level globals
_model   = None
_scaler  = None
_encoder = None
_failed_loading = False


def _load_model_assets() -> bool:
    """
    Lazy loads XGBoost model, StandardScaler, and LabelEncoder
    from the ml_model_v2 folder.
    Returns True if successfully loaded, else False (triggers rule-based fallback).
    """
    global _model, _scaler, _encoder, _failed_loading

    if _failed_loading:
        return False
    if _model is not None:
        return True

    # Reset
    _model = _scaler = _encoder = None
    _failed_loading = False

    folder_name = "ml_model_v2"
    model_dir   = os.path.join(os.path.dirname(os.path.abspath(__file__)), folder_name)

    model_path   = os.path.join(model_dir, "driver_safety_model.pkl")
    scaler_path  = os.path.join(model_dir, "scaler.pkl")
    encoder_path = os.path.join(model_dir, "encoder.pkl")

    if not (os.path.exists(model_path) and os.path.exists(scaler_path) and os.path.exists(encoder_path)):
        print(f"[WARNING] ML model binaries not found in 'ml_model_v2/'. "
              f"Falling back to Rule-Based scoring.")
        _failed_loading = True
        return False

    try:
        _model   = joblib.load(model_path)
        _scaler  = joblib.load(scaler_path)
        _encoder = joblib.load(encoder_path)
        print(f"[SUCCESS] FleetIQ ML Model V2 loaded from 'ml_model_v2/'.")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to load ML model: {e}. Falling back to Rule-Based.")
        _failed_loading = True
        return False


def calculate_trip_score_ml(
    accel_events:     int,
    brake_events:     int,
    over_speed_count: int,
    cornering_events: int,
    idle_time_min:    float,
    trip_duration_min:float,
    distance_km:      float,
    route_type:       str,
    avg_speed_kmh:    float,
    max_speed_kmh:    float,
    num_stops:        int,
    avg_engine_rpm:   float,
) -> dict:
    """
    ML-based driver safety scoring.
    Uses context-aware model with 19 features from ml_model_v2/ folder.
    Auto-falls back to Rule-Based if model files not found.
    """

    # ── Step 1: Load model assets ──
    if not _load_model_assets():
        result = calculate_trip_score(
            accel_events=accel_events,
            brake_events=brake_events,
            over_speed_count=over_speed_count,
            cornering_events=cornering_events,
            idle_time_min=idle_time_min,
            trip_duration_min=trip_duration_min,
            distance_km=distance_km
        )
        result["scoring_method"] = "Rule-Based (ML Fallback)"
        result["ml_confidence"]  = None
        return result

    # ── Step 2: Encode route_type ──
    route_type_clean = str(route_type or "Mixed").strip()
    try:
        route_encoded = _encoder.transform([route_type_clean])[0]
    except Exception:
        try:
            route_encoded = _encoder.transform(["Mixed"])[0]
        except Exception:
            route_encoded = 0

    # ── Step 3: Build feature vector ──
    dist_km   = float(distance_km or 1.0)
    dur_min   = float(trip_duration_min or 1.0)
    avg_spd   = float(avg_speed_kmh or 0.0)
    max_spd   = float(max_speed_kmh or 0.0)
    rpm       = float(avg_engine_rpm or 0.0)

    # 12 base features
    base_features = [
        float(accel_events or 0),
        float(brake_events or 0),
        float(over_speed_count or 0),
        float(cornering_events or 0),
        float(idle_time_min or 0.0),
        dist_km,
        dur_min,
        float(route_encoded),
        avg_spd,
        max_spd,
        float(num_stops or 0),
        rpm,
    ]

    # 7 derived features — only for new context-aware model (v2)
    accel_per_km  = float(accel_events or 0)    / dist_km
    brake_per_km  = float(brake_events or 0)    / dist_km
    speed_per_km  = float(over_speed_count or 0)/ dist_km
    corner_per_km = float(cornering_events or 0)/ dist_km
    idle_pct      = float(idle_time_min or 0.0) / dur_min
    speed_ratio   = avg_spd / max_spd if max_spd > 0 else 0.0
    rpm_per_speed = rpm / avg_spd      if avg_spd > 0 else 0.0

    features = base_features + [
        accel_per_km, brake_per_km, speed_per_km, corner_per_km,
        idle_pct, speed_ratio, rpm_per_speed
    ]

    # ── Step 4: Scale & Predict ──
    feature_cols = [
        "accel_events", "brake_events", "over_speed_count", "cornering_events",
        "idle_time_min", "distance_km", "trip_duration_min", "route_type",
        "avg_speed_kmh", "max_speed_kmh", "num_stops", "avg_engine_rpm",
        "accel_per_km", "brake_per_km", "speed_per_km", "corner_per_km",
        "idle_pct", "speed_ratio", "rpm_per_speed"
    ]

    features_df     = pd.DataFrame([features], columns=feature_cols)
    features_scaled = _scaler.transform(features_df)
    pred_score      = _model.predict(features_scaled)[0]
    final_score     = round(max(0.0, min(100.0, float(pred_score))), 2)

    # ── Step 5: Proximity Confidence ──
    dist       = np.linalg.norm(features_scaled[0])
    confidence = round(max(0.0, min(100.0, 100.0 * np.exp(-0.05 * dist))), 2)

    # ── Step 6: Proportional Penalty Distribution ──
    total_penalty = 100.0 - final_score

    rule_result = calculate_trip_score(
        accel_events=accel_events,
        brake_events=brake_events,
        over_speed_count=over_speed_count,
        cornering_events=cornering_events,
        idle_time_min=idle_time_min,
        trip_duration_min=trip_duration_min,
        distance_km=distance_km
    )

    rule_penalties = rule_result["penalties"]
    rp_accel     = rule_penalties["accel_penalty"]
    rp_braking   = rule_penalties["braking_penalty"]
    rp_speeding  = rule_penalties["speeding_penalty"]
    rp_cornering = rule_penalties["cornering_penalty"]
    rp_idle      = rule_penalties["idle_penalty"]

    total_weighted_rule_penalty = (
        rp_accel     * 0.20 +
        rp_braking   * 0.30 +
        rp_speeding  * 0.30 +
        rp_cornering * 0.10 +
        rp_idle      * 0.10
    )

    if total_weighted_rule_penalty > 0 and total_penalty > 0:
        ratio             = total_penalty / total_weighted_rule_penalty
        accel_penalty     = round(rp_accel     * ratio, 2)
        braking_penalty   = round(rp_braking   * ratio, 2)
        speeding_penalty  = round(rp_speeding  * ratio, 2)
        cornering_penalty = round(rp_cornering * ratio, 2)
        idle_penalty      = round(rp_idle      * ratio, 2)
    else:
        if total_penalty > 0:
            accel_penalty     = round(total_penalty * 0.20, 2)
            braking_penalty   = round(total_penalty * 0.30, 2)
            speeding_penalty  = round(total_penalty * 0.30, 2)
            cornering_penalty = round(total_penalty * 0.10, 2)
            idle_penalty      = round(total_penalty * 0.10, 2)
        else:
            accel_penalty = braking_penalty = speeding_penalty = cornering_penalty = idle_penalty = 0.0

    # ── Step 7: Component Scores ──
    accel_score     = round(max(0.0, min(100.0, 100.0 - accel_penalty)),     2)
    braking_score   = round(max(0.0, min(100.0, 100.0 - braking_penalty)),   2)
    speeding_score  = round(max(0.0, min(100.0, 100.0 - speeding_penalty)),  2)
    cornering_score = round(max(0.0, min(100.0, 100.0 - cornering_penalty)), 2)
    idle_score      = round(max(0.0, min(100.0, 100.0 - idle_penalty)),      2)

    # ── Step 8: Risk Classification ──
    risk_level = get_risk_level(final_score)

    return {
        "accel_score":      accel_score,
        "braking_score":    braking_score,
        "speeding_score":   speeding_score,
        "cornering_score":  cornering_score,
        "idle_score":       idle_score,

        "penalties": {
            "accel_penalty":    accel_penalty,
            "braking_penalty":  braking_penalty,
            "speeding_penalty": speeding_penalty,
            "cornering_penalty":cornering_penalty,
            "idle_penalty":     idle_penalty,
            "baseline":         100,
        },

        "final_score":    final_score,
        "risk_level":     risk_level,
        "scoring_method": "ML v2",
        "ml_confidence":  confidence,
    }
