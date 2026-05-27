"""
FleetIQ -- Context-Aware ML Trainer (Model v2)
-----------------------------------------------
Trains a new XGBoost model with context-aware labels.
Output saved to: driver_module/ml_model_v2/

HOW TO RUN:
    python driver_module/ml_trainer.py
    (Run from: project/backend/)

WHAT'S NEW vs old trainer:
    - Label = Rule-Based score adjusted with route/speed/RPM/stop context
    - 7 derived ratio features added (19 total, was 12)
    - Model saved to ml_model_v2/ -- old ml_model/ untouched
    - Verification test: City vs Highway, same events -> different ML scores
"""

import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import SessionLocal
from driver_module.model import Trip
from driver_module.scorer import calculate_trip_score


# -----------------------------------------
# CONTEXT MULTIPLIER MAP
# -----------------------------------------
ROUTE_MULTIPLIER = {
    "highway":  1.20,
    "city":     0.85,
    "mountain": 1.30,
    "rural":    1.00,
    "mixed":    1.10,
}


def _clamp(val, lo=0.0, hi=100.0):
    return max(lo, min(hi, val))


def _generate_context_label(row):
    """
    Generates a context-aware adjusted score for one trip row.

    Step 1: Rule-Based base score via scorer.py
    Step 2: Route type multiplier
    Step 3: Speed penalty (max_speed + avg_speed)
    Step 4: RPM penalty
    Step 5: Suspicious stop penalty (highway with many stops)
    Step 6: Final adjusted label = clamp(100 - adjusted_penalty, 0, 100)
    """

    # Step 1: Base Score
    result = calculate_trip_score(
        accel_events=int(row["accel_events"]),
        brake_events=int(row["brake_events"]),
        over_speed_count=int(row["over_speed_count"]),
        cornering_events=int(row["cornering_events"]),
        idle_time_min=float(row["idle_time_min"]),
        trip_duration_min=float(row["trip_duration_min"]),
        distance_km=float(row["distance_km"]),
    )
    base_score   = result["final_score"]
    base_penalty = 100.0 - base_score

    # Step 2: Route Type Multiplier
    route_key  = str(row["route_type"]).strip().lower()
    multiplier = ROUTE_MULTIPLIER.get(route_key, 1.00)

    # Step 3: Speed Adjustments
    max_spd = float(row["max_speed_kmh"])
    avg_spd = float(row["avg_speed_kmh"])

    if max_spd > 140:
        speed_penalty = 10.0
    elif max_spd > 120:
        speed_penalty = 5.0
    else:
        speed_penalty = 0.0

    if avg_spd > 100:
        multiplier += 0.20
    elif avg_spd > 80:
        multiplier += 0.10

    # Step 4: RPM Penalty
    rpm = float(row["avg_engine_rpm"])
    if rpm > 4000:
        rpm_penalty = 5.0
    elif rpm > 3000:
        rpm_penalty = 2.0
    else:
        rpm_penalty = 0.0

    # Step 5: Suspicious Stops Penalty
    if route_key == "highway" and int(row["num_stops"]) > 10:
        stop_penalty = 3.0
    else:
        stop_penalty = 0.0

    # Step 6: Final Adjusted Label
    adjusted_score = 100.0 - (base_penalty * multiplier) - speed_penalty - rpm_penalty - stop_penalty
    return round(_clamp(adjusted_score), 2)


def _add_derived_features(df):
    """
    Adds 7 derived ratio features to the DataFrame.
    These help ML understand patterns that raw counts cannot express.
    """
    dist_km = df["distance_km"].replace(0, np.nan)
    dur_min = df["trip_duration_min"].replace(0, np.nan)
    avg_spd = df["avg_speed_kmh"].replace(0, np.nan)
    max_spd = df["max_speed_kmh"].replace(0, np.nan)

    df["accel_per_km"]  = (df["accel_events"]      / dist_km).fillna(0.0)
    df["brake_per_km"]  = (df["brake_events"]       / dist_km).fillna(0.0)
    df["speed_per_km"]  = (df["over_speed_count"]   / dist_km).fillna(0.0)
    df["corner_per_km"] = (df["cornering_events"]   / dist_km).fillna(0.0)
    df["idle_pct"]      = (df["idle_time_min"]      / dur_min).fillna(0.0)
    df["speed_ratio"]   = (df["avg_speed_kmh"]      / max_spd).fillna(0.0)
    df["rpm_per_speed"] = (df["avg_engine_rpm"]     / avg_spd).fillna(0.0)

    return df


# -----------------------------------------
# VERIFICATION TEST
# Same events -- City vs Highway
# ML must give clearly different scores
# -----------------------------------------
def _run_verification_test(model, scaler, encoder):
    print("")
    print("=" * 58)
    print("  VERIFICATION TEST -- City vs Highway (Same Events)")
    print("=" * 58)

    common = dict(
        accel_events=3, brake_events=5, over_speed_count=0,
        cornering_events=2, idle_time_min=10.0,
        distance_km=42.0, trip_duration_min=95.0,
    )

    trip_a = {**common, "route_type": "City",    "avg_speed_kmh": 28.0,
              "max_speed_kmh": 45.0,  "num_stops": 18, "avg_engine_rpm": 1400.0}
    trip_b = {**common, "route_type": "Highway", "avg_speed_kmh": 90.0,
              "max_speed_kmh": 115.0, "num_stops": 2,  "avg_engine_rpm": 2800.0}

    # Rule-Based score (context blind -- both same)
    rule_score = calculate_trip_score(
        accel_events=common["accel_events"],
        brake_events=common["brake_events"],
        over_speed_count=common["over_speed_count"],
        cornering_events=common["cornering_events"],
        idle_time_min=common["idle_time_min"],
        trip_duration_min=common["trip_duration_min"],
        distance_km=common["distance_km"],
    )["final_score"]

    def _predict_trip(trip):
        dist_km = trip["distance_km"]
        dur_min = trip["trip_duration_min"]
        avg_spd = trip["avg_speed_kmh"]
        max_spd = trip["max_speed_kmh"]
        rpm     = trip["avg_engine_rpm"]

        route_clean = str(trip["route_type"]).strip()
        try:
            route_enc = encoder.transform([route_clean])[0]
        except Exception:
            route_enc = encoder.transform(["Mixed"])[0]

        base = [
            float(trip["accel_events"]),
            float(trip["brake_events"]),
            float(trip["over_speed_count"]),
            float(trip["cornering_events"]),
            float(trip["idle_time_min"]),
            dist_km, dur_min,
            float(route_enc),
            avg_spd, max_spd,
            float(trip["num_stops"]),
            rpm,
        ]
        derived = [
            trip["accel_events"]      / dist_km,
            trip["brake_events"]      / dist_km,
            trip["over_speed_count"]  / dist_km,
            trip["cornering_events"]  / dist_km,
            trip["idle_time_min"]     / dur_min,
            avg_spd / max_spd         if max_spd > 0 else 0.0,
            rpm     / avg_spd         if avg_spd > 0 else 0.0,
        ]
        features = np.array([base + derived])
        scaled   = scaler.transform(features)
        pred     = model.predict(scaled)[0]
        return round(float(_clamp(pred)), 2)

    score_city    = _predict_trip(trip_a)
    score_highway = _predict_trip(trip_b)
    diff          = round(score_city - score_highway, 2)
    status        = "PASS" if score_city > score_highway else "FAIL"

    print("  Rule-Based Score (both trips)   : %.2f" % rule_score)
    print("  ML Score -- Trip A (City)       : %.2f" % score_city)
    print("  ML Score -- Trip B (Highway)    : %.2f" % score_highway)
    print("  Difference (City - Highway)     : %.2f pts" % diff)
    print("  Status                          : %s" % status)
    print("=" * 58)
    print("")

    if score_city <= score_highway:
        print("[WARNING] Verification FAILED -- check label generation or training data.")


# -----------------------------------------
# MAIN TRAINER
# -----------------------------------------
def run_trainer():
    print("=" * 58)
    print("  FleetIQ ML Trainer -- Context-Aware Model v2")
    print("  Output -> driver_module/ml_model_v2/")
    print("=" * 58)

    # Step 1: Fetch from DB
    db = SessionLocal()
    try:
        print("\n[Step 1] Fetching trips from database...")
        trips = db.query(
            Trip.trip_id,
            Trip.accel_events,
            Trip.brake_events,
            Trip.over_speed_count,
            Trip.cornering_events,
            Trip.idle_time_min,
            Trip.distance_km,
            Trip.trip_duration_min,
            Trip.route_type,
            Trip.avg_speed_kmh,
            Trip.max_speed_kmh,
            Trip.num_stops,
            Trip.avg_engine_rpm,
        ).all()
        print("         Fetched %d raw trips from DB." % len(trips))
    except Exception as e:
        print("[ERROR] DB fetch failed: %s" % e)
        db.close()
        return
    finally:
        db.close()

    if not trips:
        print("[ERROR] No trips found. Exiting.")
        return

    # Step 2: Build DataFrame & Clean
    print("\n[Step 2] Cleaning data...")
    data_list = [
        {
            "trip_id":           t[0],
            "accel_events":      t[1],
            "brake_events":      t[2],
            "over_speed_count":  t[3],
            "cornering_events":  t[4],
            "idle_time_min":     t[5],
            "distance_km":       t[6],
            "trip_duration_min": t[7],
            "route_type":        t[8],
            "avg_speed_kmh":     t[9],
            "max_speed_kmh":     t[10],
            "num_stops":         t[11],
            "avg_engine_rpm":    t[12],
        }
        for t in trips
    ]
    df = pd.DataFrame(data_list)

    df = df[df["distance_km"].notnull()      & (df["distance_km"] > 0)]
    df = df[df["trip_duration_min"].notnull() & (df["trip_duration_min"] > 0)]
    print("         %d trips after distance/duration filter." % len(df))

    if len(df) < 10:
        print("[ERROR] Less than 10 valid trips -- insufficient for training. Exiting.")
        return

    df["route_type"] = df["route_type"].fillna("Mixed").astype(str)

    numeric_cols = [
        "accel_events", "brake_events", "over_speed_count", "cornering_events",
        "idle_time_min", "avg_speed_kmh", "max_speed_kmh", "num_stops", "avg_engine_rpm"
    ]
    for col in numeric_cols:
        if df[col].isnull().any():
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            print("         Imputed NULLs in '%s' with median=%.2f" % (col, median_val))

    # Step 3: Context-Aware Label Generation
    print("\n[Step 3] Generating context-aware training labels...")
    df["label_score"] = df.apply(_generate_context_label, axis=1)

    print("         Label distribution:")
    print("           Min  = %.2f" % df["label_score"].min())
    print("           Max  = %.2f" % df["label_score"].max())
    print("           Mean = %.2f" % df["label_score"].mean())
    print("           Std  = %.2f" % df["label_score"].std())

    # Step 3.5: Add Derived Features
    print("\n[Step 3.5] Adding 7 derived ratio features (12 -> 19 total)...")
    df = _add_derived_features(df)

    # Step 4: Encode route_type
    print("\n[Step 4] Encoding categorical feature: route_type...")
    encoder = LabelEncoder()
    df["route_type"] = encoder.fit_transform(df["route_type"])
    print("         Classes: %s" % list(encoder.classes_))

    # Step 5: Features & Scale
    feature_cols = [
        # 12 original
        "accel_events", "brake_events", "over_speed_count", "cornering_events",
        "idle_time_min", "distance_km", "trip_duration_min", "route_type",
        "avg_speed_kmh", "max_speed_kmh", "num_stops", "avg_engine_rpm",
        # 7 derived
        "accel_per_km", "brake_per_km", "speed_per_km", "corner_per_km",
        "idle_pct", "speed_ratio", "rpm_per_speed",
    ]

    X = df[feature_cols].copy()
    y = df["label_score"]

    print("\n[Step 5] Normalizing 19 features with StandardScaler...")
    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Step 6: Train XGBoost
    print("\n[Step 6] Training XGBoost Regressor (80/20 split)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42
    )
    print("         Train samples: %d | Test samples: %d" % (len(X_train), len(X_test)))

    model = XGBRegressor(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # Step 7: Evaluate
    print("\n[Step 7] Evaluating model...")
    predictions = model.predict(X_test)
    mae         = mean_absolute_error(y_test, predictions)
    status      = "PASS (< 5.0)" if mae < 5.0 else "REVIEW (>= 5.0)"
    print("         MAE = %.4f   [%s]" % (mae, status))

    # Feature Importance
    importances   = model.feature_importances_
    importance_df = pd.DataFrame({
        "Feature":    feature_cols,
        "Importance": importances,
    }).sort_values("Importance", ascending=False)

    print("\n[INFO] Top 10 Feature Importances:")
    for i, (_, row) in enumerate(importance_df.head(10).iterrows()):
        print("  %2d. %-22s : %.4f" % (i + 1, row["Feature"], row["Importance"]))

    # Step 8: Save to ml_model_v2/
    model_dir    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml_model_v2")
    os.makedirs(model_dir, exist_ok=True)

    model_path   = os.path.join(model_dir, "driver_safety_model.pkl")
    scaler_path  = os.path.join(model_dir, "scaler.pkl")
    encoder_path = os.path.join(model_dir, "encoder.pkl")
    classes_path = os.path.join(model_dir, "label_classes.json")

    print("\n[Step 8] Saving model artifacts to: %s" % model_dir)
    joblib.dump(model,   model_path)
    joblib.dump(scaler,  scaler_path)
    joblib.dump(encoder, encoder_path)
    with open(classes_path, "w") as f:
        json.dump(list(encoder.classes_), f)

    print("         [OK] driver_safety_model.pkl saved")
    print("         [OK] scaler.pkl saved")
    print("         [OK] encoder.pkl saved")
    print("         [OK] label_classes.json saved")
    print("\n[NOTE] Old model in ml_model/ is UNTOUCHED.")
    print("[NOTE] Set USE_ML_MODEL=2 in .env to activate this new model.")

    # Step 9: Verification Test
    _run_verification_test(model, scaler, encoder)

    print("=" * 58)
    print("  Training Complete! FleetIQ ML Model v2 is ready.")
    print("=" * 58)
    print("")


if __name__ == "__main__":
    run_trainer()
