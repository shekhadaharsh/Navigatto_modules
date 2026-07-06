import urllib.request
import json

try:
    url = "http://127.0.0.1:8000/api/drivers"
    req = urllib.request.urlopen(url)
    data = json.loads(req.read().decode())
    print("Drivers:", data)
except Exception as e:
    print("Error:", e)
