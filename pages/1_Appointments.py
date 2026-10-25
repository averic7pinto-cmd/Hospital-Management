import streamlit as st
import pandas as pd
from datetime import date, datetime
from hospital_data import initialize_data, sync_appointments, sync_all
import c_backend
from consultation import (
    auto_check_consultation_flow, get_consultation_window,
    call_patient_now, complete_consultation_now, DEFAULT_DURATION_MINS
)
from ui import (
    setup_page, hero, panel_heading, chip_filter,
    html_block, esc, pill, initials, flash,
    PRIORITY_STYLE, STATUS_STYLE
)

st.set_page_config(
    page_title="Appointments | MediCare",
    page_icon="📅",
    layout="wide"
)

initialize_data()

# Auto-check consultation timings against current clock
auto_check_consultation_flow()

setup_page(
    "SCHEDULING",
    "Appointments",
    "Book, view, call, and manage hospital appointments with 30-minute consultation slots."
)

STATUSES = ["Scheduled", "Waiting", "In Consultation", "Completed", "Cancelled"]

appointments = st.session_state.appointments
patients = st.session_state.patients
doctors = st.session_state.doctors

# Active consultation alert
active_alert = st.session_state.pop("_consultation_alert", None)
if active_alert:
    st.info(active_alert, icon="🔔")

# ---------------- HERO ----------------

hero(
    "📅",
    "Appointments & Visit Management",
    "Schedule new visits, view appointment queues, and track 30-minute doctor consultations. ",
    [
        ("Total", len(appointments)),
        ("Today", len(appointments[appointments["Date"] == date.today()]) if not appointments.empty else 0),
        ("Waiting", len(appointments[appointments["Status"] == "Waiting"]) if not appointments.empty else 0),
        ("Completed",
         len(appointments[appointments["Status"] == "Completed"]) if not appointments.empty else 0),
    ]
)

tab_records, tab_book, tab_update = st.tabs(
    ["📋  All Appointments", "➕  Book Appointment", "🔄  Update / Remove"]
)

# ---------------- RECORDS (ALL APPOINTMENTS) ----------------

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

    filtered = appointments.copy() if not appointments.empty else pd.DataFrame(columns=appointments.columns)

    if status_filter != "All" and not filtered.empty:
        filtered = filtered[filtered["Status"] == status_filter]

    if search_text.strip() and not filtered.empty:
        mask = (
            filtered["Patient"].str.contains(
                search_text, case=False, na=False
            )
            | filtered["Doctor"].str.contains(
                search_text, case=False, na=False
            )
        )
        filtered = filtered[mask]

    c_status = "⚡ C Min-Heap Active (appointments.dll & appointments.csv)" if st.session_state.get("c_backend_active") else "Session Memory"
    st.caption(f"Showing {len(filtered)} of {len(appointments)} scheduled appointments · {c_status}")

    if filtered.empty:
        st.markdown(
            """
            <div class="empty-state" style="padding:2.5rem 1rem;text-align:center;background:#f8faff;border-radius:12px;border:1px dashed #cbd5e1;margin-top:1rem;">
                <div style="font-size:2.5rem;margin-bottom:0.5rem;">📅</div>
                <h3 style="margin:0 0 0.5rem 0;color:#1e293b;">No Appointments Found</h3>
                <p style="color:#64748b;margin:0 0 1rem 0;">No appointments match your filter. Book an appointment using the <strong>➕ Book Appointment</strong> tab.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        for _, r in filtered.iterrows():
            with st.container(border=True):
                _, _, end_time_str = get_consultation_window(r['Time'], DEFAULT_DURATION_MINS, r['Date'])
                status = str(r['Status'])

                col_token, col_patient, col_schedule, col_action = st.columns([1.5, 2.7, 3, 1.8], gap="small")

                with col_token:
                    st.markdown(f"#### {esc(r['Token'])}")
                    st.markdown(pill(status, STATUS_STYLE.get(status, 'grey')), unsafe_allow_html=True)

                with col_patient:
                    st.markdown(f"**Patient:** {esc(r['Patient'])}")
                    st.caption(f"Doctor: **{esc(r['Doctor'])}** ({esc(r['Department'])})")

                with col_schedule:
                    priority = str(r['Priority'])
                    prio_color = PRIORITY_STYLE.get(priority, 'grey')
                    st.write(f"📅 **Date:** `{r['Date']}` · 🕘 **Time:** `{r['Time']}`")
                    st.write(f"⏱️ **Session:** `{r['Time']} – {end_time_str}` (30 mins)")

                with col_action:
                    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
                    if status == "Waiting":
                        if st.button("📢 Call Patient", key=f"btn_call_appt_{r['Token']}", type="primary", use_container_width=True):
                            call_patient_now(r['Token'], r['Patient'], r['Doctor'], DEFAULT_DURATION_MINS)
                            sync_appointments()
                            st.rerun()
                    elif status == "In Consultation":
                        if st.button("✅ Complete", key=f"btn_fin_appt_{r['Token']}", type="primary", use_container_width=True):
                            complete_consultation_now(r['Token'], r['Patient'], r['Doctor'])
                            sync_appointments()
                            st.rerun()

                    if st.button("🗑️ Remove", key=f"btn_del_appt_{r['Token']}", type="secondary", use_container_width=True):
                        tok = r['Token']
                        pat = r['Patient']
                        ok, msg = c_backend.delete_appointment(tok)
                        if ok:
                            sync_appointments()
                            flash(f"Appointment {tok} for {pat} was removed from C min-heap and CSV.")
                            st.rerun()
                        else:
                            st.error(msg)

# ---------------- BOOKING ----------------

with tab_book:
    form_col, preview_col = st.columns([1.2, 1], gap="large")

    with form_col:
        with st.container(border=True):
            panel_heading("➕", "Book Appointment",
                          "Schedule a patient visit into C Min-Heap")

            # Patient selection (existing or quick new)
            has_existing = not patients.empty
            patient_mode = "Select Existing Patient"

            if has_existing:
                patient_mode = st.radio(
                    "Patient Choice",
                    ["Select Existing Patient", "Register New Patient"],
                    horizontal=True
                )

            selected_patient_name = ""
            new_patient_age = 30
            new_patient_gender = "Male"
            new_patient_phone = ""
            new_patient_bg = "O+"

            if patient_mode == "Select Existing Patient" and has_existing:
                selected_patient_name = st.selectbox(
                    "Select Patient",
                    patients["Name"].tolist()
                )
            else:
                st.markdown("##### New Patient Details")
                selected_patient_name = st.text_input("Patient Full Name", placeholder="e.g. Everett")
                np_col1, np_col2 = st.columns(2)
                with np_col1:
                    new_patient_age = st.number_input("Age", min_value=0, max_value=120, value=30, key="np_age")
                    new_patient_gender = st.selectbox("Gender", ["Male", "Female", "Other"], key="np_gen")
                with np_col2:
                    new_patient_phone = st.text_input("Phone Number", placeholder="e.g. 9876543210", max_chars=15, key="np_ph")
                    new_patient_bg = st.selectbox("Blood Group", ["O+", "A+", "B+", "AB+", "O-", "A-", "B-", "AB-", "Unknown"], key="np_bg")

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

                prio_col, dur_col = st.columns(2)
                with prio_col:
                    priority = st.selectbox(
                        "Priority",
                        ["Normal", "High", "Emergency"]
                    )
                with dur_col:
                    duration_mins = st.selectbox(
                        "Consultation Duration",
                        [30, 15, 45, 60],
                        index=0,
                        format_func=lambda m: f"{m} minutes"
                    )

                submitted = st.form_submit_button(
                    "Confirm & Save Appointment",
                    use_container_width=True,
                    type="primary"
                )

                if submitted:
                    if not selected_patient_name.strip():
                        st.error("Please enter or select a patient name.")
                    else:
                        # If a new patient was typed in, register them in C hash table first
                        if patient_mode == "Register New Patient" or not has_existing:
                            if not new_patient_phone.strip() or not new_patient_phone.strip().replace("+", "").isdigit():
                                st.error("Please provide a valid phone number for the new patient.")
                                st.stop()

                            existing_pids = set(patients["Patient ID"].tolist()) if not patients.empty else set()
                            p_counter = 1001 + len(existing_pids)
                            while f"P-{p_counter}" in existing_pids:
                                p_counter += 1
                            new_pid = f"P-{p_counter}"

                            ok_p, msg_p = c_backend.add_patient(
                                new_pid, selected_patient_name.strip(), int(new_patient_age),
                                new_patient_gender, new_patient_phone.strip(), new_patient_bg
                            )
                            if not ok_p:
                                st.error(f"Could not register patient: {msg_p}")
                                st.stop()

                        # Generate unique token
                        existing_tokens = set(
                            st.session_state.appointments["Token"].tolist()
                        ) if not st.session_state.appointments.empty else set()

                        counter = len(existing_tokens) + 101
                        while f"T-{counter}" in existing_tokens:
                            counter += 1
                        token = f"T-{counter}"

                        initial_status = "Waiting" if appointment_date == date.today() else "Scheduled"

                        # Insert into C priority min-heap backend and appointments.csv
                        ok, msg = c_backend.add_appointment(
                            token=token,
                            patient=selected_patient_name.strip(),
                            doctor=selected_doctor,
                            department=doctor_row["Department"],
                            appointment_date=appointment_date,
                            appointment_time=appointment_time,
                            priority=priority,
                            status=initial_status
                        )

                        if ok:
                            sync_all()
                            flash(f"Appointment booked for '{selected_patient_name.strip()}' with {selected_doctor} on {appointment_date} at {appointment_time.strftime('%H:%M')}! Token: {token}")
                            st.rerun()
                        else:
                            st.error(msg)

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
                    <strong>{esc(selected_patient_name or 'Not specified')}</strong></div>
                <div class="detail-row"><span>Department</span>
                    <strong>{esc(doctor_row['Department'])}</strong></div>
                <div class="detail-row"><span>Session Length</span>
                    <strong>30 minutes</strong></div>
                <div class="detail-row"><span>Consultation fee</span>
                    <strong>₹{esc(doctor_row['Consultation Fee'])}</strong></div>
                """),
                unsafe_allow_html=True
            )

            st.markdown(
                '<div class="note">Each consultation reserves a 30-minute block for the doctor. '
                'When the appointment time arrives, an alert is triggered and the patient moves to consultation. '
                'After 30 minutes, consultation completes automatically and the next patient is called.</div>',
                unsafe_allow_html=True
            )

# ---------------- UPDATE / REMOVE ----------------

with tab_update:
    if appointments.empty:
        st.info("There are no appointments to update or remove yet.")
    else:
        update_col, detail_col = st.columns([1.15, 1], gap="large")

        with update_col:
            with st.container(border=True):
                panel_heading("🔄", "Update or Remove Appointment",
                              "Manage appointment status or delete record")

                selected_token = st.selectbox(
                    "Select Token",
                    appointments["Token"].tolist()
                )

                new_status = st.selectbox("New Status", STATUSES)

                b_col1, b_col2 = st.columns(2)
                with b_col1:
                    if st.button("Update Status", type="primary", use_container_width=True):
                        ok, msg = c_backend.update_appointment_status(selected_token, new_status)
                        if ok:
                            sync_appointments()
                            flash(f"{selected_token} updated to {new_status} in C Min-Heap & CSV.")
                            st.rerun()
                        else:
                            st.error(msg)

                with b_col2:
                    if st.button("🗑️ Delete Visit", type="secondary", use_container_width=True):
                        ok, msg = c_backend.delete_appointment(selected_token)
                        if ok:
                            sync_appointments()
                            flash(f"Appointment {selected_token} deleted from C Min-Heap and CSV.")
                            st.rerun()
                        else:
                            st.error(msg)

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
                        <strong>{esc(row['Date'])} · {esc(row['Time'])} (30 mins)</strong></div>
                    <div class="detail-row"><span>Priority</span>
                        {pill(row['Priority'], PRIORITY_STYLE.get(row['Priority'], 'grey'))}</div>
                    <div class="detail-row"><span>Current status</span>
                        {pill(row['Status'], STATUS_STYLE.get(row['Status'], 'grey'))}</div>
                    """),
                    unsafe_allow_html=True
                )
