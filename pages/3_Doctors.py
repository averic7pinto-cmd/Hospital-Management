import streamlit as st
import pandas as pd
from hospital_data import initialize_data
from ui import (
    setup_page, hero, panel_heading, doctor_cards, chip_filter,
    data_table, html_block, pill, h_bars, flash, AVAILABILITY_STYLE
)

st.set_page_config(
    page_title="Doctors | MediCare",
    page_icon="🩺",
    layout="wide"
)

initialize_data()

setup_page(
    "MEDICAL STAFF",
    "Doctors",
    "View doctors, departments, fees, and availability."
)

doctors = st.session_state.doctors

# ---------------- HERO ----------------

hero(
    "🩺",
    "Meet the care team",
    "Browse doctors by department, check who is available and "
    "keep availability up to date.",
    [
        ("Doctors", len(doctors)),
        ("Available",
         len(doctors[doctors["Availability"] == "Available"])),
        ("Busy", len(doctors[doctors["Availability"] == "Busy"])),
        ("Departments", doctors["Department"].nunique()),
    ]
)

tab_directory, tab_manage = st.tabs(
    ["🩺  Doctor Directory", "⚙️  Manage Availability"]
)

# ---------------- DIRECTORY ----------------

with tab_directory:
    departments = ["All"] + sorted(doctors["Department"].unique().tolist())

    department_filter = chip_filter(
        "Filter by Department", departments, key="doctor_department"
    )

    availability_filter = chip_filter(
        "Filter by Availability",
        ["All", "Available", "Busy"],
        key="doctor_availability"
    )

    filtered = doctors.copy()

    if department_filter != "All":
        filtered = filtered[
            filtered["Department"] == department_filter
        ]

    if availability_filter != "All":
        filtered = filtered[
            filtered["Availability"] == availability_filter
        ]

    st.caption(f"Showing {len(filtered)} of {len(doctors)} doctors")

    doctor_cards(filtered)

# ---------------- MANAGE ----------------

with tab_manage:
    update_col, summary_col = st.columns([1, 1.3], gap="large")

    with update_col:
        with st.container(border=True):
            panel_heading("⚙️", "Update Availability",
                          "Change a doctor's status")

            selected_doctor = st.selectbox(
                "Select Doctor",
                doctors["Name"].tolist(),
                key="doctor_availability_select"
            )

            current_availability = doctors.loc[
                doctors["Name"] == selected_doctor,
                "Availability"
            ].iloc[0]

            st.markdown(
                html_block(f"""
                <div class="detail-row">
                    <span>Current status</span>
                    {pill(current_availability,
                          AVAILABILITY_STYLE.get(current_availability, "grey"))}
                </div>
                """),
                unsafe_allow_html=True
            )

            new_availability = st.selectbox(
                "Set Availability",
                ["Available", "Busy"],
                index=["Available", "Busy"].index(current_availability)
            )

            if st.button("Save Availability", type="primary",
                         use_container_width=True):
                index = st.session_state.doctors.index[
                    st.session_state.doctors["Name"] == selected_doctor
                ][0]

                st.session_state.doctors.at[
                    index, "Availability"
                ] = new_availability

                flash(f"{selected_doctor}: {new_availability}")
                st.rerun()

        with st.container(border=True):
            panel_heading("▥", "Doctors per Department",
                          "Staff coverage across specialities")

            h_bars(st.session_state.doctors["Department"].value_counts())

    with summary_col:
        with st.container(border=True):
            panel_heading("📋", "Doctor Table", "Complete staff listing")

            table = st.session_state.doctors.copy()
            table["Consultation Fee"] = (
                "₹" + table["Consultation Fee"].astype(str)
            )

            data_table(
                table,
                pills={"Availability": AVAILABILITY_STYLE},
                max_height=460
            )

            st.markdown(
                '<div class="note">Doctor details are sample data for the '
                'GUI prototype.</div>',
                unsafe_allow_html=True
            )