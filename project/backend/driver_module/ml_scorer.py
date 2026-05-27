import os
import joblib
import numpy as np
from driver_module.scorer import calculate_trip_score, get_risk_level

# --- Module Globals for Lazy Loading ---
_model = None
_scaler = None
_encoder = None
_failed_loading = False

def _load_model_assets() -> bool:
    """
    Lazy loads the trained XGBoost model, StandardScaler, and LabelEncoder
    from the ml_model/ directory. Returns True if successfully loaded,
    else False (triggers fallback).
    """
    global _model, _scaler, _encoder, _failed_loading
    
    if _failed_loading:
        return False
    if _model is not None:
        return True
        
    model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml_model")
    model_path = os.path.join(model_dir, "driver_safety_model.pkl")
    scaler_path = os.path.join(model_dir, "scaler.pkl")
    encoder_path = os.path.join(model_dir, "encoder.pkl")
    
    if not (os.path.exists(model_path) and os.path.exists(scaler_path) and os.path.exists(encoder_path)):
        print("[WARNING] FleetIQ ML model binaries not found. Automatically falling back to legacy Rule-Based math scoring.")
        _failed_loading = True
        return False
        
    try:
        _model = joblib.load(model_path)
        _scaler = joblib.load(scaler_path)
        _encoder = joblib.load(encoder_path)
        print("[SUCCESS] FleetIQ ML Model and Preprocessor assets loaded successfully.")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to load FleetIQ ML model binaries: {e}. Falling back to Rule-Based math scoring.")
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
    Executes the machine learning-based driver safety scoring.
    Failsafe: Auto-falls back to standard rule-based scoring if ML assets fail to load.
    """
    
    # ── Step 1: Ensure Model Assets are Loaded ──
    if not _load_model_assets():
        # FALLBACK: Execute legacy rule-based math
        result = calculate_trip_score(
            accel_events=accel_events,
            brake_events=brake_events,
            over_speed_count=over_speed_count,
            cornering_events=cornering_events,
            idle_time_min=idle_time_min,
            trip_duration_min=trip_duration_min,
            distance_km=distance_km
        )
        result["scoring_method"] = "Rule-Based"
        result["ml_confidence"] = None
        return result

    # ── Step 2: Preprocess Features ──
    route_type_clean = str(route_type or "Mixed").strip()
    
    try:
        route_encoded = _encoder.transform([route_type_clean])[0]
    except Exception:
        # Fallback to "Mixed" encoding if route_type is unseen in training
        try:
            route_encoded = _encoder.transform(["Mixed"])[0]
        except Exception:
            route_encoded = 0

    # Ensure all numerical values are float and non-null
    features = [
        float(accel_events or 0),
        float(brake_events or 0),
        float(over_speed_count or 0),
        float(cornering_events or 0),
        float(idle_time_min or 0.0),
        float(distance_km or 1.0),
        float(trip_duration_min or 1.0),
        float(route_encoded),
        float(avg_speed_kmh or 0.0),
        float(max_speed_kmh or 0.0),
        float(num_stops or 0),
        float(avg_engine_rpm or 0.0)
    ]
    
    # ── Step 3: Run Scaling & Prediction ──
    features_arr = np.array([features])
    features_scaled = _scaler.transform(features_arr)
    
    pred_score = _model.predict(features_scaled)[0]
    final_score = round(max(0.0, min(100.0, float(pred_score))), 2)

    # ── Step 4: Proximity Confidence Calculation ──
    # Computes Euclidean distance of the test sample from the standardized origin
    dist = np.linalg.norm(features_scaled[0])
    # Map distance exponentially to a percentage. If dist is 0, confidence is 100%.
    confidence = 100.0 * np.exp(-0.05 * dist)
    confidence = round(max(0.0, min(100.0, confidence)), 2)

    # ── Step 5: Proportional Penalty Distribution (correlated with actual rule-based penalties) ──
    total_penalty = 100.0 - final_score
    
    # Calculate rule-based penalties first to use as weights
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
    rp_accel = rule_penalties["accel_penalty"]
    rp_braking = rule_penalties["braking_penalty"]
    rp_speeding = rule_penalties["speeding_penalty"]
    rp_cornering = rule_penalties["cornering_penalty"]
    rp_idle = rule_penalties["idle_penalty"]
    
    # Calculate the weighted sum of rule-based penalties
    # weights: accel: 0.20, braking: 0.30, speeding: 0.30, cornering: 0.10, idle: 0.10
    total_weighted_rule_penalty = (
        rp_accel * 0.20 +
        rp_braking * 0.30 +
        rp_speeding * 0.30 +
        rp_cornering * 0.10 +
        rp_idle * 0.10
    )
    
    if total_weighted_rule_penalty > 0 and total_penalty > 0:
        # Distribute ML total penalty proportionally to rule-based penalties
        ratio = total_penalty / total_weighted_rule_penalty
        accel_penalty     = round(rp_accel * ratio, 2)
        braking_penalty   = round(rp_braking * ratio, 2)
        speeding_penalty  = round(rp_speeding * ratio, 2)
        cornering_penalty = round(rp_cornering * ratio, 2)
        idle_penalty      = round(rp_idle * ratio, 2)
    else:
        # Fallback if no rule-based penalties exist but ML predicts a penalty, or if total penalty is 0
        if total_penalty > 0:
            # Distribute based on standard Geotab weights
            accel_penalty     = round(total_penalty * 0.20, 2)
            braking_penalty   = round(total_penalty * 0.30, 2)
            speeding_penalty  = round(total_penalty * 0.30, 2)
            cornering_penalty = round(total_penalty * 0.10, 2)
            idle_penalty      = round(total_penalty * 0.10, 2)
        else:
            accel_penalty = braking_penalty = speeding_penalty = cornering_penalty = idle_penalty = 0.0

    # Invert back to calculate component scores (clamped between 0 and 100)
    accel_score     = round(max(0.0, min(100.0, 100.0 - accel_penalty)), 2)
    braking_score   = round(max(0.0, min(100.0, 100.0 - braking_penalty)), 2)
    speeding_score  = round(max(0.0, min(100.0, 100.0 - speeding_penalty)), 2)
    cornering_score = round(max(0.0, min(100.0, 100.0 - cornering_penalty)), 2)
    idle_score      = round(max(0.0, min(100.0, 100.0 - idle_penalty)), 2)

    # ── Step 6: Risk Classification ──
    risk_level = get_risk_level(final_score)

    return {
        # Component scores
        "accel_score":      accel_score,
        "braking_score":    braking_score,
        "speeding_score":   speeding_score,
        "cornering_score":  cornering_score,
        "idle_score":       idle_score,

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
        "final_score":      final_score,
        "risk_level":       risk_level,
        "scoring_method":   "ML",
        "ml_confidence":    confidence
    }
