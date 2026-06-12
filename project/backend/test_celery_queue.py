import requests
import uuid
from datetime import datetime, timedelta

def test_celery():
    print("Testing Celery Queue via API...")
    url = "http://127.0.0.1:8000/maintenance/telemetry"
    
    vid = "9FC1905B-9E13-4BF7-8742-56C270915E41" # Hardcoded to prevent DB lock hang
    
    now = datetime.utcnow()
    fake_data = {
        "rows": [
            {
                "vehicle_id": vid,
                "ts": (now - timedelta(minutes=1)).isoformat(),
                "rpm": 2500,
                "coolant_temp": 110.0,
                "engine_load": 60.0,
                "fuel_rate": 10.0,
                "idle_time": 0.0,
                "speed": 110.0,
                "ignition": 1,
                "engine_torque": 0.0,
                "oil_pressure": 350.0,
                "brake_pedal": 0,
                "accel_x": 0.0,
                "accel_y": 0.05,
                "accel_z": 0.02,
                "gvw": 12000.0,
                "gps_slope": 0.0,
                "odometer": 10001.0
            }
        ]
    }
    
    print(f"Sending 1 Telemetry Packet to API: {url}")
    try:
        response = requests.post(url, json=fake_data)
        print(f"API Response Status Code: {response.status_code}")
        print(f"API Response Body: {response.json()}")
        print("\n✅ Task has been queued! Check your Celery Terminal window to see if it processed it.")
    except Exception as e:
        print(f"Error connecting to API: {e}")

if __name__ == "__main__":
    test_celery()
