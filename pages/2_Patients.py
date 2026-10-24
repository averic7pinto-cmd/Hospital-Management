import streamlit as st
import pandas as pd
from hospital_data import initialize_data
from ui import (
    setup_page, hero, panel_heading, patient_cards, chip_filter,
    h_bars, donut, flash, HEX
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
    "Register patients and manage patient information."
)

patients = st.session_state.patients

# ---------------- HERO ----------------

average_age = (
    f"{patients['Age'].mean():.0f}" if not patients.empty else "–"
)

hero(
    "👥",
    "Every patient, one place",
    "Register new patients, search the directory and keep contact "
    "and blood-group details at hand.",
    [
        ("Registered", len(patients)),
        ("Male", len(patients[patients["Gender"] == "Male"])),
        ("Female", len(patients[patients["Gender"] == "Female"])),
        ("Avg. age", average_age),
    ]
)

tab_directory, tab_register = st.tabs(
    ["👥  Patient Directory", "➕  Register Patient"]
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

    patients = st.session_state.patients
    filtered = patients.copy()

    if gender_filter != "All":
        filtered = filtered[filtered["Gender"] == gender_filter]

    if search.strip():
        mask = (
            filtered["Name"].str.contains(search, case=False, na=False)
            | filtered["Patient ID"].str.contains(
                search, case=False, na=False)
            | filtered["Phone"].astype(str).str.contains(
                search, case=False, na=False)
        )
        filtered = filtered[mask]

    st.caption(f"Showing {len(filtered)} of {len(patients)} patients · "
               "demo records are not saved to a database")

    patient_cards(filtered, empty_text="No patients match your search.")

# ---------------- REGISTER ----------------

with tab_register:
    form_col, overview_col = st.columns([1.15, 1], gap="large")

    with form_col:
        with st.container(border=True):
            panel_heading("➕", "Register a New Patient",
                          "Add a patient to the hospital records")

            with st.form("patient_form", clear_on_submit=True):
                name = st.text_input("Full Name")

                col1, col2 = st.columns(2)

                with col1:
                    age = st.number_input(
                        "Age",
                        min_value=0,
                        max_value=120,
                        value=18
                    )

                    gender = st.selectbox(
                        "Gender",
                        ["Male", "Female", "Other"]
                    )

                with col2:
                    phone = st.text_input(
                        "Phone Number",
                        max_chars=15
                    )

                    blood_group = st.selectbox(
                        "Blood Group",
                        ["Unknown", "A+", "A-", "B+", "B-",
                         "AB+", "AB-", "O+", "O-"]
                    )

                submitted = st.form_submit_button(
                    "Register Patient",
                    type="primary",
                    use_container_width=True
                )

                if submitted:
                    if not name.strip():
                        st.error("Please enter the patient's name.")
                    elif not phone.strip():
                        st.error("Please enter a phone number.")
                    elif not phone.strip().replace("+", "").isdigit():
                        st.error(
                            "Enter a valid phone number using digits "
                            "and an optional +."
                        )
                    elif patients["Phone"].astype(str).eq(
                            phone.strip()).any():
                        st.error("This phone number is already registered.")
                    else:
                        patient_id = f"P-{1001 + len(patients)}"

                        new_patient = {
                            "Patient ID": patient_id,
                            "Name": name.strip(),
                            "Age": int(age),
                            "Gender": gender,
                            "Phone": phone.strip(),
                            "Blood Group": blood_group
                        }

                        st.session_state.patients = pd.concat(
                            [
                                st.session_state.patients,
                                pd.DataFrame([new_patient])
                            ],
                            ignore_index=True
                        )

                        flash(
                            "Patient registered successfully! "
                            f"ID: {patient_id}"
                        )
                        st.rerun()

    with overview_col:
        with st.container(border=True):
            panel_heading("📊", "Patient Overview",
                          "Who is registered right now")

            gender_counts = st.session_state.patients["Gender"].value_counts()
            donut(
                gender_counts,
                colors={"Male": HEX["blue"], "Female": HEX["purple"],
                        "Other": HEX["grey"]},
                center_label="Patients",
                empty_text="Register a patient to see the breakdown."
            )

        with st.container(border=True):
            panel_heading("🩸", "Blood Groups", "Known blood groups on file")

            blood_counts = st.session_state.patients["Blood Group"] \
                .value_counts()
            h_bars(
                blood_counts,
                colors={group: HEX["red"] for group in blood_counts.index},
                empty_text="No blood-group data yet."
            )