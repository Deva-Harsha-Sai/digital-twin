import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import os

os.makedirs("ml", exist_ok=True)

# ---------------------------
# 1. Simulate Vital Signs Dataset
# ---------------------------
def generate_data(n=1000):
    data = pd.DataFrame({
        "heart_rate": np.random.randint(60, 140, size=n),
        "spo2": np.random.randint(85, 100, size=n),
        "bp_sys": np.random.randint(100, 180, size=n),
        "bp_dia": np.random.randint(60, 120, size=n),
    })

    # Simulate heart risk (binary)
    data["heart_risk"] = ((data["heart_rate"] > 100) | (data["bp_sys"] > 150)).astype(int)

    # Simulate respiratory distress risk (binary)
    data["respiratory_risk"] = (data["spo2"] < 92).astype(int)

    # Simulate stress level (multi-class: 0=low, 1=medium, 2=high)
    stress_score = (
        0.5 * ((data["heart_rate"] - 60) / 80) +
        0.3 * ((data["bp_sys"] - 100) / 80) +
        0.2 * ((100 - data["spo2"]) / 15)
    )
    data["stress_level"] = pd.cut(stress_score, bins=[-1, 0.3, 0.6, 1.1], labels=[0, 1, 2]).astype(int)

    return data

data = generate_data()

X = data[["heart_rate", "spo2", "bp_sys", "bp_dia"]]

# Standardize features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
joblib.dump(scaler, "ml/scaler.pkl")

# ---------------------------
# 2. Train Heart Disease Risk Model
# ---------------------------
y_heart = data["heart_risk"]
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_heart, test_size=0.2, random_state=42)
heart_model = LogisticRegression()
heart_model.fit(X_train, y_train)
joblib.dump(heart_model, "ml/heart_model.pkl")

# ---------------------------
# 3. Train Respiratory Risk Model
# ---------------------------
y_resp = data["respiratory_risk"]
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_resp, test_size=0.2, random_state=42)
resp_model = RandomForestClassifier()
resp_model.fit(X_train, y_train)
joblib.dump(resp_model, "ml/respiratory_model.pkl")

# ---------------------------
# 4. Train Stress Level Classifier
# ---------------------------
y_stress = data["stress_level"]
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_stress, test_size=0.2, random_state=42)
stress_model = RandomForestClassifier()
stress_model.fit(X_train, y_train)
joblib.dump(stress_model, "ml/stress_model.pkl")

print("✅ All models and scaler saved in 'ml/' folder.")
