import streamlit as st
import time
from datetime import datetime
from utils.firebase_ops import (
    get_all_patients, get_patient_ehr,
    store_vital, get_patient_vitals, add_patient,
    add_patient_ehr
)
from utils.vitals_simulator import generate_vital, run_all_models

# --- Streamlit Page Config ---
st.set_page_config(
    page_title="Doctor Portal - Digital Twin",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Theme Colors ---
PRIMARY_COLOR = "#2c3e50"
ACCENT_COLOR = "#2980b9"
BACKGROUND_COLOR = "#f0f4f8"
CARD_COLOR = "#ffffff"
TEXT_COLOR = "#222222"

# --- CSS Styling ---
st.markdown(
    f"""
    <style>
    .reportview-container {{
        background-color: {BACKGROUND_COLOR};
        color: {TEXT_COLOR};
    }}
    .sidebar .sidebar-content {{
        background-color: {PRIMARY_COLOR};
        color: white;
    }}
    .card {{
        background-color: {CARD_COLOR};
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }}
    .live-card {{
        background-color: #e8f8f5;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🩺 Doctor Portal - Digital Twin Patient Monitoring")

# --- Sidebar: Add Patient Form ---
st.sidebar.header("➕ Add New Patient")
with st.sidebar.form("add_patient_form"):
    new_name = st.text_input("Name")
    new_age = st.number_input("Age", min_value=0, max_value=120, step=1)
    new_gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    new_contact = st.text_input("Contact Info")
    new_notes = st.text_area("Medical Notes")
    submitted = st.form_submit_button("Add Patient")

    if submitted and new_name:
        patient_id = new_name.lower().replace(" ", "_") + "_" + datetime.utcnow().strftime("%Y%m%d%H%M%S")
        add_patient(
            patient_id, new_name, new_age, new_gender,
            conditions=[new_notes] if new_notes else []
        )
        st.success(f"Patient '{new_name}' added successfully!")
        st.experimental_rerun()

# --- Load Patients ---
patients = get_all_patients()
if not patients:
    st.warning("No patients found. Add a new patient using the sidebar.")
    st.stop()

# --- Patient Selection ---
patient_names = [f"{p.get('name', 'Unnamed')} ({p['id']})" for p in patients]
selected = st.selectbox("Select Patient", ["Select..."] + patient_names)

if selected == "Select...":
    st.info("Please select a patient to view their details.")
    st.stop()

try:
    selected_patient_id = selected.split("(")[-1].strip(")")
except Exception:
    st.error("Invalid patient selection.")
    st.stop()

selected_patient = next((p for p in patients if p["id"] == selected_patient_id), None)
if not selected_patient:
    st.error("Selected patient not found.")
    st.stop()

# --- Patient Card ---
st.markdown(
    f"""
    <div class="card">
        <h3>{selected_patient.get('name', 'Unnamed')}</h3>
        <p><b>Age:</b> {selected_patient.get('age', 'N/A')}</p>
        <p><b>Gender:</b> {selected_patient.get('gender', 'N/A')}</p>
        <p><b>Patient ID:</b> {selected_patient.get('id')}</p>
        <p><b>Contact:</b> {selected_patient.get('contact', 'N/A')}</p>
        <p><b>Notes:</b> {"; ".join(selected_patient.get('conditions', []))}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- EHR Section ---
st.subheader("📋 Electronic Health Record (EHR)")
ehr_records = get_patient_ehr(selected_patient_id)

if ehr_records:
    for i, record in enumerate(ehr_records, 1):
        st.markdown(f"### 📄 EHR Record #{i}")
        st.markdown("---")
        for key, value in record.items():
            if key.lower() in ["id", "patient_id"]:
                continue
            if isinstance(value, list):
                st.write(f"**{key.capitalize()}:**")
                for item in value:
                    st.markdown(f"- {item}")
            elif isinstance(value, dict):
                st.write(f"**{key.capitalize()}:**")
                for subkey, subvalue in value.items():
                    st.markdown(f"- **{subkey}**: {subvalue}")
            else:
                st.write(f"**{key.capitalize()}:** {value}")
else:
    st.info("No EHR records available.")

# --- Add EHR Form ---
with st.expander("➕ Add New EHR Record"):
    with st.form("add_ehr_form"):
        diagnosis = st.text_input("Diagnosis")
        treatment = st.text_input("Treatment")
        medications = st.text_input("Medications (comma-separated)")
        additional_notes = st.text_area("Additional Notes")
        submitted_ehr = st.form_submit_button("Add EHR Record")

        if submitted_ehr and diagnosis:
            ehr_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "diagnosis": diagnosis,
                "treatment": treatment,
                "medications": [m.strip() for m in medications.split(",")] if medications else [],
                "notes": additional_notes
            }
            add_patient_ehr(selected_patient_id, ehr_data)
            st.success("✅ EHR record added.")
            st.experimental_rerun()

# --- Vitals Monitoring ---
# --- Vitals Monitoring ---
st.subheader("⌚ Live Vitals Monitoring")
if st.button("Start Monitoring (30 sec)"):
    placeholder = st.empty()
    
    all_heart_risks = []
    all_respiratory_risks = []
    all_stress_levels = []  # assuming stress_level is numeric, else treat differently

    for second in range(30):
        vitals = generate_vital()
        prediction = run_all_models(vitals)
        store_vital(selected_patient_id, vitals, prediction)

        all_heart_risks.append(prediction['heart_risk'])
        all_respiratory_risks.append(prediction['respiratory_risk'])

        # Try to parse stress_level as float if possible, else keep as is
        try:
            stress_val = float(prediction['stress_level'])
            all_stress_levels.append(stress_val)
        except Exception:
            all_stress_levels.append(prediction['stress_level'])

        with placeholder.container():
            st.markdown(
                f"""
                <div class="live-card">
                    <h4>⏱️ Second {second + 1}</h4>
                    <b>Vitals:</b> {vitals}<br><br>
                    <b>Predictions:</b><br>
                    🫀 Heart Risk: <b>{int(prediction['heart_risk'] * 100)}%</b><br>
                    🌬️ Respiratory Risk: <b>{int(prediction['respiratory_risk'] * 100)}%</b><br>
                    😓 Stress Level: <b>{prediction['stress_level']}</b>
                </div>
                """,
                unsafe_allow_html=True,
            )
        time.sleep(1)

    st.success("✅ 30-second monitoring complete.")

    # --- Calculate Averages ---
    avg_heart_risk = sum(all_heart_risks) / len(all_heart_risks) if all_heart_risks else 0
    avg_respiratory_risk = sum(all_respiratory_risks) / len(all_respiratory_risks) if all_respiratory_risks else 0

    # Handle stress level average only if all numeric, else fallback to showing "Varied" or skip
    numeric_stress_levels = [x for x in all_stress_levels if isinstance(x, (int, float))]
    if len(numeric_stress_levels) == len(all_stress_levels) and numeric_stress_levels:
        avg_stress_level = sum(numeric_stress_levels) / len(numeric_stress_levels)
        avg_stress_display = f"{avg_stress_level:.2f}"
    else:
        avg_stress_display = "Varied / Non-numeric"

    st.markdown(
        f"""
        <div class="card" style="background:#dff0d8;">
            <h3>📊 Results (30 seconds)</h3>
            🫀 Heart Risk: <b>{int(avg_heart_risk * 100)}%</b><br>
            🌬️ Respiratory Risk: <b>{int(avg_respiratory_risk * 100)}%</b><br>
            😓 Stress Level: <b>{avg_stress_display}</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- Past Vitals ---
st.subheader("📈 Past Vitals History")
past_vitals = get_patient_vitals(selected_patient_id)

if past_vitals:
    for record in past_vitals[:10]:
        ts = record.get("timestamp")
        vitals = record.get("vital_data", {})
        preds = record.get("predictions", {})
        st.markdown(
            f"""
            <div class="card" style="background:#ecf0f1;">
                <b>🕒 Timestamp:</b> {ts}<br>
                <b>Vitals:</b> {vitals}<br>
                <b>Predictions:</b><br>
                - Heart Risk: {int(preds.get('heart_risk', 0)*100)}%<br>
                - Respiratory Risk: {int(preds.get('respiratory_risk', 0)*100)}%<br>
                - Stress Level: {preds.get('stress_level', 'N/A')}
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.info("No vitals history found.")

# --- Footer ---
st.markdown("<hr>")
st.markdown(
    """
    <p style="text-align:center; color:gray; font-size:12px;">
    Powered by <b>Digital Twin Technology</b> & Federated Data Fusion
    </p>
    """,
    unsafe_allow_html=True,
)
