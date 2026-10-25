import html
import streamlit as st
import pandas as pd
from pathlib import Path

from hospital_data import initialize_data
from consultation import auto_check_consultation_flow

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="MediCare | Hospital Management",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ---------------- CSS ----------------

def load_css():
    css_file = Path(__file__).parent / "assets" / "style.css"

    if css_file.exists():
        st.markdown(
            f"<style>{css_file.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True
        )


load_css()
initialize_data()
auto_check_consultation_flow()

# Active consultation alert
active_alert = st.session_state.pop("_consultation_alert", None)
if active_alert:
    st.info(active_alert, icon="🔔")

patients = st.session_state.patients
doctors = st.session_state.doctors
appointments = st.session_state.appointments

today = pd.Timestamp.today().date()

today_appointments = appointments[
    appointments["Date"] == today
].copy()

waiting = len(today_appointments[today_appointments["Status"] == "Waiting"])
consulting = len(
    today_appointments[today_appointments["Status"] == "In Consultation"]
)
completed = len(
    today_appointments[today_appointments["Status"] == "Completed"]
)

# Logged-in user shown in the header.
USER_NAME = "Hospital Admin"
USER_ROLE = "Administrator"
USER_INITIALS = "HA"

DEPARTMENTS = [
    "Cardiology", "Neurology", "Orthopedics",
    "General Medicine", "Dermatology", "Pediatrics"
]

PRIORITY_STYLE = {"Normal": "blue", "High": "red", "Medium": "amber",
                  "Low": "grey", "Emergency": "red"}
STATUS_STYLE = {"Waiting": "orange", "In Consultation": "purple",
                "Scheduled": "green", "Completed": "green",
                "Cancelled": "grey"}


def esc(value):
    return html.escape(str(value))


def panel_heading(icon, title, subtitle):
    st.markdown(
        f"""
        <div class="panel-heading">
            <div class="panel-icon">{icon}</div>
            <div>
                <h3>{title}</h3>
                <p>{subtitle}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ---------------- SIDEBAR ----------------

with st.sidebar:

    st.markdown("""
    <div class="brand">
        <div class="brand-symbol">✚</div>
        <div>
            <div class="brand-title">Medi<span>Care</span></div>
            <div class="brand-caption">HOSPITAL MANAGEMENT</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="nav-caption">WORKSPACE</div>',
                unsafe_allow_html=True)

    st.page_link("app.py", label="Dashboard", icon="🏠")
    st.page_link("pages/1_Appointments.py",
                 label="Appointments", icon="📅")
    st.page_link("pages/2_Patients.py",
                 label="Patients", icon="👥")
    st.page_link("pages/3_Doctors.py",
                 label="Doctors", icon="🩺")
    st.page_link("pages/4_Waiting_Queue.py",
                 label="Waiting Queue", icon="⏳")
    st.page_link("pages/5_Reports.py",
                 label="Reports", icon="📊")

    st.markdown("""
    <div class="sidebar-message">
        <div class="heart-icon">♡</div>
        <div>
            <strong>Better Care.</strong><br>
            Healthier Tomorrow.
        </div>
    </div>

    <div class="sidebar-status">
        <span class="online-dot"></span>
        C Backend Active
        <span>•</span>
        Hash Table &amp; Min-Heap
    </div>
    """, unsafe_allow_html=True)


# ---------------- HEADER ----------------

header, right_column = st.columns([3, 2])

with header:
    st.markdown(
        '<div class="eyebrow">HOSPITAL OVERVIEW</div>',
        unsafe_allow_html=True
    )
    st.markdown('<h1 class="dashboard-title">Dashboard</h1>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Monitor appointments, patient flow '
        'and hospital activity in real time · <span class="pill green">● Live</span></div>',
        unsafe_allow_html=True
    )

with right_column:
    st.markdown(
        f"""
        <div class="header-right">
            <div class="date-card">
                <span>▦</span>
                <div>
                    <strong>{today.strftime("%d %b %Y")}</strong>
                    <small>{today.strftime("%A")}</small>
                </div>
            </div>
            <div class="header-divider"></div>
            <div class="profile">
                <div class="avatar">{esc(USER_INITIALS)}</div>
                <div>
                    <strong>{esc(USER_NAME)}</strong>
                    <small>{esc(USER_ROLE)}</small>
                </div>
                <span class="chevron">⌄</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ---------------- KPI CARDS ----------------

st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

kpis = [
    ("Total Patients", len(patients), "Registered patients",
     "👥", "blue", "live total"),
    ("Today's Appointments", len(today_appointments),
     "Appointments scheduled today", "▦", "purple", "today's visits"),
    ("Waiting Patients", waiting, "Currently in waiting queue",
     "⌛", "orange", "in queue"),
    ("Active Consultations", consulting, "Patients with doctors",
     "⚕", "green", "active now")
]

columns = st.columns(4, gap="medium")

for column, item in zip(columns, kpis):
    label, value, description, symbol, color, compare = item

    with column:
        st.markdown(
            f"""
            <div class="kpi-card {color}">
                <div class="kpi-decoration"></div>
                <div class="kpi-body">
                    <div class="kpi-icon">{symbol}</div>
                    <div>
                        <div class="kpi-label">{label}</div>
                        <div class="kpi-value">{value}</div>
                    </div>
                </div>
                <div class="kpi-footer">
                    <div class="kpi-description">{description}</div>
                    <div class="kpi-trend"><small>{compare}</small></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


# ---------------- APPOINTMENTS + QUEUE ----------------

st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

left, right = st.columns([1.75, 1], gap="medium")

with left:
    with st.container(border=True):
        title_col, button_col = st.columns([4, 1])
        with title_col:
            panel_heading("▦", "Recent Appointments",
                          "Latest patient appointment records")
        with button_col:
            if st.button("View All  ›", key="hdr_all_appointments"):
                st.switch_page("pages/1_Appointments.py")

        if appointments.empty:
            st.info("No appointments have been added yet.")
        else:
            display = appointments.tail(6)

            rows = ""
            for _, row in display.iterrows():
                status = str(row.get("Status", ""))
                priority = str(row.get("Priority", ""))
                status_color = STATUS_STYLE.get(status, "grey")
                dot_color = {"orange": "orange", "purple": "purple",
                             "green": "green"}.get(status_color, "grey")
                priority_color = PRIORITY_STYLE.get(priority, "grey")

                rows += f"""
                <tr>
                    <td><span class="row-dot dot-{dot_color}"></span></td>
                    <td>{esc(row.get("Token", ""))}</td>
                    <td>{esc(row.get("Patient", ""))}</td>
                    <td>{esc(row.get("Doctor", ""))}</td>
                    <td>{esc(row.get("Department", ""))}</td>
                    <td>{esc(row.get("Time", ""))}</td>
                    <td><span class="pill {priority_color}">{esc(priority)}</span></td>
                    <td><span class="pill {status_color}">{esc(status)}</span></td>
                </tr>
                """

            st.markdown(
                f"""
                <table class="appt-table">
                    <thead>
                        <tr>
                            <th></th><th>Token</th><th>Patient</th>
                            <th>Doctor</th><th>Department</th><th>Time</th>
                            <th>Priority</th><th>Status</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
                """,
                unsafe_allow_html=True
            )


with right:
    with st.container(border=True):
        title_col, button_col = st.columns([3, 2])
        with title_col:
            panel_heading("⌛", "Patients Overview", "Today's patient flow")
        with button_col:
            if st.button("View Queue  ›", key="hdr_view_queue"):
                st.switch_page("pages/4_Waiting_Queue.py")

        queue_items = [
            ("Waiting", waiting, "In queue", "orange", "⌛"),
            ("In Consultation", consulting, "With doctors",
             "purple", "⚕"),
            ("Completed", completed, "Finished today", "green", "✓")
        ]

        for label, count, description, color, symbol in queue_items:
            st.markdown(
                f"""
                <div class="queue-row">
                    <div class="queue-icon {color}">{symbol}</div>
                    <div class="queue-content">
                        <strong>{label}</strong>
                        <small>{description}</small>
                        <div class="queue-track">
                            <div class="queue-fill {color}"
                                 style="width:{min(count * 35, 100)}%">
                            </div>
                        </div>
                    </div>
                    <div class="queue-count">{count}</div>
                </div>
                """,
                unsafe_allow_html=True
            )


# ---------------- DEPARTMENT CHART + QUICK ACTIONS ----------------

st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

chart_column, actions_column = st.columns([1.75, 1], gap="medium")

with chart_column:
    with st.container(border=True):
        title_col, button_col = st.columns([4, 1])
        with title_col:
            panel_heading("▥", "Department Overview",
                          "Appointment distribution across departments")
        with button_col:
            if st.button("View Reports  ›", key="hdr_view_reports"):
                st.switch_page("pages/5_Reports.py")

        counts = {name: 0 for name in DEPARTMENTS}
        if not appointments.empty and "Department" in appointments.columns:
            for name, number in appointments["Department"].value_counts().items():
                counts[name] = int(number)

        axis_max = max(2, max(counts.values()))
        bar_area = 110  # pixels available for the tallest bar

        columns_html = ""
        labels_html = ""
        for index, (name, number) in enumerate(counts.items()):
            if number:
                height = max(8, round(number / axis_max * bar_area))
                bar = (f'<div class="dept-bar b{index % 6}" '
                       f'style="height:{height}px"></div>')
            else:
                bar = '<div class="dept-bar zero"></div>'

            columns_html += (
                f'<div class="dept-col">'
                f'<div class="dept-count">{number}</div>{bar}</div>'
            )
            labels_html += f"<span>{esc(name)}</span>"

        grid_step = bar_area / 2
        st.markdown(
            f"""
            <div class="dept-chart"
                 style="background: repeating-linear-gradient(to top,
                 #edf1f9 0, #edf1f9 1px, transparent 1px,
                 transparent {grid_step}px);">
                {columns_html}
            </div>
            <div class="dept-labels">{labels_html}</div>
            """,
            unsafe_allow_html=True
        )


with actions_column:
    with st.container(border=True):
        panel_heading("ϟ", "Quick Actions",
                      "Frequently used hospital operations")

        a, b, c = st.columns(3, gap="small")

        with a:
            if st.button("New Appointment\n\nBook a patient appointment  →",
                         key="qa_book", icon="📅",
                         use_container_width=True):
                st.switch_page("pages/1_Appointments.py")

        with b:
            if st.button("Register Patient\n\nAdd a new patient  →",
                         key="qa_patient", icon="👤",
                         use_container_width=True):
                st.switch_page("pages/2_Patients.py")

        with c:
            if st.button("View Doctors\n\nBrowse doctor profiles  →",
                         key="qa_doctors", icon="🩺",
                         use_container_width=True):
                st.switch_page("pages/3_Doctors.py")


# ---------------- FOOTER ----------------

st.markdown("""
<div class="footer">
    MediCare Hospital Management System
    <span>•</span>
    Academic Project
    <div class="footer-tagline">Care that counts.</div>
</div>
""", unsafe_allow_html=True)