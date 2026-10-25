"""Shared look & feel for every MediCare page (CSS, sidebar, header, widgets)."""

import html
import re
from pathlib import Path

import pandas as pd
import streamlit as st

# Logged-in user shown in the header.
USER_NAME = "Hospital Admin"
USER_ROLE = "Administrator"
USER_INITIALS = "HA"

PRIORITY_STYLE = {"Normal": "blue", "High": "red", "Medium": "amber",
                  "Low": "grey", "Emergency": "red"}
STATUS_STYLE = {"Waiting": "orange", "In Consultation": "purple",
                "Scheduled": "blue", "Completed": "green",
                "Cancelled": "grey"}
AVAILABILITY_STYLE = {"Available": "green", "Busy": "orange"}
GENDER_STYLE = {"Male": "blue", "Female": "purple", "Other": "grey"}


# ---------------------------------------------------------------- helpers

def esc(value):
    return html.escape(str(value))


def html_block(markup):
    """Collapse whitespace between tags so Markdown never treats
    indented HTML (or blank lines) as a code block."""
    return re.sub(r">\s+<", "><", markup).strip()


def flash(message, kind="success"):
    """Queue a message that survives the next st.rerun()."""
    st.session_state["_flash"] = (kind, message)


def show_flash():
    pending = st.session_state.pop("_flash", None)
    if pending:
        kind, message = pending
        getattr(st, kind)(message)


# -------------------------------------------------------------------- css

def load_css():
    css_file = Path(__file__).parent / "assets" / "style.css"

    if css_file.exists():
        st.markdown(
            f"<style>{css_file.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True
        )


# ---------------------------------------------------------------- sidebar

def render_sidebar():
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


# ----------------------------------------------------------------- header

def render_header(eyebrow, title, subtitle):
    today = pd.Timestamp.today().date()
    left, right = st.columns([3, 2])

    with left:
        st.markdown(
            f'<div class="eyebrow">{esc(eyebrow)}</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<h1 class="dashboard-title">{esc(title)}</h1>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="subtitle">{esc(subtitle)}</div>',
            unsafe_allow_html=True
        )

    with right:
        st.markdown(
            html_block(f"""
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
            """),
            unsafe_allow_html=True
        )

    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)


def setup_page(eyebrow, title, subtitle):
    """Call right after st.set_page_config() on every page."""
    load_css()
    render_sidebar()
    render_header(eyebrow, title, subtitle)
    show_flash()


def gap():
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- widgets

def panel_heading(icon, title, subtitle=""):
    sub = f"<p>{esc(subtitle)}</p>" if subtitle else ""
    st.markdown(
        html_block(f"""
        <div class="panel-heading">
            <div class="panel-icon">{icon}</div>
            <div><h3>{esc(title)}</h3>{sub}</div>
        </div>
        """),
        unsafe_allow_html=True
    )


def kpi_cards(items):
    """items: (label, value, description, symbol, color) — color is one of
    blue / purple / orange / green."""
    columns = st.columns(len(items), gap="medium")

    for column, (label, value, description, symbol, color) in zip(
            columns, items):
        with column:
            st.markdown(
                html_block(f"""
                <div class="kpi-card {color}">
                    <div class="kpi-decoration"></div>
                    <div class="kpi-body">
                        <div class="kpi-icon">{symbol}</div>
                        <div>
                            <div class="kpi-label">{esc(label)}</div>
                            <div class="kpi-value">{esc(value)}</div>
                        </div>
                    </div>
                    <div class="kpi-footer">
                        <div class="kpi-description">{esc(description)}</div>
                    </div>
                </div>
                """),
                unsafe_allow_html=True
            )


def data_table(df, pills=None, max_height=380, empty_text="No records found."):
    """Styled HTML table. pills = {column: {value: colour}} renders those
    columns as coloured badges."""
    if df.empty:
        st.markdown(
            f'<div class="empty-state">{esc(empty_text)}</div>',
            unsafe_allow_html=True
        )
        return

    pills = pills or {}
    head = "".join(f"<th>{esc(c)}</th>" for c in df.columns)

    body = ""
    for _, row in df.iterrows():
        cells = ""
        for column in df.columns:
            value = row[column]
            if column in pills:
                color = pills[column].get(str(value), "grey")
                cells += (f'<td><span class="pill {color}">'
                          f'{esc(value)}</span></td>')
            else:
                cells += f"<td>{esc(value)}</td>"
        body += f"<tr>{cells}</tr>"

    st.markdown(
        html_block(
            f'<div class="table-scroll" style="max-height:{max_height}px">'
            f'<table class="data-table"><thead><tr>{head}</tr></thead>'
            f'<tbody>{body}</tbody></table></div>'
        ),
        unsafe_allow_html=True
    )


def pill(text, color):
    return f'<span class="pill {color}">{esc(text)}</span>'


def initials(name):
    words = [w for w in str(name).replace("Dr.", "").split() if w]
    return "".join(w[0] for w in words[:2]).upper() or "DR"


# ======================================================================
#  Richer visual components (hero banner, card grids, charts, filters)
# ======================================================================

HEX = {"blue": "#4361ee", "purple": "#8a4fe9", "orange": "#ff9c20",
       "green": "#1db981", "red": "#ee5370", "amber": "#f5b83d",
       "grey": "#9aa8c2"}
PALETTE = ["#4361ee", "#8a4fe9", "#1db981", "#ff9c20", "#ee5370", "#2aa6cf"]
BANNERS = [("#2a3fc9", "#5a79ff"), ("#6a3fd8", "#a77bf6"),
           ("#0f9d78", "#4fd2a4"), ("#e5810f", "#ffbf5e"),
           ("#d93f63", "#ff8fa3"), ("#1b8db8", "#5ecbe8")]


def hex_for(style_map, labels):
    """{label: hex colour} for a pill style map such as STATUS_STYLE."""
    return {str(l): HEX[style_map.get(str(l), "grey")] for l in labels}


def hero(icon, heading, text, stats):
    """Gradient banner with glass stat chips. stats = [(label, value)]."""
    chips = "".join(
        f'<div class="hero-stat"><strong>{esc(value)}</strong>'
        f'<small>{esc(label)}</small></div>'
        for label, value in stats
    )
    st.markdown(
        html_block(f"""
        <div class="hero">
            <div class="hero-text">
                <div class="hero-icon">{icon}</div>
                <h2>{esc(heading)}</h2>
                <p>{esc(text)}</p>
            </div>
            <div class="hero-stats">{chips}</div>
        </div>
        """),
        unsafe_allow_html=True
    )


def chip_filter(label, options, key):
    """Pill-style single choice filter."""
    if hasattr(st, "pills"):
        choice = st.pills(label, options, default=options[0], key=key,
                          label_visibility="collapsed")
        return choice or options[0]
    return st.radio(label, options, horizontal=True, key=key,
                    label_visibility="collapsed")


def card_grid(cards, min_width=270, empty_text="Nothing to show yet."):
    if not cards:
        st.markdown(f'<div class="empty-state">{esc(empty_text)}</div>',
                    unsafe_allow_html=True)
        return
    st.markdown(
        html_block(
            f'<div class="card-grid" style="--min:{min_width}px">'
            + "".join(cards) + "</div>"
        ),
        unsafe_allow_html=True
    )


def appointment_cards(df, empty_text="No appointments found."):
    cards = []
    for _, r in df.iterrows():
        stripe = PRIORITY_STYLE.get(str(r["Priority"]), "grey")
        cards.append(f"""
        <div class="item-card stripe-{stripe}">
            <div class="item-top">
                <span class="token">{esc(r['Token'])}</span>
                {pill(r['Status'], STATUS_STYLE.get(str(r['Status']), 'grey'))}
            </div>
            <div class="item-name">{esc(r['Patient'])}</div>
            <div class="item-sub">with {esc(r['Doctor'])} · {esc(r['Department'])}</div>
            <div class="item-foot">
                <span>📅 {esc(r['Date'])}</span>
                <span>🕘 {esc(r['Time'])}</span>
                {pill(r['Priority'], stripe)}
            </div>
        </div>
        """)
    card_grid(cards, 290, empty_text)


def patient_cards(df, empty_text="No patients found."):
    cards = []
    for _, r in df.iterrows():
        gender = str(r["Gender"])
        cards.append(f"""
        <div class="item-card person">
            <div class="avatar-lg {gender.lower()}">{esc(initials(r['Name']))}</div>
            <div class="person-info">
                <strong>{esc(r['Name'])}</strong>
                <small>{esc(r['Patient ID'])} · {esc(r['Age'])} yrs</small>
                <div class="person-tags">
                    {pill(gender, GENDER_STYLE.get(gender, 'grey'))}
                    <span class="phone">📞 {esc(r['Phone'])}</span>
                </div>
            </div>
            <div class="bg-badge">{esc(r['Blood Group'])}</div>
        </div>
        """)
    card_grid(cards, 320, empty_text)


def doctor_cards(df, empty_text="No doctors match the filters."):
    cards = []
    for i, (_, r) in enumerate(df.iterrows()):
        c1, c2 = BANNERS[i % len(BANNERS)]
        availability = str(r["Availability"])
        color = AVAILABILITY_STYLE.get(availability, "grey")
        cards.append(f"""
        <div class="doc2">
            <div class="doc2-banner" style="background:linear-gradient(120deg,{c1},{c2})"></div>
            <div class="doc-avatar" style="background:linear-gradient(135deg,{c1},{c2})">{esc(initials(r['Name']))}</div>
            <strong>{esc(r['Name'])}</strong>
            <small>{esc(r['Department'])}</small>
            <div class="doc2-meta">
                <div><span>ID</span><b>{esc(r['Doctor ID'])}</b></div>
                <div><span>Fee</span><b>₹{esc(r['Consultation Fee'])}</b></div>
            </div>
            {pill('● ' + availability, color)}
        </div>
        """)
    card_grid(cards, 230, empty_text)


def queue_cards(waiting_df, minutes_per_patient=15):
    """Ordered list of waiting patients (already sorted by priority)."""
    if waiting_df.empty:
        st.markdown('<div class="empty-state">🎉 No patients are '
                    'currently waiting.</div>', unsafe_allow_html=True)
        return

    cards = ""
    for position, (_, r) in enumerate(waiting_df.iterrows(), start=1):
        stripe = PRIORITY_STYLE.get(str(r["Priority"]), "grey")
        nxt = " next" if position == 1 else ""
        badge = '<span class="next-chip">NEXT UP</span>' if position == 1 else ""
        wait = (position - 1) * minutes_per_patient
        wait_text = "Now" if wait == 0 else f"{wait} min"
        cards += f"""
        <div class="queue-card stripe-{stripe}{nxt}">
            <div class="q-pos">{position}</div>
            <div class="q-main">
                <strong>{esc(r['Patient'])} {badge}</strong>
                <small>{esc(r['Token'])} · {esc(r['Doctor'])} · {esc(r['Department'])}</small>
            </div>
            {pill(r['Priority'], stripe)}
            <div class="q-wait"><strong>{wait_text}</strong><small>est. wait</small></div>
        </div>
        """
    st.markdown(html_block(cards), unsafe_allow_html=True)


def h_bars(counts, colors=None, empty_text="No data yet."):
    """Horizontal progress-style bars from a Series of counts."""
    if counts is None or len(counts) == 0:
        st.markdown(f'<div class="empty-state">{esc(empty_text)}</div>',
                    unsafe_allow_html=True)
        return

    top = max(int(counts.max()), 1)
    rows = ""
    for i, (label, value) in enumerate(counts.items()):
        color = (colors or {}).get(str(label)) or PALETTE[i % len(PALETTE)]
        rows += f"""
        <div class="hbar">
            <div class="hbar-top"><span>{esc(label)}</span><strong>{int(value)}</strong></div>
            <div class="hbar-track"><div class="hbar-fill"
                 style="width:{value / top * 100:.0f}%;background:{color}"></div></div>
        </div>
        """
    st.markdown(html_block(f'<div class="hbars">{rows}</div>'),
                unsafe_allow_html=True)


def donut(counts, colors=None, center_label="Total", empty_text="No data yet."):
    """CSS donut chart with a legend, from a Series of counts."""
    if counts is None or len(counts) == 0 or counts.sum() == 0:
        st.markdown(f'<div class="empty-state">{esc(empty_text)}</div>',
                    unsafe_allow_html=True)
        return

    total = int(counts.sum())
    stops, legend, accumulated = [], "", 0
    for i, (label, value) in enumerate(counts.items()):
        color = (colors or {}).get(str(label)) or PALETTE[i % len(PALETTE)]
        start = accumulated / total * 100
        accumulated += value
        end = accumulated / total * 100
        stops.append(f"{color} {start:.2f}% {end:.2f}%")
        legend += f"""
        <div class="legend-row">
            <span class="legend-dot" style="background:{color}"></span>
            {esc(label)}<strong>{int(value)}</strong>
            <em>{value / total * 100:.0f}%</em>
        </div>
        """

    st.markdown(
        html_block(f"""
        <div class="donut-wrap">
            <div class="donut" style="background:conic-gradient({', '.join(stops)})">
                <div class="donut-hole"><strong>{total}</strong>
                <small>{esc(center_label)}</small></div>
            </div>
            <div class="legend">{legend}</div>
        </div>
        """),
        unsafe_allow_html=True
    )