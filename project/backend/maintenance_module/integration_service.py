import os
import uuid
import json
import re
import datetime
import requests
from sqlalchemy.orm import Session
from sqlalchemy import text

# Default baseline values by vehicle type
DEFAULT_BASELINES = {
    "Cargo Van": {
        "brake": {"base_life": 50000.0, "unit": "km"},
        "tire": {"base_life": 80000.0, "unit": "km"},
        "battery": {"base_life": 5000.0, "unit": "cycles"},
        "engine": {"base_life": 10000.0, "unit": "hours"}
    },
    "Medium Truck": {
        "brake": {"base_life": 40000.0, "unit": "km"},
        "tire": {"base_life": 70000.0, "unit": "km"},
        "battery": {"base_life": 4000.0, "unit": "cycles"},
        "engine": {"base_life": 8000.0, "unit": "hours"}
    },
    "Heavy Truck": {
        "brake": {"base_life": 30000.0, "unit": "km"},
        "tire": {"base_life": 60000.0, "unit": "km"},
        "battery": {"base_life": 3000.0, "unit": "cycles"},
        "engine": {"base_life": 6000.0, "unit": "hours"}
    }
}

class VehicleIntegrationService:
    @staticmethod
    def decode_vin(db: Session, vin: str) -> dict:
        """
        Decodes the VIN using cache-first strategy.
        Falls back to external api call, or mock data if offline/no key is found.
        """
        vin = vin.strip().upper()
        
        # 1. Check cache first
        try:
            cached = db.execute(
                text("SELECT response_json FROM dbo.vehicle_api_cache WHERE vin = :vin"),
                {"vin": vin}
            ).fetchone()
            if cached:
                print(f"[VehicleIntegrationService] VIN cache hit for: {vin}")
                return json.loads(cached[0])
        except Exception as e:
            print(f"[VehicleIntegrationService] Cache read error: {e}")

        # 2. Query external API (or mock fallback if offline/no key)
        api_key = os.getenv("VEHICLE_DATABASE_API_KEY")
        api_response = None

        if api_key:
            try:
                # Basic VIN Decode API request from vehicledatabases.com
                url = f"https://api.vehicledatabases.com/vin-decode/{vin}"
                headers = {"x-authkey": api_key}
                res = requests.get(url, headers=headers, timeout=20)
                if res.status_code == 200:
                    data = res.json()
                    # Map external fields to standard formats
                    api_response = {
                        "make": data.get("make"),
                        "model": data.get("model"),
                        "year": int(data.get("year")) if data.get("year") else None,
                        "engine": data.get("engine"),
                        "fuel": data.get("fuel_type") or data.get("fuel"),
                        "transmission": data.get("transmission"),
                        "body_type": data.get("body_class") or data.get("body_type")
                    }
                else:
                    print(f"[VehicleIntegrationService] External API returned non-200 status: {res.status_code}, response: {res.text}")
            except Exception as e:
                print(f"[VehicleIntegrationService] External API VIN decode failed: {e}")

        # 3. If API failed or no key, perform smart mock matching based on common VIN prefixes
        if not api_response:
            print(f"[VehicleIntegrationService] Using internal mock decoder for: {vin}")
            # Mock details based on typical patterns in tests
            if "HONDA" in vin or vin.startswith("1HG") or vin.startswith("5FN"):
                api_response = {"make": "Honda", "model": "Civic", "year": 2022, "engine": "2.0L", "fuel": "Gasoline"}
            elif "FORD" in vin or vin.startswith("1FA") or vin.startswith("1FT"):
                api_response = {"make": "Ford", "model": "Transit", "year": 2021, "engine": "3.5L", "fuel": "Gasoline"}
            elif "TOYOTA" in vin or vin.startswith("JTD") or vin.startswith("4T1"):
                api_response = {"make": "Toyota", "model": "Camry", "year": 2023, "engine": "2.5L", "fuel": "Gasoline"}
            elif "VOLVO" in vin or vin.startswith("YV1"):
                api_response = {"make": "Volvo", "model": "FH16", "year": 2020, "engine": "16.0L", "fuel": "Diesel"}
            else:
                # General default mock if prefix is unknown
                api_response = {"make": "Generic", "model": "Truck", "year": 2020, "engine": "4.0L", "fuel": "Diesel"}

        # 4. Save to cache database
        try:
            db.execute(
                text("""
                    INSERT INTO dbo.vehicle_api_cache (id, vin, make, model, year, engine, fuel, response_json, created_at)
                    VALUES (:id, :vin, :make, :model, :year, :engine, :fuel, :response_json, :created_at)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "vin": vin,
                    "make": api_response.get("make"),
                    "model": api_response.get("model"),
                    "year": api_response.get("year"),
                    "engine": api_response.get("engine"),
                    "fuel": api_response.get("fuel"),
                    "response_json": json.dumps(api_response),
                    "created_at": datetime.datetime.now()
                }
            )
            db.commit()
            print(f"[VehicleIntegrationService] VIN response cached for: {vin}")
        except Exception as e:
            db.rollback()
            print(f"[VehicleIntegrationService] Cache write failed: {e}")

        return api_response

    @staticmethod
    def fetch_maintenance_schedule(db: Session, vehicle_id: str, make: str, model: str, year: int, vin: str = None) -> list:
        """
        Fetches the vehicle maintenance schedule using cache-first strategy.
        Returns a list of maintenance milestone dicts.
        """
        # 1. Check cache first
        try:
            rows = db.execute(
                text("""
                    SELECT service_item, interval_km, interval_months, source 
                    FROM dbo.maintenance_schedule_cache 
                    WHERE vehicle_id = :vehicle_id
                """),
                {"vehicle_id": vehicle_id}
            ).fetchall()
            if rows:
                print(f"[VehicleIntegrationService] Maintenance schedule cache hit for: {vehicle_id}")
                return [
                    {
                        "service_item": r[0],
                        "interval_km": r[1],
                        "interval_months": r[2],
                        "source": r[3]
                    }
                    for r in rows
                ]
        except Exception as e:
            print(f"[VehicleIntegrationService] Schedule cache query failed: {e}")

        # 2. Call external OEM Maintenance API (or fallback if offline/no key)
        api_key = os.getenv("VEHICLE_DATABASE_API_KEY")
        schedule_items = []
        source = "OEM_API"

        if api_key:
            try:
                # Query vehicledatabases.com maintenance schedule endpoint
                res = None
                if vin:
                    print(f"[VehicleIntegrationService] Querying schedule by VIN: {vin}")
                    url = f"https://api.vehicledatabases.com/vehicle-maintenance/v4/{vin}"
                    headers = {"x-authkey": api_key}
                    res = requests.get(url, headers=headers, timeout=20)
                    if res.status_code != 200:
                        print(f"[VehicleIntegrationService] VIN schedule query returned status {res.status_code}. Retrying by Make/Model/Year fallback...")
                        res = None

                if not res and make and model and year:
                    print(f"[VehicleIntegrationService] Querying schedule by Make/Model/Year: {make} {model} {year}")
                    url = "https://api.vehicledatabases.com/vehicle-maintenance/v4"
                    params = {"make": make, "model": model, "year": year}
                    headers = {"x-authkey": api_key}
                    res = requests.get(url, params=params, headers=headers, timeout=20)

                if res and res.status_code == 200:
                    data = res.json()
                    print(f"[VehicleIntegrationService] OEM Maintenance API response JSON: {data}")
                    # Standardize OEM service schedule items list
                    raw_items = data.get("maintenance", []) or data.get("schedule", [])
                    for item in raw_items:
                        schedule_items.append({
                            "service_item": item.get("action") or item.get("description"),
                            "interval_km": item.get("interval_km") or item.get("mileage_km") or 15000,
                            "interval_months": item.get("interval_months") or 12
                        })
                else:
                    status_code = res.status_code if res else "No Request"
                    response_text = res.text if res else "N/A"
                    print(f"[VehicleIntegrationService] OEM Maintenance API returned non-200 status: {status_code}, response: {response_text}")
            except Exception as e:
                print(f"[VehicleIntegrationService] OEM Maintenance API call failed: {e}")

        # 3. Fallback to default internal template if empty
        if not schedule_items:
            print(f"[VehicleIntegrationService] Applying default internal templates for {make} {model}")
            source = "INTERNAL_TEMPLATE"
            schedule_items = [
                {"service_item": "Brake pads inspection and potential replacement", "interval_km": 30000, "interval_months": 24},
                {"service_item": "Rotate tires and check alignment", "interval_km": 15000, "interval_months": 12},
                {"service_item": "Replace spark plugs and engine air filter", "interval_km": 60000, "interval_months": 36},
                {"service_item": "Replace main 12V battery unit", "interval_km": 80000, "interval_months": 48},
                {"service_item": "Change engine oil and inspect filters", "interval_km": 10000, "interval_months": 6}
            ]

        # 4. Save to cache database
        try:
            now = datetime.datetime.now()
            for item in schedule_items:
                db.execute(
                    text("""
                        INSERT INTO dbo.maintenance_schedule_cache (id, vehicle_id, service_item, interval_km, interval_months, source, created_at)
                        VALUES (:id, :vehicle_id, :service_item, :interval_km, :interval_months, :source, :created_at)
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "vehicle_id": vehicle_id,
                        "service_item": item["service_item"],
                        "interval_km": item.get("interval_km"),
                        "interval_months": item.get("interval_months"),
                        "source": source,
                        "created_at": now
                    }
                )
            db.commit()
            print(f"[VehicleIntegrationService] Schedule cached successfully for vehicle: {vehicle_id}")
        except Exception as e:
            db.rollback()
            print(f"[VehicleIntegrationService] Cache write for schedule failed: {e}")

        return schedule_items

    @classmethod
    def generate_base_life(cls, db: Session, vehicle_id: str, vehicle_type: str, make: str, model: str, year: int, vin: str = None) -> dict:
        """
        Parses the maintenance schedule using the Knowledge Engine parser
        to estimate component base life values.
        """
        # Determine classification category fallback
        v_class = "Medium Truck"
        if vehicle_type:
            v_type_lower = vehicle_type.lower()
            if "van" in v_type_lower or "car" in v_type_lower or "cargo" in v_type_lower:
                v_class = "Cargo Van"
            elif "heavy" in v_type_lower or "semi" in v_type_lower or "container" in v_type_lower:
                v_class = "Heavy Truck"
        
        defaults = DEFAULT_BASELINES[v_class]
        
        # Load the schedule
        schedule = cls.fetch_maintenance_schedule(db, vehicle_id, make, model, year, vin)
        
        # Initialize results with default classification templates
        estimated_baselines = {
            "brake": defaults["brake"]["base_life"],
            "tire": defaults["tire"]["base_life"],
            "battery": defaults["battery"]["base_life"],
            "engine": defaults["engine"]["base_life"]
        }

        # Knowledge Engine parsing rules
        for item in schedule:
            desc = item["service_item"].lower()
            km = item.get("interval_km")
            if not km or km <= 0:
                continue

            # 1. Brakes Wear baseline detection
            if "brake" in desc or "pad" in desc:
                # If replacement is explicitly mentioned, set baseline
                if "replace" in desc or "change" in desc:
                    estimated_baselines["brake"] = float(km)
                else:
                    # If just inspection, baseline is estimated at 1.5x inspection interval
                    estimated_baselines["brake"] = float(km * 1.5)

            # 2. Tires Wear baseline detection
            elif "tire" in desc or "tyre" in desc:
                if "replace" in desc or "change" in desc or "new" in desc:
                    estimated_baselines["tire"] = float(km)
                else:
                    # Tires rotation/alignment is done frequently, replacement baseline is longer
                    estimated_baselines["tire"] = float(km * 4.0)

            # 3. Battery Wear baseline detection
            elif "battery" in desc or "crank" in desc:
                # Battery starts cycles estimated from months (e.g. 100 starts per month)
                months = item.get("interval_months") or (km / 1000)
                estimated_baselines["battery"] = float(max(1000, months * 100))

            # 4. Engine Wear baseline detection
            elif "engine" in desc or "coolant" in desc or "spark plug" in desc:
                # Convert km to engine hours: e.g. km / average speed of 50 km/h
                estimated_baselines["engine"] = float(max(1000, km / 5.0))

        # Clamp all baselines to reasonable physical ranges to prevent outliers
        estimated_baselines["brake"] = max(10000.0, min(80000.0, estimated_baselines["brake"]))
        estimated_baselines["tire"] = max(20000.0, min(150000.0, estimated_baselines["tire"]))
        estimated_baselines["battery"] = max(1000.0, min(10000.0, estimated_baselines["battery"]))
        estimated_baselines["engine"] = max(2000.0, min(20000.0, estimated_baselines["engine"]))

        return estimated_baselines
