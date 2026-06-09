import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
import joblib
import os

def train():
    print("Starting Brake AI Model Training...")
    
    # Path to the CSV file
    csv_path = os.path.join(os.path.dirname(__file__), 'brake_synthetic_training_data.csv')
    
    if not os.path.exists(csv_path):
        print(f"Error: Could not find {csv_path}.")
        return
        
    df = pd.read_csv(csv_path)
    
    # 1. Define Features (X) and Targets (y)
    features = ['speed', 'accel_x', 'gvw', 'gps_slope']
    
    if not all(col in df.columns for col in features):
        print("Error: Missing required columns in CSV.")
        return
        
    X = df[features]
    
    # The 3 things we want the AI to predict
    y_event = df['event_type']
    y_multi = df['severity_multi']
    y_wear = df['wear_units']
    
    # 2. Train the 3 Models using Random Forest
    print("Training Event Type Classifier...")
    clf_event = RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42)
    clf_event.fit(X, y_event)
    
    print("Training Severity Multiplier Regressor...")
    reg_multi = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42)
    reg_multi.fit(X, y_multi)
    
    print("Training Wear Units Regressor...")
    reg_wear = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42)
    reg_wear.fit(X, y_wear)
    
    # 3. Bundle them up
    models = {
        'event_classifier': clf_event,
        'multi_regressor': reg_multi,
        'wear_regressor': reg_wear
    }
    
    # Save the bundled models to a .pkl file
    model_path = os.path.join(os.path.dirname(__file__), 'brake_wear_model.pkl')
    joblib.dump(models, model_path)
    
    print(f"Success! Brake AI Model trained and saved to {model_path}")

if __name__ == "__main__":
    train()
