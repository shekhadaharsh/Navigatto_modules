import urllib.request
import json

try:
    url = "http://127.0.0.1:8000/api/drivers/DR001/trips"
    req = urllib.request.urlopen(url)
    data = json.loads(req.read().decode())
    print(f"Number of trips for DR001: {len(data)}")
    if len(data) > 0:
        print("First trip:", data[0])
except Exception as e:
    print("Error:", e)
