import joblib
import pandas as pd
import os

def test_ai_model():
    print("========================================")
    print(" ENGINE WEAR AI MODEL - LIVE TEST ")
    print("========================================\n")

    # Load the trained model
    model_path = os.path.join(os.path.dirname(__file__), 'engine_wear_model.pkl')
    try:
        models = joblib.load(model_path)
        print("[OK] AI Model successfully loaded from disk!\n")
    except Exception as e:
        print(f"[FAIL] Failed to load AI Model: {e}")
        return

    # Define some test scenarios
    scenarios = [
        {
            "name": "Scenario 1: Normal Smooth Driving",
            "data": {'rpm': 1500, 'coolant_temp': 85.0, 'engine_load': 30.0, 'fuel_rate': 5.0, 'idle_time': 0.0}
        },
        {
            "name": "Scenario 2: Overheating Engine",
            "data": {'rpm': 2500, 'coolant_temp': 110.0, 'engine_load': 50.0, 'fuel_rate': 8.0, 'idle_time': 0.0}
        },
        {
            "name": "Scenario 3: High Load (Pulling heavy weight)",
            "data": {'rpm': 2000, 'coolant_temp': 90.0, 'engine_load': 95.0, 'fuel_rate': 30.0, 'idle_time': 0.0}
        },
        {
            "name": "Scenario 4: Idling for too long",
            "data": {'rpm': 800, 'coolant_temp': 80.0, 'engine_load': 15.0, 'fuel_rate': 2.0, 'idle_time': 45.0}
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
    test_ai_model()
