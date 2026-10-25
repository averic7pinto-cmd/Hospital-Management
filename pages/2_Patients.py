import streamlit as st
import pandas as pd
from datetime import date
from hospital_data import initialize_data, sync_patients, sync_appointments, sync_all
import c_backend
from ui import (
    setup_page, hero, panel_heading, chip_filter,
    h_bars, donut, flash, pill, html_block, esc, HEX, GENDER_STYLE
)

st.set_page_config(
    page_title="Patients | MediCare",
    page_icon="👥",
    layout="wide"
)

initialize_data()

setup_page(
    "PATIENT RECORDS",
    "Patients",
    "Register, view, search, and manage hospital patient records."
)

patients = st.session_state.patients
doctors = st.session_state.doctors
appointments = st.session_state.appointments

# ---------------- HERO ----------------

average_age = (
    f"{patients['Age'].mean():.0f}" if not patients.empty else "0"
)

hero(
    "👥",
    "Patient Directory & Management",
    "Add new patients manually, search directory records, and remove patients. ",
    [
        ("Registered", len(patients)),
        ("Male", len(patients[patients["Gender"] == "Male"]) if not patients.empty else 0),
        ("Female", len(patients[patients["Gender"] == "Female"]) if not patients.empty else 0),
        ("Avg. age", average_age),
    ]
)

tab_directory, tab_register, tab_manage = st.tabs(
    ["👥  Patient Directory", "➕  Add Patient", "🔍  Find Patient"]
)

# ---------------- DIRECTORY ----------------

with tab_directory:
    filter_col, search_col = st.columns([2, 1.2], gap="medium")

    with filter_col:
        gender_filter = chip_filter(
            "Filter by gender",
            ["All", "Male", "Female", "Other"],
            key="patient_gender"
        )

    with search_col:
        search = st.text_input(
            "Search patients",
            placeholder="🔍  Search name, ID or phone...",
            label_visibility="collapsed"
        )

    filtered = patients.copy() if not patients.empty else pd.DataFrame(columns=patients.columns)

    if gender_filter != "All" and not filtered.empty:
        filtered = filtered[filtered["Gender"] == gender_filter]

    if search.strip() and not filtered.empty:
        mask = (
            filtered["Name"].str.contains(search, case=False, na=False)
            | filtered["Patient ID"].str.contains(search, case=False, na=False)
            | filtered["Phone"].astype(str).str.contains(search, case=False, na=False)
        )
        filtered = filtered[mask]

    c_status = "⚡ C Hash Table Active (patients.dll & patients.csv)" if st.session_state.get("c_backend_active") else "Session Memory"
    st.caption(f"Showing {len(filtered)} of {len(patients)} registered patients · {c_status}")

    if filtered.empty:
        st.markdown(
            """
            <div class="empty-state" style="padding:2.5rem 1rem;text-align:center;background:#f8faff;border-radius:12px;border:1px dashed #cbd5e1;margin-top:1rem;">
                <div style="font-size:2.5rem;margin-bottom:0.5rem;">👥</div>
                <h3 style="margin:0 0 0.5rem 0;color:#1e293b;">No Patients Found</h3>
                <p style="color:#64748b;margin:0 0 1rem 0;">No patients currently exist. Add a patient using the <strong>➕ Add Patient</strong> tab.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        for _, p in filtered.iterrows():
            with st.container(border=True):
                col_info, col_contact, col_appts, col_action = st.columns([3, 2.5, 2, 1.2], gap="small")

                with col_info:
                    st.markdown(f"#### {esc(p['Name'])}")
                    gender = str(p['Gender'])
                    st.markdown(
                        f"""
                        <div style="display:flex;gap:6px;align-items:center;">
                            <span style="font-weight:600;color:#2563eb;background:#eff6ff;padding:2px 8px;border-radius:4px;font-size:0.85rem;">{esc(p['Patient ID'])}</span>
                            <span style="color:#64748b;font-size:0.9rem;">· {p['Age']} yrs ·</span>
                            {pill(gender, GENDER_STYLE.get(gender, 'grey'))}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col_contact:
                    st.write(f"📞 **Phone:** `{p['Phone']}`")
                    st.write(f"🩸 **Blood Group:** `{p['Blood Group']}`")

                with col_appts:
                    # Count appointments for this patient
                    user_appts = appointments[appointments["Patient"] == p["Name"]] if not appointments.empty else pd.DataFrame()
                    st.write(f"📅 **Appointments:** `{len(user_appts)}`")
                    if not user_appts.empty:
                        latest_date = str(user_appts.iloc[-1]["Date"])
                        st.caption(f"Latest: {latest_date}")
                    else:
                        st.caption("No visits scheduled yet")

                with col_action:
                    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                    if st.button("🗑️ Remove", key=f"btn_del_patient_{p['Patient ID']}", type="secondary", use_container_width=True):
                        patient_name = p['Name']
                        pid = p['Patient ID']
                        ok, msg = c_backend.delete_patient(pid)
                        if ok:
                            # Also delete any appointments associated with this patient
                            deleted_appts = c_backend.delete_appointments_by_patient(patient_name)
                            sync_all()
                            flash(f"Patient '{patient_name}' ({pid}) and {deleted_appts} linked appointment(s) removed successfully.")
                            st.rerun()
                        else:
                            st.error(msg)

# ---------------- ADD PATIENT ----------------

with tab_register:
    form_col, overview_col = st.columns([1.2, 1], gap="large")

    with form_col:
        with st.container(border=True):
            panel_heading("➕", "Add a New Patient",
                          "Enter original patient details to save to patients.csv")

            with st.form("patient_form", clear_on_submit=True):
                name = st.text_input("Patient Full Name", placeholder="e.g. Everett", help="Enter patient name")

                col1, col2 = st.columns(2)

                with col1:
                    age = st.number_input(
                        "Age",
                        min_value=0,
                        max_value=120,
                        value=30
                    )

                    gender = st.selectbox(
                        "Gender",
                        ["Male", "Female", "Other"]
                    )

                with col2:
                    phone = st.text_input(
                        "Phone Number",
                        placeholder="e.g. 9876543210",
                        max_chars=15
                    )

                    blood_group = st.selectbox(
                        "Blood Group",
                        ["O+", "A+", "B+", "AB+", "O-", "A-", "B-", "AB-", "Unknown"]
                    )

                st.markdown("---")
                st.markdown("#### 📅 Schedule Initial Appointment")
                schedule_now = st.checkbox("Book an appointment for this patient now", value=True)

                selected_doctor = None
                appointment_date = None
                appointment_time = None
                priority = "Normal"

                if schedule_now:
                    doc_col, prio_col = st.columns(2)
                    with doc_col:
                        selected_doctor = st.selectbox(
                            "Consulting Doctor",
                            doctors["Name"].tolist()
                        )
                    with prio_col:
                        priority = st.selectbox(
                            "Priority",
                            ["Normal", "High", "Emergency"]
                        )

                    dt_col, tm_col = st.columns(2)
                    with dt_col:
                        appointment_date = st.date_input(
                            "Appointment Date",
                            value=date.today(),
                            min_value=date.today()
                        )
                    with tm_col:
                        appointment_time = st.time_input("Appointment Time")

                submitted = st.form_submit_button(
                    "Register Patient & Save",
                    type="primary",
                    use_container_width=True
                )

                if submitted:
                    if not name.strip():
                        st.error("Please enter the patient's name.")
                    elif not phone.strip():
                        st.error("Please enter a phone number.")
                    elif not phone.strip().replace("+", "").isdigit():
                        st.error("Enter a valid phone number using digits and an optional +.")
                    else:
                        existing_ids = set(st.session_state.patients["Patient ID"].tolist()) if not st.session_state.patients.empty else set()
                        counter = 1001 + len(existing_ids)
                        while f"P-{counter}" in existing_ids:
                            counter += 1
                        patient_id = f"P-{counter}"

                        # 1. Add patient into C hash table and patients.csv
                        ok, msg = c_backend.add_patient(
                            patient_id, name.strip(), int(age), gender, phone.strip(), blood_group
                        )

                        if not ok:
                            st.error(msg)
                        else:
                            # 2. If schedule_now was checked, also book appointment into appointments.csv
                            appt_msg = ""
                            if schedule_now and selected_doctor:
                                existing_tokens = set(
                                    st.session_state.appointments["Token"].tolist()
                                ) if not st.session_state.appointments.empty else set()

                                t_num = len(existing_tokens) + 101
                                while f"T-{t_num}" in existing_tokens:
                                    t_num += 1
                                token = f"T-{t_num}"

                                doc_row = doctors[doctors["Name"] == selected_doctor].iloc[0]
                                dept = doc_row["Department"]
                                appt_status = "Waiting" if appointment_date == date.today() else "Scheduled"

                                ok_appt, msg_appt = c_backend.add_appointment(
                                    token=token,
                                    patient=name.strip(),
                                    doctor=selected_doctor,
                                    department=dept,
                                    appointment_date=appointment_date,
                                    appointment_time=appointment_time,
                                    priority=priority,
                                    status=appt_status
                                )
                                if ok_appt:
                                    appt_msg = f" and appointment booked with {selected_doctor} (Token: {token})"
                                else:
                                    appt_msg = f" (Note: appointment could not be booked: {msg_appt})"

                            sync_all()
                            flash(f"Patient '{name.strip()}' registered successfully (ID: {patient_id}){appt_msg}!")
                            st.rerun()

    with overview_col:
        with st.container(border=True):
            panel_heading("📊", "Patient Overview",
                          "Live summary of registered patients")

            if not st.session_state.patients.empty:
                gender_counts = st.session_state.patients["Gender"].value_counts()
                donut(
                    gender_counts,
                    colors={"Male": HEX["blue"], "Female": HEX["purple"],
                            "Other": HEX["grey"]},
                    center_label="Patients",
                    empty_text="Register a patient to see the breakdown."
                )
            else:
                st.info("No patients registered yet. Add a patient on the left to see statistics.")

        with st.container(border=True):
            panel_heading("🩸", "Blood Groups", "Registered patient blood types")

            if not st.session_state.patients.empty:
                blood_counts = st.session_state.patients["Blood Group"].value_counts()
                h_bars(
                    blood_counts,
                    colors={group: HEX["red"] for group in blood_counts.index},
                    empty_text="No blood-group data yet."
                )
            else:
                st.info("No blood-group data yet.")

# ---------------- FIND PATIENT ----------------

with tab_manage:
    with st.container(border=True):
        panel_heading("🔍", "Find Patient",
                      "Instant search by Patient ID")

        query_col, btn_col = st.columns([3, 1])
        with query_col:
            query_id = st.text_input("Enter Patient ID", placeholder="e.g. P-1001", label_visibility="collapsed")
        with btn_col:
            search_btn = st.button("Search Patient", type="primary", use_container_width=True)

        if search_btn or query_id.strip():
            if query_id.strip():
                result = c_backend.find_patient_by_id(query_id.strip())
                if result:
                    st.success(f"Patient record found for {result['Name']} ({result['Patient ID']}):")
                    st.markdown(html_block(f"""
                    <div class="detail-row"><span>Patient ID</span><strong>{esc(result['Patient ID'])}</strong></div>
                    <div class="detail-row"><span>Name</span><strong>{esc(result['Name'])}</strong></div>
                    <div class="detail-row"><span>Age</span><strong>{result['Age']} yrs</strong></div>
                    <div class="detail-row"><span>Gender</span>{pill(result['Gender'], GENDER_STYLE.get(result['Gender'], 'grey'))}</div>
                    <div class="detail-row"><span>Phone</span><strong>{esc(result['Phone'])}</strong></div>
                    <div class="detail-row"><span>Blood Group</span><strong>{esc(result['Blood Group'])}</strong></div>
                    """), unsafe_allow_html=True)
                else:
                    st.warning(f"Patient ID '{query_id.strip()}' was not found in the records.")
            else:
                st.info("Please enter a Patient ID to search.")
