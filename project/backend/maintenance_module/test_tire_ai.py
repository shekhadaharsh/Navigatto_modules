import joblib
import pandas as pd
import os

def test_tire_ai():
    print("========================================")
    print(" TIRE WEAR AI MODEL - LIVE TEST ")
    print("========================================\n")

    # Load the trained model
    model_path = os.path.join(os.path.dirname(__file__), 'models', 'tire_wear_model.pkl')
    try:
        models = joblib.load(model_path)
        print("[OK] AI Model successfully loaded from disk!\n")
    except Exception as e:
        print(f"[FAIL] Failed to load AI Model: {e}")
        return

    # Define some test scenarios
    scenarios = [
        {
            "name": "Scenario 1: Normal City Driving",
            "data": {'speed': 40.0, 'lateral_g': 0.1, 'accel_z': 0.05, 'gvw': 10000.0}
        },
        {
            "name": "Scenario 2: High Speed Highway",
            "data": {'speed': 110.0, 'lateral_g': 0.05, 'accel_z': 0.02, 'gvw': 12000.0}
        },
        {
            "name": "Scenario 3: Harsh Cornering",
            "data": {'speed': 60.0, 'lateral_g': 0.55, 'accel_z': 0.08, 'gvw': 15000.0}
        },
        {
            "name": "Scenario 4: Heavy Overloaded Truck",
            "data": {'speed': 50.0, 'lateral_g': 0.15, 'accel_z': 0.1, 'gvw': 19500.0}
        },
        {
            "name": "Scenario 5: Rough Offroad Driving",
            "data": {'speed': 30.0, 'lateral_g': 0.2, 'accel_z': 0.25, 'gvw': 14000.0}
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
        print(f"   --> AI Predicted Wear:       {round(wear_units, 4)} units\n")

if __name__ == "__main__":
    test_tire_ai()
