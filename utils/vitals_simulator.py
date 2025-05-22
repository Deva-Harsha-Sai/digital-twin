# utils/vitals_simulator.py
import random
import time
import joblib
from datetime import datetime
from utils.firebase_ops import store_vital

# Load ML models and scaler
scaler = joblib.load("ml/scaler.pkl")
heart_model = joblib.load("ml/heart_model.pkl")
resp_model = joblib.load("ml/respiratory_model.pkl")
stress_model = joblib.load("ml/stress_model.pkl")

# ---------------------------
# Simulate One Vital Sample
# ---------------------------
def generate_vital():
    return {
        "heart_rate": random.randint(60, 140),
        "spo2": random.randint(85, 100),
        "bp_sys": random.randint(100, 180),
        "bp_dia": random.randint(60, 120)
    }

# ---------------------------
# Run all ML Models
# ---------------------------
def run_all_models(vital):
    X = [[
        vital["heart_rate"],
        vital["spo2"],
        vital["bp_sys"],
        vital["bp_dia"]
    ]]
    X_scaled = scaler.transform(X)

    heart_risk = round(heart_model.predict_proba(X_scaled)[0][1], 2)
    respiratory_risk = round(resp_model.predict_proba(X_scaled)[0][1], 2)
    stress_level = int(stress_model.predict(X_scaled)[0])

    return {
        "heart_risk": heart_risk,
        "respiratory_risk": respiratory_risk,
        "stress_level": stress_level
    }

# ---------------------------
# Simulate Monitoring Session
# ---------------------------
def monitor_patient(patient_id, update_ui_callback=None):
    for _ in range(30):  # 30 seconds
        vital = generate_vital()
        prediction = run_all_models(vital)
        store_vital(patient_id, vital, prediction)

        if update_ui_callback:
            update_ui_callback(vital, prediction)

        time.sleep(1)  # simulate real-time
