import os
import base64
import json
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# Default to meta-llama/llama-4-scout-17b-16e-instruct for vision processing
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


def extract_receipt_details(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """
    Sends the base64-encoded receipt image to Groq's Llama 3.2 Vision API
    and extracts structured parameters (liters, price, station_name, refuel_time).
    """
    if not GROQ_API_KEY:
        print("[WARNING] GROQ_API_KEY is not set. Falling back to mock extraction.")
        return {
            "liters": 100.0,
            "price": 9500.0,
            "station_name": "Mock Petrol Pump",
            "refuel_time": None
        }

    # Encode raw image bytes directly to base64
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    image_url_value = f"data:{mime_type};base64,{base64_image}"

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
      "Authorization": f"Bearer {GROQ_API_KEY}",
      "Content-Type": "application/json"
    }

    prompt_text = (
        "Analyze this petrol pump / gas station receipt image. "
        "Extract the following details and return ONLY a valid JSON object: "
        "1. 'liters' (float representation of total liters filled, e.g., 80.5) "
        "2. 'price' (float representation of total cost paid, e.g., 7650.0) "
        "3. 'station_name' (string of the petrol pump or fuel dealer name, e.g., 'Indian Oil') "
        "4. 'refuel_time' (string representation of the date and time printed on the receipt, e.g., '2026-07-09 10:20:00'). "
        "Return ONLY the raw JSON object. Do not wrap it in markdown blockticks or output any conversational text."
    )

    payload = {
        "model": VISION_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": image_url_value}}
                ]
            }
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=(15, 60))
        if response.status_code != 200:
            print(f"[ERROR] Groq API returned status {response.status_code}: {response.text}")
            raise Exception(f"Groq API error: {response.text}")

        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Parse the JSON response
        data = json.loads(content)
        print(f"[OK] Extracted receipt details: {data}")
        return data

    except Exception as e:
        print(f"[ERROR] Failed to extract details from receipt: {e}")
        # Return fallback mock details on failure to prevent server crashes
        return {
            "liters": None,
            "price": None,
            "station_name": "Failed Parse",
            "refuel_time": None
        }
