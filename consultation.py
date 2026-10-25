"""
Consultation Lifecycle & Queue Progression Engine.

Data Structures Used:
1. Priority Min-Heap (appointments.c):
   - Orders appointments chronologically by Date, Time, and Emergency/High/Normal priority.
   - Ensures the highest-priority/earliest patient is always at the root of the heap (O(1) peek).

2. FIFO Waiting Queue per Doctor:
   - For each doctor, waiting patients queue sequentially in priority order.

3. Time-Interval Consultation Slot:
   - Each consultation occupies a time block [Start Time, Start Time + Duration].
   - While active, Doctor is Busy, and Patient is In Consultation.
   - When duration (e.g. 30 mins) expires, the consultation auto-completes,
     the doctor is freed, and the next patient in the Priority Queue is called!
"""

from datetime import datetime, date, time, timedelta
import pandas as pd
import streamlit as st
import c_backend


DEFAULT_DURATION_MINS = 30


def parse_time_str(time_str: str) -> time:
    """Parse HH:MM string into time object."""
    try:
        parts = time_str.strip().split(":")
        h = int(parts[0])
        m = int(parts[1][:2])
        return time(h, m)
    except Exception:
        return time(9, 0)


def get_consultation_window(time_str: str, duration_mins: int = DEFAULT_DURATION_MINS, appt_date: date = None) -> tuple[datetime, datetime, str]:
    """Calculate start_dt, end_dt, and formatted end_time string."""
    d = appt_date or date.today()
    t = parse_time_str(time_str)
    start_dt = datetime.combine(d, t)
    end_dt = start_dt + timedelta(minutes=duration_mins)
    end_time_str = end_dt.strftime("%H:%M")
    return start_dt, end_dt, end_time_str


def auto_check_consultation_flow():
    """
    Check today's appointments against the current time:
    - If scheduled time has arrived and patient is Waiting -> trigger Call Alert & transition to In Consultation
    - If 30-min consultation window has expired and patient is In Consultation -> transition to Completed & call next!
    """
    if not c_backend.is_backend_available():
        return

    appts = c_backend.get_all_appointments()
    today = date.today()
    now = datetime.now()

    updated = False

    for a in appts:
        token = a["Token"]
        status = a["Status"]
        pat_date = a["Date"]
        time_str = a["Time"]
        patient = a["Patient"]
        doctor = a["Doctor"]

        # Only check today's active appointments
        if pat_date != today or status in ("Completed", "Cancelled"):
            continue

        start_dt, end_dt, end_time_str = get_consultation_window(time_str, DEFAULT_DURATION_MINS, today)

        # 1. Has the consultation time arrived for a waiting patient?
        if status in ("Waiting", "Scheduled") and start_dt <= now < end_dt:
            # Check if this doctor is already in consultation with someone else
            doc_busy = any(
                other["Doctor"] == doctor and other["Status"] == "In Consultation" and other["Token"] != token
                for other in appts
            )
            if not doc_busy:
                c_backend.update_appointment_status(token, "In Consultation")
                st.session_state["_consultation_alert"] = (
                    f"🔔 ALERT ({time_str}): Patient {patient} is now called for consultation with {doctor}! "
                    f"(Scheduled session: {time_str} – {end_time_str})"
                )
                updated = True

        # 2. Has the 30-minute consultation window expired for an in-consultation patient?
        elif status == "In Consultation" and now >= end_dt:
            c_backend.update_appointment_status(token, "Completed")
            st.session_state["_consultation_alert"] = (
                f"✅ Consultation finished for {patient} with {doctor} (Session {time_str}–{end_time_str} complete). "
                f"Calling next patient in queue!"
            )
            updated = True

    if updated:
        # Refresh session state
        st.session_state.appointments = c_backend.get_appointments_df()


def call_patient_now(token: str, patient_name: str, doctor_name: str, duration_mins: int = DEFAULT_DURATION_MINS):
    """Manually start consultation right now for a waiting patient."""
    now = datetime.now()
    now_time_str = now.strftime("%H:%M")
    end_dt = now + timedelta(minutes=duration_mins)
    end_time_str = end_dt.strftime("%H:%M")

    ok, msg = c_backend.update_appointment_status(token, "In Consultation")
    if ok:
        st.session_state.appointments = c_backend.get_appointments_df()
        st.session_state["_consultation_alert"] = (
            f"🔔 CALLED: {patient_name} has entered consultation with {doctor_name}! "
            f"(Consultation active: {now_time_str} – {end_time_str}, {duration_mins} mins)"
        )
        return True, "Consultation started"
    return False, msg


def complete_consultation_now(token: str, patient_name: str, doctor_name: str):
    """Manually complete consultation, free doctor, and alert the next patient."""
    ok, msg = c_backend.update_appointment_status(token, "Completed")
    if ok:
        st.session_state.appointments = c_backend.get_appointments_df()

        # Check who is next in line for this doctor in the Priority Min-Heap
        appts = c_backend.get_all_appointments()
        next_pat = None
        for a in appts:
            if a["Doctor"] == doctor_name and a["Status"] == "Waiting" and a["Date"] == date.today():
                next_pat = a
                break

        if next_pat:
            alert = (
                f"✅ Completed consultation for {patient_name}. "
                f"📢 NEXT UP: Calling {next_pat['Patient']} for {doctor_name}!"
            )
        else:
            alert = f"✅ Completed consultation for {patient_name}. Doctor {doctor_name} has no more waiting patients."

        st.session_state["_consultation_alert"] = alert
        return True, alert
    return False, msg

