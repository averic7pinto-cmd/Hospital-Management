
import streamlit as st
import pandas as pd


def initialize_data():
    """Create demo data once per Streamlit session."""

    if "patients" not in st.session_state:
        st.session_state.patients = pd.DataFrame([
            {
                "Patient ID": "P-1001",
                "Name": "Rahul Sharma",
                "Age": 32,
                "Gender": "Male",
                "Phone": "9876543210",
                "Blood Group": "O+"
            },
            {
                "Patient ID": "P-1002",
                "Name": "Priya Nair",
                "Age": 27,
                "Gender": "Female",
                "Phone": "9876543211",
                "Blood Group": "B+"
            },
            {
                "Patient ID": "P-1003",
                "Name": "Arjun Patel",
                "Age": 45,
                "Gender": "Male",
                "Phone": "9876543212",
                "Blood Group": "A+"
            }
        ])

    if "doctors" not in st.session_state:
        st.session_state.doctors = pd.DataFrame([
            {
                "Doctor ID": "D-101",
                "Name": "Dr. Mehta",
                "Department": "Cardiology",
                "Availability": "Available",
                "Consultation Fee": 700
            },
            {
                "Doctor ID": "D-102",
                "Name": "Dr. Rao",
                "Department": "Neurology",
                "Availability": "Available",
                "Consultation Fee": 600
            },
            {
                "Doctor ID": "D-103",
                "Name": "Dr. Shah",
                "Department": "Orthopedics",
                "Availability": "Busy",
                "Consultation Fee": 500
            },
            {
                "Doctor ID": "D-104",
                "Name": "Dr. Fernandes",
                "Department": "General Medicine",
                "Availability": "Available",
                "Consultation Fee": 400
            }
        ])

    if "appointments" not in st.session_state:
        st.session_state.appointments = pd.DataFrame([
            {
                "Token": "T-101",
                "Patient": "Rahul Sharma",
                "Doctor": "Dr. Mehta",
                "Department": "Cardiology",
                "Date": pd.Timestamp.today().date(),
                "Time": "09:30 AM",
                "Priority": "Normal",
                "Status": "Waiting"
            },
            {
                "Token": "T-102",
                "Patient": "Priya Nair",
                "Doctor": "Dr. Rao",
                "Department": "Neurology",
                "Date": pd.Timestamp.today().date(),
                "Time": "10:00 AM",
                "Priority": "High",
                "Status": "In Consultation"
            },
            {
                "Token": "T-103",
                "Patient": "Arjun Patel",
                "Doctor": "Dr. Mehta",
                "Department": "Cardiology",
                "Date": pd.Timestamp.today().date(),
                "Time": "10:30 AM",
                "Priority": "Normal",
                "Status": "Scheduled"
            }
        ])
