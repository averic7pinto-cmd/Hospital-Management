import streamlit as st
import pandas as pd
from datetime import date
from hospital_data import initialize_data
from ui import (
    setup_page, hero, panel_heading, appointment_cards, chip_filter,
    html_block, esc, pill, initials, flash,
    PRIORITY_STYLE, STATUS_STYLE
)

st.set_page_config(
    page_title="Appointments | MediCare",
    page_icon="📅",
    layout="wide"
)

initialize_data()

setup_page(
    "SCHEDULING",
    "Appointments",
    "Book, view, and manage hospital appointments."
)

STATUSES = ["Scheduled", "Waiting", "In Consultation", "Completed", "Cancelled"]

appointments = st.session_state.appointments
patients = st.session_state.patients
doctors = st.session_state.doctors

# ---------------- HERO ----------------

hero(
    "📅",
    "Keep every visit on track",
    "Book new visits, follow today's schedule and move patients "
    "through consultation.",
    [
        ("Total", len(appointments)),
        ("Today", len(appointments[appointments["Date"] == date.today()])),
        ("Waiting", len(appointments[appointments["Status"] == "Waiting"])),
        ("Completed",
         len(appointments[appointments["Status"] == "Completed"])),
    ]
)

tab_records, tab_book, tab_update = st.tabs(
    ["📋  All Appointments", "➕  Book Appointment", "🔄  Update Status"]
)

# ---------------- RECORDS ----------------

with tab_records:
    filter_col, search_col = st.columns([2.2, 1], gap="medium")

    with filter_col:
        status_filter = chip_filter(
            "Filter by Status", ["All"] + STATUSES, key="appt_status"
        )

    with search_col:
        search_text = st.text_input(
            "Search Patient or Doctor",
            placeholder="🔍  Search patient or doctor...",
            label_visibility="collapsed"
        )

    filtered = appointments.copy()

    if status_filter != "All":
        filtered = filtered[filtered["Status"] == status_filter]

    if search_text.strip():
        mask = (
            filtered["Patient"].str.contains(
                search_text, case=False, na=False
            )
            | filtered["Doctor"].str.contains(
                search_text, case=False, na=False
            )
        )
        filtered = filtered[mask]

    st.caption(f"Showing {len(filtered)} of {len(appointments)} appointments")

    appointment_cards(
        filtered,
        empty_text="No appointments match your filters."
    )

# ---------------- BOOKING ----------------

with tab_book:
    if patients.empty:
        st.warning("Register a patient on the Patients page first.")
    else:
        form_col, preview_col = st.columns([1.15, 1], gap="large")

        with form_col:
            with st.container(border=True):
                panel_heading("➕", "New Appointment",
                              "Choose a patient, a doctor and a time")

                selected_patient = st.selectbox(
                    "Select Patient",
                    patients["Name"].tolist()
                )

                selected_doctor = st.selectbox(
                    "Select Doctor",
                    doctors["Name"].tolist()
                )

                doctor_row = doctors[
                    doctors["Name"] == selected_doctor
                ].iloc[0]

                with st.form("appointment_form", clear_on_submit=True):
                    col1, col2 = st.columns(2)

                    with col1:
                        appointment_date = st.date_input(
                            "Appointment Date",
                            value=date.today(),
                            min_value=date.today()
                        )

                    with col2:
                        appointment_time = st.time_input("Appointment Time")

                    priority = st.selectbox(
                        "Priority",
                        ["Normal", "High", "Emergency"]
                    )

                    submitted = st.form_submit_button(
                        "Confirm Appointment",
                        use_container_width=True,
                        type="primary"
                    )

                    if submitted:
                        if (
                            appointment_date == date.today()
                            and appointment_time.strftime("%H:%M") <
                                pd.Timestamp.now().strftime("%H:%M")
                        ):
                            st.error("Please choose a future time.")
                        else:
                            existing_tokens = len(
                                st.session_state.appointments
                            ) + 101

                            new_appointment = {
                                "Token": f"T-{existing_tokens}",
                                "Patient": selected_patient,
                                "Doctor": selected_doctor,
                                "Department": doctor_row["Department"],
                                "Date": appointment_date,
                                "Time": appointment_time.strftime("%I:%M %p"),
                                "Priority": priority,
                                "Status": "Waiting"
                                if appointment_date == date.today()
                                else "Scheduled"
                            }

                            st.session_state.appointments = pd.concat(
                                [
                                    st.session_state.appointments,
                                    pd.DataFrame([new_appointment])
                                ],
                                ignore_index=True
                            )

                            flash(
                                f"Appointment created! Token: "
                                f"{new_appointment['Token']}"
                            )
                            st.rerun()

        with preview_col:
            with st.container(border=True):
                panel_heading("👁️", "Booking Preview",
                              "Updates as you choose")

                st.markdown(
                    html_block(f"""
                    <div class="doc-card">
                        <div class="doc-avatar">{esc(initials(selected_doctor))}</div>
                        <div class="doc-info">
                            <strong>{esc(selected_doctor)}</strong>
                            <small>{esc(doctor_row['Department'])}</small>
                            <div class="doc-fee">₹{esc(doctor_row['Consultation Fee'])} consultation</div>
                        </div>
                        {pill(doctor_row['Availability'],
                              'green' if doctor_row['Availability'] == 'Available' else 'orange')}
                    </div>
                    <div class="detail-row"><span>Patient</span>
                        <strong>{esc(selected_patient)}</strong></div>
                    <div class="detail-row"><span>Department</span>
                        <strong>{esc(doctor_row['Department'])}</strong></div>
                    <div class="detail-row"><span>Consultation fee</span>
                        <strong>₹{esc(doctor_row['Consultation Fee'])}</strong></div>
                    """),
                    unsafe_allow_html=True
                )

                st.markdown(
                    '<div class="note">Appointments for today join the '
                    'waiting queue straight away; future dates are marked '
                    'Scheduled.</div>',
                    unsafe_allow_html=True
                )

# ---------------- UPDATE STATUS ----------------

with tab_update:
    if appointments.empty:
        st.info("There are no appointments to update yet.")
    else:
        update_col, detail_col = st.columns([1.15, 1], gap="large")

        with update_col:
            with st.container(border=True):
                panel_heading("🔄", "Update Appointment Status",
                              "Move a patient through the visit")

                selected_token = st.selectbox(
                    "Select Token",
                    appointments["Token"].tolist()
                )

                new_status = st.selectbox("New Status", STATUSES)

                if st.button("Update Status", type="primary",
                             use_container_width=True):
                    index = st.session_state.appointments.index[
                        st.session_state.appointments["Token"]
                        == selected_token
                    ][0]

                    st.session_state.appointments.at[
                        index, "Status"
                    ] = new_status
                    flash(f"{selected_token} updated to {new_status}.")
                    st.rerun()

        with detail_col:
            row = appointments[
                appointments["Token"] == selected_token
            ].iloc[0]

            with st.container(border=True):
                panel_heading("🧾", "Appointment Details",
                              f"Token {selected_token}")

                st.markdown(
                    html_block(f"""
                    <div class="detail-row"><span>Patient</span>
                        <strong>{esc(row['Patient'])}</strong></div>
                    <div class="detail-row"><span>Doctor</span>
                        <strong>{esc(row['Doctor'])}</strong></div>
                    <div class="detail-row"><span>Date &amp; time</span>
                        <strong>{esc(row['Date'])} · {esc(row['Time'])}</strong></div>
                    <div class="detail-row"><span>Priority</span>
                        {pill(row['Priority'], PRIORITY_STYLE.get(row['Priority'], 'grey'))}</div>
                    <div class="detail-row"><span>Current status</span>
                        {pill(row['Status'], STATUS_STYLE.get(row['Status'], 'grey'))}</div>
                    """),
                    unsafe_allow_html=True
                )