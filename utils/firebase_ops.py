# utils/firebase_ops.py
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Initialize Firebase
cred = credentials.Certificate("firebase_config.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ---------------------
# Patient Management
# ---------------------
def add_patient(patient_id, name, age, gender, conditions=None):
    ref = db.collection("patients").document(patient_id)
    ref.set({
        "name": name,
        "age": age,
        "gender": gender,
        "conditions": conditions or [],
        "created_at": datetime.utcnow()
    })

def get_all_patients():
    docs = db.collection("patients").stream()
    return [{**doc.to_dict(), "id": doc.id} for doc in docs]

def get_patient(patient_id):
    doc = db.collection("patients").document(patient_id).get()
    if doc.exists:
        return doc.to_dict()
    return None

# ---------------------
# EHR Retrieval
# ---------------------
def get_patient_ehr(patient_id):
    ehr_ref = db.collection("patients").document(patient_id).collection("ehr").stream()
    return [{**doc.to_dict(), "id": doc.id} for doc in ehr_ref]

# ---------------------
# Vital Simulation Storage
# ---------------------
def store_vital(patient_id, vital_data, predictions):
    data = {
        "timestamp": datetime.utcnow(),
        "vital_data": vital_data,
        "predictions": predictions
    }
    db.collection("patients").document(patient_id).collection("vitals").add(data)

# ---------------------
# Retrieve Historical Vitals
# ---------------------
def get_patient_vitals(patient_id):
    vitals_ref = (
        db.collection("patients")
          .document(patient_id)
          .collection("vitals")
          .order_by("timestamp", direction=firestore.Query.DESCENDING)
    )
    docs = vitals_ref.stream()
    return [doc.to_dict() for doc in docs]


def add_patient_ehr(patient_id, ehr_data):
    from firebase_admin import firestore
    db = firestore.client()
    ehr_ref = db.collection("patients").document(patient_id).collection("ehr")
    ehr_ref.add(ehr_data)

