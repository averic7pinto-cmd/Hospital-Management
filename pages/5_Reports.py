import streamlit as st
import pandas as pd
from hospital_data import initialize_data
from ui import (
    setup_page, hero, panel_heading, donut, h_bars, hex_for, gap,
    HEX, STATUS_STYLE, PRIORITY_STYLE
)

st.set_page_config(
    page_title="Reports | MediCare",
    page_icon="📊",
    layout="wide"
)

initialize_data()

setup_page(
    "INSIGHTS",
    "Reports",
    "Explore appointment trends and hospital activity."
)

appointments = st.session_state.appointments
patients = st.session_state.patients
doctors = st.session_state.doctors

# ---------------- HERO ----------------

completed = len(appointments[appointments["Status"] == "Completed"])

hero(
    "📊",
    "Hospital activity at a glance",
    "See how appointments are distributed by status, department, "
    "priority and doctor, then export the data.",
    [
        ("Patients", len(patients)),
        ("Appointments", len(appointments)),
        ("Completed", completed),
        ("Doctors", len(doctors)),
    ]
)


def counts_for(column):
    if appointments.empty:
        return None
    return appointments[column].value_counts()


# ---------------- CHARTS ----------------

row1_left, row1_right = st.columns(2, gap="medium")

with row1_left:
    with st.container(border=True):
        panel_heading("📅", "Appointments by Status",
                      "Where every appointment currently stands")
        status_counts = counts_for("Status")
        donut(
            status_counts,
            colors=hex_for(
                STATUS_STYLE,
                status_counts.index if status_counts is not None else []
            ),
            center_label="Appointments",
            empty_text="No appointment data available yet."
        )

with row1_right:
    with st.container(border=True):
        panel_heading("🏥", "Department Activity",
                      "Appointment volume per department")
        h_bars(
            counts_for("Department"),
            empty_text="Book appointments to view department activity."
        )

gap()

row2_left, row2_right = st.columns(2, gap="medium")

with row2_left:
    with st.container(border=True):
        panel_heading("🚦", "Priority Breakdown",
                      "Normal, high and emergency cases")
        priority_counts = counts_for("Priority")
        donut(
            priority_counts,
            colors=hex_for(
                PRIORITY_STYLE,
                priority_counts.index if priority_counts is not None else []
            ),
            center_label="Cases",
            empty_text="No appointment data available yet."
        )

with row2_right:
    with st.container(border=True):
        panel_heading("🩺", "Doctor Workload",
                      "Appointments handled per doctor")
        h_bars(
            counts_for("Doctor"),
            empty_text="No appointment data available yet."
        )

gap()

# ---------------- EXPORT ----------------

with st.container(border=True):
    panel_heading("⬇️", "Export Report",
                  "Download the current appointment data")

    if appointments.empty:
        st.info("There is no appointment data to export yet.")
    else:
        csv_data = appointments.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download Appointments CSV",
            data=csv_data,
            file_name="hospital_appointments_report.csv",
            mime="text/csv",
            use_container_width=True
        )

    st.markdown(
        '<div class="note">Reports are calculated from the current '
        "session's demo data. They are not permanent records.</div>",
        unsafe_allow_html=True
    )