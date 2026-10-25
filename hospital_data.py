import streamlit as st
import pandas as pd
import c_backend


def initialize_data():
    """Initialize C backend (DLLs) and sync data into Streamlit session state."""

    # 1. Initialize C libraries (patients.dll & appointments.dll)
    backend_ok = c_backend.init_backend()
    st.session_state.c_backend_active = backend_ok

    # 2. Sync Patients into session state (only real manual data from C backend / CSV)
    if "patients" not in st.session_state or backend_ok:
        if backend_ok:
            st.session_state.patients = c_backend.get_patients_df()
        elif "patients" not in st.session_state:
            st.session_state.patients = pd.DataFrame(columns=[
                "Patient ID", "Name", "Age", "Gender", "Phone", "Blood Group"
            ])

    # 3. Sync Appointments into session state (only real manual data from C backend / CSV)
    if "appointments" not in st.session_state or backend_ok:
        if backend_ok:
            st.session_state.appointments = c_backend.get_appointments_df()
        elif "appointments" not in st.session_state:
            st.session_state.appointments = pd.DataFrame(columns=[
                "Token", "Patient", "Doctor", "Department",
                "Date", "Time", "Priority", "Status"
            ])

    # 4. Doctors directory (as specified, doctors list is kept)
    if "doctors" not in st.session_state:
        st.session_state.doctors = pd.DataFrame([
            {"Doctor ID": "D-101", "Name": "Dr. Mehta", "Department": "Cardiology", "Availability": "Available", "Consultation Fee": 700},
            {"Doctor ID": "D-102", "Name": "Dr. Rao", "Department": "Neurology", "Availability": "Available", "Consultation Fee": 600},
            {"Doctor ID": "D-103", "Name": "Dr. Shah", "Department": "Orthopedics", "Availability": "Busy", "Consultation Fee": 500},
            {"Doctor ID": "D-104", "Name": "Dr. Fernandes", "Department": "General Medicine", "Availability": "Available", "Consultation Fee": 400},
        ])


def sync_patients():
    """Refresh st.session_state.patients from C hash table backend."""
    if c_backend.is_backend_available():
        st.session_state.patients = c_backend.get_patients_df()


def sync_appointments():
    """Refresh st.session_state.appointments from C min-heap backend."""
    if c_backend.is_backend_available():
        st.session_state.appointments = c_backend.get_appointments_df()


def sync_all():
    """Refresh all datasets from C backend."""
    sync_patients()
    sync_appointments()
