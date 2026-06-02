"""
Fuel Module — ML Predictor
───────────────────────────
Loads xgboost_fuel_prediction_model.pkl and predicts expected fuel (L)
from a trip's journey features.

Feature order the model was trained on (12 features):
  distance_km, route_type, load_pct, vehicle_type,
  engine_total_hour, Total_Odometer, temp_celsius,
  avg_engine_rpm, avg_engine_load_pct, avg_fuel_rate_Lhr,
  avg_speed_kmh, idle_time_min
"""


import os
import joblib
import pandas as pd

# ── NEW: Env flag to toggle ML vs DB fuel source ──
USE_ML_FUEL_PREDICTION = os.getenv("USE_ML_FUEL_PREDICTION", "true").lower() == "true"

# ── Label encoding maps (must match what the notebook used) ──
ROUTE_TYPE_MAP = {
    "City":     0,
    "Highway":  1,
    "Mixed":    2,
    "Mountain": 3,
    "Rural":    4,
}

VEHICLE_TYPE_MAP = {
    "Heavy Cargo Truck":   0,
    "Medium Cargo Truck":  1,   
    "Mini Truck":          2,
    "Pickup Truck":        3,
}

# ── Load model once at import time ──
_MODEL = None

def _load_model():
    global _MODEL
    if _MODEL is None:
        model_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "xgboost_fuel_prediction_model.pkl"
        )
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Fuel prediction model not found at: {model_path}"
            )
        _MODEL = joblib.load(model_path)
    return _MODEL


def predict_expected_fuel(
    distance_km: float,
    route_type: str,
    load_pct: float,
    vehicle_type: str,
    engine_total_hour: float,
    total_odometer: float,
    temp_celsius: float,
    avg_engine_rpm: float,
    avg_engine_load_pct: float,
    avg_fuel_rate_lhr: float,
    avg_speed_kmh: float,
    idle_time_min: float,
) -> float:
    """
    Returns predicted expected fuel in litres (rounded to 2 dp).
    Falls back to None if model cannot be loaded.
    """
    try:
        model = _load_model()

        route_encoded   = ROUTE_TYPE_MAP.get(str(route_type).strip(), 2)    # default Mixed
        vehicle_encoded = VEHICLE_TYPE_MAP.get(str(vehicle_type).strip(), 0) # default Heavy

        features = pd.DataFrame([{
            "distance_km":        float(distance_km   or 0.0),
            "route_type":         route_encoded,
            "load_pct":           float(load_pct       or 0.0),
            "vehicle_type":       vehicle_encoded,
            "engine_total_hour":  float(engine_total_hour or 0.0),
            "Total_Odometer":     float(total_odometer or 0.0),
            "temp_celsius":       float(temp_celsius   or 25.0),
            "avg_engine_rpm":     float(avg_engine_rpm or 0.0),
            "avg_engine_load_pct":float(avg_engine_load_pct or 0.0),
            "avg_fuel_rate_Lhr":  float(avg_fuel_rate_lhr  or 0.0),
            "avg_speed_kmh":      float(avg_speed_kmh  or 0.0),
            "idle_time_min":      float(idle_time_min  or 0.0),
        }])

        prediction = model.predict(features)[0]
        return round(float(prediction), 2)

    except Exception as e:
        print(f"[FuelPredictor] Prediction failed: {e}")
        return None