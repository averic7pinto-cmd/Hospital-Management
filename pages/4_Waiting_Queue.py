import streamlit as st
import pandas as pd
from hospital_data import initialize_data
from ui import (
    setup_page, hero, panel_heading, queue_cards, appointment_cards,
    html_block, esc, pill, flash, PRIORITY_STYLE, STATUS_STYLE
)

st.set_page_config(
    page_title="Waiting Queue | MediCare",
    page_icon="⏳",
    layout="wide"
)

initialize_data()

setup_page(
    "PATIENT FLOW",
    "Waiting Queue",
    "Monitor patient tokens, priority, and queue positions."
)

STATUSES = ["Scheduled", "Waiting", "In Consultation", "Completed", "Cancelled"]

appointments = st.session_state.appointments

waiting = appointments[
    appointments["Status"] == "Waiting"
].copy()

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
]

emergency_count = len(waiting[waiting["Priority"] == "Emergency"]) \
    if not waiting.empty else 0
high_count = len(waiting[waiting["Priority"] == "High"]) \
    if not waiting.empty else 0
estimated_wait = max(len(waiting) - 1, 0) * 15

# ---------------- HERO ----------------

hero(
    "⏳",
    "Live patient queue",
    "Emergency and high-priority patients move to the front. Waits "
    "are illustrative, at 15 minutes per patient ahead.",
    [
        ("Waiting", len(waiting)),
        ("Emergency", emergency_count),
        ("High priority", high_count),
        ("Last wait", f"{estimated_wait}m"),
    ]
)

left, right = st.columns([1.6, 1], gap="large")

# ---------------- QUEUE ----------------

with left:
    if not in_consultation.empty:
        with st.container(border=True):
            panel_heading("⚕", "In Consultation",
                          "Patients currently with a doctor")
            appointment_cards(in_consultation)

    with st.container(border=True):
        panel_heading("📋", "Up Next",
                      "Ordered by priority, then date and time")

        queue_cards(waiting)

# ---------------- MANAGE + GUIDE ----------------

with right:
    with st.container(border=True):
        panel_heading("🔄", "Manage Patient Status",
                      "Update a patient's visit progress")

        if appointments.empty:
            st.info("There are no appointments to manage.")
        else:
            selected_token = st.selectbox(
                "Select Appointment Token",
                appointments["Token"].tolist()
            )

            selected_row = appointments[
                appointments["Token"] == selected_token
            ].iloc[0]

            st.markdown(
                html_block(f"""
                <div class="detail-row"><span>Patient</span>
                    <strong>{esc(selected_row['Patient'])}</strong></div>
                <div class="detail-row"><span>Current status</span>
                    {pill(selected_row['Status'],
                          STATUS_STYLE.get(selected_row['Status'], 'grey'))}</div>
                <div class="detail-row"><span>Priority</span>
                    {pill(selected_row['Priority'],
                          PRIORITY_STYLE.get(selected_row['Priority'], 'grey'))}</div>
                """),
                unsafe_allow_html=True
            )

            new_status = st.selectbox("Update Status", STATUSES)

            if st.button("Update Patient Status", type="primary",
                         use_container_width=True):
                row_index = st.session_state.appointments.index[
                    st.session_state.appointments["Token"] == selected_token
                ][0]

                st.session_state.appointments.at[
                    row_index, "Status"
                ] = new_status

                flash(f"{selected_token} updated to {new_status}.")
                st.rerun()

    with st.container(border=True):
        panel_heading("📌", "Priority Guide", "How the queue is ordered")

        st.markdown(
            html_block("""
            <div class="guide-grid" style="grid-template-columns:1fr">
                <div class="guide-tile red">
                    <strong>🔴 Emergency</strong>
                    <span>Highest queue priority in this demonstration.</span>
                </div>
                <div class="guide-tile amber">
                    <strong>🟠 High Priority</strong>
                    <span>Placed ahead of normal-priority patients.</span>
                </div>
                <div class="guide-tile blue">
                    <strong>🔵 Normal</strong>
                    <span>Standard queue order.</span>
                </div>
            </div>
            <div class="note">This is a demonstration queue, not a clinical
            triage system. Real emergencies must follow hospital emergency
            procedures.</div>
            """),
            unsafe_allow_html=True
        )