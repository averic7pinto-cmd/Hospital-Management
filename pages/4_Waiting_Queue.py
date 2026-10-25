import streamlit as st
import pandas as pd
from datetime import datetime, date
from hospital_data import initialize_data, sync_appointments
import c_backend
from consultation import (
    auto_check_consultation_flow, get_consultation_window,
    call_patient_now, complete_consultation_now, DEFAULT_DURATION_MINS
)
from ui import (
    setup_page, hero, panel_heading, html_block, esc, pill, flash,
    PRIORITY_STYLE, STATUS_STYLE
)

st.set_page_config(
    page_title="Waiting Queue | MediCare",
    page_icon="⏳",
    layout="wide"
)

initialize_data()


auto_check_consultation_flow()

setup_page(
    "PATIENT FLOW",
    "Waiting & Consultations",
    "Live patient flow, consultation timing (30 min doctor slots)."
)

STATUSES = ["Scheduled", "Waiting", "In Consultation", "Completed", "Cancelled"]

appointments = st.session_state.appointments

# Active consultation alert
active_alert = st.session_state.pop("_consultation_alert", None)
if active_alert:
    st.info(active_alert, icon="🔔")

waiting = appointments[
    appointments["Status"] == "Waiting"
].copy() if not appointments.empty else pd.DataFrame(columns=appointments.columns)

priority_order = {
    "Emergency": 0,
    "High": 1,
    "Normal": 2
}

if not waiting.empty:
    waiting["_PriorityOrder"] = (
        waiting["Priority"].map(priority_order).fillna(2)
    )
    waiting = waiting.sort_values(
        by=["_PriorityOrder", "Date", "Time"],
        ascending=[True, True, True]
    ).reset_index(drop=True)

in_consultation = appointments[
    appointments["Status"] == "In Consultation"
].copy() if not appointments.empty else pd.DataFrame(columns=appointments.columns)

emergency_count = len(waiting[waiting["Priority"] == "Emergency"]) if not waiting.empty else 0
high_count = len(waiting[waiting["Priority"] == "High"]) if not waiting.empty else 0
estimated_wait = max(len(waiting) - 1, 0) * DEFAULT_DURATION_MINS


hero(
    "⏳",
    "Live Patient Queue & Consultations",
    f"Active 30-minute consultation slots per doctor. Check for availiabilty",
    [
        ("In Queue", len(waiting)),
        ("In Consultation", len(in_consultation)),
        ("Emergency", emergency_count),
        ("Est. Last Wait", f"{estimated_wait}m"),
    ]
)


ctrl_col1, ctrl_col2 = st.columns([3, 1])
with ctrl_col1:
    now_str = datetime.now().strftime("%H:%M:%S")
    st.caption(f"🕒 Current Hospital Clock: **{now_str}** · Standard Doctor Consultation: **{DEFAULT_DURATION_MINS} minutes**")
with ctrl_col2:
    if st.button("🔄 Check Schedule / Refresh", use_container_width=True):
        auto_check_consultation_flow()
        sync_appointments()
        st.rerun()

left, right = st.columns([1.7, 1], gap="large")



with left:
    # 1. IN CONSULTATION PANEL
    st.markdown("### ⚕ Active Consultations")
    if in_consultation.empty:
        st.markdown(
            """
            <div style="background:#f8fafc;padding:1rem;border-radius:8px;border:1px dashed #cbd5e1;color:#64748b;margin-bottom:1.5rem;">
                No doctor is currently consulting a patient. Call the next patient below to start.
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        for _, c_row in in_consultation.iterrows():
            with st.container(border=True):
                c_start, c_end, end_str = get_consultation_window(c_row['Time'], DEFAULT_DURATION_MINS, c_row['Date'])
                c_col1, c_col2, c_col3 = st.columns([3, 2.5, 2])

                with c_col1:
                    st.markdown(f"#### 👤 {esc(c_row['Patient'])}")
                    st.markdown(f"**Token:** `{c_row['Token']}` · **Doctor:** `{esc(c_row['Doctor'])}` ({c_row['Department']})")

                with c_col2:
                    st.markdown(f"⏱️ **Session Window:** `{c_row['Time']} – {end_str}`")
                    st.markdown(f"🩺 **Duration:** `{DEFAULT_DURATION_MINS} minutes`")

                with c_col3:
                    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
                    if st.button("✅ Complete & Call Next", key=f"fin_c_{c_row['Token']}", type="primary", use_container_width=True):
                        complete_consultation_now(c_row['Token'], c_row['Patient'], c_row['Doctor'])
                        sync_appointments()
                        st.rerun()

    st.markdown("### 📋 Waiting Queue (Next Up)")
    if waiting.empty:
        st.markdown(
            """
            <div style="background:#f0fdf4;padding:1.5rem;border-radius:8px;border:1px solid #bbf7d0;color:#166534;margin-bottom:1.5rem;">
                🎉 <strong>No patients are currently waiting.</strong> All scheduled appointments are completed or upcoming.
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        for pos, (_, w_row) in enumerate(waiting.iterrows(), start=1):
            with st.container(border=True):
                w_start, w_end, w_end_str = get_consultation_window(w_row['Time'], DEFAULT_DURATION_MINS, w_row['Date'])
                prio_stripe = PRIORITY_STYLE.get(str(w_row["Priority"]), "grey")

                col_pos, col_info, col_time, col_btn = st.columns([0.8, 3, 2.5, 1.8])

                with col_pos:
                    badge_color = "#ef4444" if w_row["Priority"] == "Emergency" else ("#f59e0b" if w_row["Priority"] == "High" else "#2563eb")
                    st.markdown(
                        f"""
                        <div style="background:{badge_color};color:white;width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:1.1rem;margin-top:6px;">
                            #{pos}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col_info:
                    next_chip = " <span style='background:#fef3c7;color:#92400e;padding:2px 6px;border-radius:4px;font-size:0.75rem;font-weight:700;'>NEXT UP</span>" if pos == 1 else ""
                    st.markdown(f"**{esc(w_row['Patient'])}**{next_chip}", unsafe_allow_html=True)
                    st.caption(f"Token: `{w_row['Token']}` · Doctor: **{esc(w_row['Doctor'])}** ({w_row['Department']})")

                with col_time:
                    st.write(f"🕘 **Time:** `{w_row['Time']}`")
                    st.markdown(
                        f"<div style='display:flex;gap:6px;align-items:center;'><span style='color:#64748b;font-size:0.85rem;'>Priority:</span> {pill(w_row['Priority'], prio_stripe)}</div>",
                        unsafe_allow_html=True
                    )

                with col_btn:
                    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
                    if st.button("📢 Call Patient", key=f"call_w_{w_row['Token']}", type="secondary", use_container_width=True):
                        call_patient_now(w_row['Token'], w_row['Patient'], w_row['Doctor'], DEFAULT_DURATION_MINS)
                        sync_appointments()
                        st.rerun()



with right:
    with st.container(border=True):
        panel_heading("⚙️", "Check Patients Details", "Manual doctor & patient status")

        if appointments.empty:
            st.info("No appointments currently scheduled.")
        else:
            selected_token = st.selectbox(
                "Select Appointment Token",
                appointments["Token"].tolist(),
                key="wq_select_token"
            )

            selected_row = appointments[
                appointments["Token"] == selected_token
            ].iloc[0]

            st.markdown(
                html_block(f"""
                <div class="detail-row"><span>Patient</span><strong>{esc(selected_row['Patient'])}</strong></div>
                <div class="detail-row"><span>Doctor</span><strong>{esc(selected_row['Doctor'])}</strong></div>
                <div class="detail-row"><span>Time Window</span><strong>{esc(selected_row['Time'])} ({DEFAULT_DURATION_MINS}m)</strong></div>
                <div class="detail-row"><span>Status</span>{pill(selected_row['Status'], STATUS_STYLE.get(selected_row['Status'], 'grey'))}</div>
                <div class="detail-row"><span>Priority</span>{pill(selected_row['Priority'], PRIORITY_STYLE.get(selected_row['Priority'], 'grey'))}</div>
                """),
                unsafe_allow_html=True
            )

            new_status = st.selectbox("Change Status", STATUSES, key="wq_new_status")

            btn1, btn2 = st.columns(2)
            with btn1:
                if st.button("Update Status", type="primary", use_container_width=True):
                    ok, msg = c_backend.update_appointment_status(selected_token, new_status)
                    if ok:
                        sync_appointments()
                        flash(f"{selected_token} updated to {new_status}.")
                        st.rerun()
                    else:
                        st.error(msg)
            with btn2:
                if st.button("🗑️ Remove", type="secondary", use_container_width=True):
                    ok, msg = c_backend.delete_appointment(selected_token)
                    if ok:
                        sync_appointments()
                        flash(f"Appointment {selected_token} deleted.")
                        st.rerun()
                    else:
                        st.error(msg)

   