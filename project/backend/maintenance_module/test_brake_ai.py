import joblib
import pandas as pd
import os

def test_brake_ai():
    print("========================================")
    print(" BRAKE WEAR AI MODEL - LIVE TEST ")
    print("========================================\n")

    # Load the trained model
    model_path = os.path.join(os.path.dirname(__file__), 'brake_wear_model.pkl')
    try:
        models = joblib.load(model_path)
        print("[OK] AI Model successfully loaded from disk!\n")
    except Exception as e:
        print(f"[FAIL] Failed to load AI Model: {e}")
        return

    # Define some test scenarios
    scenarios = [
        {
            "name": "Scenario 1: Light City Braking",
            "data": {'speed': 30.0, 'accel_x': -0.15, 'gvw': 10000.0, 'gps_slope': 0.0}
        },
        {
            "name": "Scenario 2: Medium Highway Braking",
            "data": {'speed': 80.0, 'accel_x': -0.25, 'gvw': 15000.0, 'gps_slope': 0.0}
        },
        {
            "name": "Scenario 3: Harsh Emergency Braking",
            "data": {'speed': 60.0, 'accel_x': -0.60, 'gvw': 12000.0, 'gps_slope': 0.0}
        },
        {
            "name": "Scenario 4: Heavy Loaded Harsh Braking",
            "data": {'speed': 70.0, 'accel_x': -0.55, 'gvw': 19000.0, 'gps_slope': 0.0}
        },
        {
            "name": "Scenario 5: Downhill Harsh Braking",
            "data": {'speed': 50.0, 'accel_x': -0.45, 'gvw': 15000.0, 'gps_slope': -5.0}
        }
    ]

    for scenario in scenarios:
        print(f"> {scenario['name']}")
        input_df = pd.DataFrame([scenario["data"]])
        
        # AI Inference
        event_type = models['event_classifier'].predict(input_df)[0]
        multi = float(models['multi_regressor'].predict(input_df)[0])
        wear_units = float(models['wear_regressor'].predict(input_df)[0])
        
        print(f"   Inputs:  {scenario['data']}")
        print(f"   --> AI Predicted Event:     '{event_type}'")
        print(f"   --> AI Predicted Multiplier: {round(multi, 2)}x")
        print(f"   --> AI Predicted Wear:       {round(wear_units, 2)} units\n")

if __name__ == "__main__":
    test_brake_ai()
