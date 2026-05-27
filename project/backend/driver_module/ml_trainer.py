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

def run_trainer():
    print("[START] Starting FleetIQ ML Model Training...")
    
    # 1. Fetch data from DB using SessionLocal
    db = SessionLocal()
    try:
        print("[INFO] Fetching journeys from database...")
        # Query only the 12 required columns plus trip_id
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
            Trip.avg_engine_rpm
        ).all()
        
        print(f"[SUCCESS] Fetched {len(trips)} journeys from database.")
    except Exception as e:
        print(f"[ERROR] Error fetching from database: {e}")
        db.close()
        return
    finally:
        db.close()
        
    if not trips:
        print("[ERROR] No journeys found in database. Exiting.")
        return

    # Convert to pandas DataFrame
    data_list = []
    for t in trips:
        data_list.append({
            "trip_id": t[0],
            "accel_events": t[1],
            "brake_events": t[2],
            "over_speed_count": t[3],
            "cornering_events": t[4],
            "idle_time_min": t[5],
            "distance_km": t[6],
            "trip_duration_min": t[7],
            "route_type": t[8],
            "avg_speed_kmh": t[9],
            "max_speed_kmh": t[10],
            "num_stops": t[11],
            "avg_engine_rpm": t[12]
        })
        
    df = pd.DataFrame(data_list)
    
    # 2. Data Cleaning & Filtering
    print("[INFO] Cleaning data...")
    # Clean distance_km <= 0 or null
    df = df[df["distance_km"].notnull() & (df["distance_km"] > 0)]
    # Clean trip_duration_min <= 0 or null
    df = df[df["trip_duration_min"].notnull() & (df["trip_duration_min"] > 0)]
    
    print(f"[SUCCESS] {len(df)} trips remaining after primary distance and duration filtering.")
    
    if len(df) < 10:
        print("[ERROR] Insufficient valid data for training (less than 10 valid trips). Exiting.")
        return
        
    # Replace NULLs in route_type with 'Mixed'
    df["route_type"] = df["route_type"].fillna("Mixed").astype(str)
    
    # Impute remaining numeric NULLs with column median
    numeric_cols = [
        "accel_events", "brake_events", "over_speed_count", "cornering_events",
        "idle_time_min", "avg_speed_kmh", "max_speed_kmh", "num_stops", "avg_engine_rpm"
    ]
    for col in numeric_cols:
        if df[col].isnull().any():
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            
    # 3. Generate Training Labels using scorer.py's calculate_trip_score
    print("[INFO] Generating training labels using rule-based scorer...")
    scores = []
    for idx, row in df.iterrows():
        score_res = calculate_trip_score(
            accel_events=int(row["accel_events"]),
            brake_events=int(row["brake_events"]),
            over_speed_count=int(row["over_speed_count"]),
            cornering_events=int(row["cornering_events"]),
            idle_time_min=float(row["idle_time_min"]),
            trip_duration_min=float(row["trip_duration_min"]),
            distance_km=float(row["distance_km"])
        )
        scores.append(score_res["final_score"])
        
    df["label_score"] = scores
    
    # 4. Feature Preprocessing
    feature_cols = [
        "accel_events", "brake_events", "over_speed_count", "cornering_events",
        "idle_time_min", "distance_km", "trip_duration_min", "route_type",
        "avg_speed_kmh", "max_speed_kmh", "num_stops", "avg_engine_rpm"
    ]
    
    X = df[feature_cols].copy()
    y = df["label_score"]
    
    # Encoding route_type
    print("[INFO] Encoding categorical route types...")
    encoder = LabelEncoder()
    X["route_type"] = encoder.fit_transform(X["route_type"])
    
    # Standardize features
    print("[INFO] Normalizing features using StandardScaler...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 5. Train XGBoost Model (80/20 split)
    print("[INFO] Training XGBoost Regressor...")
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
    
    model = XGBRegressor(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.08,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    # 6. Evaluation
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    print(f"[INFO] Evaluation complete. Mean Absolute Error (MAE): {mae:.4f} (target: < 5.0)")
    
    # 7. Print Feature Importance
    importances = model.feature_importances_
    importance_df = pd.DataFrame({
        "Feature": feature_cols,
        "Importance": importances
    }).sort_values(by="Importance", ascending=False)
    
    print("\n[INFO] Feature Importance Breakdown:")
    for _, r in importance_df.iterrows():
        print(f"  * {r['Feature']:<20} : {r['Importance']:.4f}")
    print()
    
    # 8. Save binaries to driver_module/ml_model/
    model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml_model")
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, "driver_safety_model.pkl")
    scaler_path = os.path.join(model_dir, "scaler.pkl")
    encoder_path = os.path.join(model_dir, "encoder.pkl")
    classes_path = os.path.join(model_dir, "label_classes.json")
    
    print("[INFO] Saving model preprocessor binaries...")
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    joblib.dump(encoder, encoder_path)
    
    # Backup encoder classes as json
    with open(classes_path, "w") as f:
        json.dump(list(encoder.classes_), f)
        
    print(f"[SUCCESS] Model successfully saved to: {model_path}")
    print(f"[SUCCESS] Scaler successfully saved to: {scaler_path}")
    print(f"[SUCCESS] Encoder successfully saved to: {encoder_path}")
    print("[SUCCESS] ML Training Process Complete!\n")

if __name__ == "__main__":
    run_trainer()
