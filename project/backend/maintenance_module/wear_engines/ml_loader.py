"""
Vehicle Maintenance Wear and Alert Engines
--------------------------------------------
Calculates wear increments and alerts based on FMC650 sensor data.
Supports incremental processing to prevent double-counting.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime
import math
import joblib
import os
import pandas as pd
import logging

_ENGINE_AI_MODELS = None
_BRAKE_AI_MODELS = None
_TIRE_AI_MODELS = None

def get_engine_model():
    global _ENGINE_AI_MODELS
    if _ENGINE_AI_MODELS is None:
        try:
            path = os.path.join(os.path.dirname(__file__), 'engine_wear_model.pkl')
            _ENGINE_AI_MODELS = joblib.load(path)
        except Exception as e:
            logging.warning(f"Could not load AI model for engine wear: {e}")
    return _ENGINE_AI_MODELS

def get_brake_model():
    global _BRAKE_AI_MODELS
    if _BRAKE_AI_MODELS is None:
        try:
            path = os.path.join(os.path.dirname(__file__), 'brake_wear_model.pkl')
            _BRAKE_AI_MODELS = joblib.load(path)
        except Exception as e:
            logging.warning(f"Could not load AI model for brake wear: {e}")
    return _BRAKE_AI_MODELS

def get_tire_model():
    global _TIRE_AI_MODELS
    if _TIRE_AI_MODELS is None:
        try:
            path = os.path.join(os.path.dirname(__file__), 'tire_wear_model.pkl')
            _TIRE_AI_MODELS = joblib.load(path)
        except Exception as e:
            logging.warning(f"Could not load AI model for tire wear: {e}")
    return _TIRE_AI_MODELS

# ── Wear Thresholds & Constants ──────────────────────────────
