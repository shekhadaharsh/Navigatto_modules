import urllib.request
import json

try:
    url = "http://127.0.0.1:8000/api/drivers/DR001/trips/TR001/details"
    req = urllib.request.urlopen(url)
    data = json.loads(req.read().decode())
    print("API Response keys:", list(data.keys()))
    print("Journey:", data.get("journey"))
    print("Driver score:", data.get("driver_score"))
    print("Fuel theft:", data.get("fuel_theft"))
    print("Expected fuel:", data.get("expected_fuel"))
    print("Maintenance:", data.get("maintenance"))
except Exception as e:
    print("Error calling API:", e)
