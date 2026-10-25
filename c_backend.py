"""
C Backend Adapter for Hospital Management System.
Connects Python (Streamlit frontend) to C DLL modules:
- patients.dll: Hash table (open addressing) + CSV persistence
- appointments.dll: Min-heap (priority queue) + CSV persistence
"""

import ctypes
import os
import sys
from datetime import date, datetime
from pathlib import Path
import pandas as pd

# Directory where DLLs are located
BASE_DIR = Path(__file__).resolve().parent

# Buffer sizes matching C headers
ID_LEN = 24
NAME_LEN = 100
GENDER_LEN = 16
PHONE_LEN = 20
BLOOD_LEN = 8

TOKEN_LEN = 24
PERSON_LEN = 100
DEPT_LEN = 64
DATE_LEN = 16
TIME_LEN = 16
PRIORITY_LEN = 16
STATUS_LEN = 24

_patients_lib = None
_appointments_lib = None
_init_error = None


def _load_library(name: str):
    """Load DLL on Windows or .so/.dylib on Linux/macOS."""
    # Ensure current directory and msys64/ucrt64/bin (if on Windows) are in DLL search path
    if sys.platform == "win32":
        try:
            os.add_dll_directory(str(BASE_DIR))
        except (AttributeError, OSError):
            pass

    # Potential filenames
    filenames = [f"{name}.dll", f"lib{name}.dll", f"{name}.so", f"lib{name}.so", f"{name}.dylib"]
    for fname in filenames:
        path = BASE_DIR / fname
        if path.exists():
            return ctypes.CDLL(str(path))
    
    # Try default lookup
    return ctypes.CDLL(name)


def init_backend():
    """Initialize ctypes bindings for patients and appointments C modules."""
    global _patients_lib, _appointments_lib, _init_error
    if _patients_lib is not None and _appointments_lib is not None:
        return True

    try:
        # Load patients DLL
        p_lib = _load_library("patients")
        p_lib.patients_init.argtypes = []
        p_lib.patients_init.restype = None

        p_lib.patients_count.argtypes = []
        p_lib.patients_count.restype = ctypes.c_int

        p_lib.patients_get_at.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_int),
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
        ]
        p_lib.patients_get_at.restype = ctypes.c_int

        p_lib.patients_find.argtypes = [
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_int),
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
        ]
        p_lib.patients_find.restype = ctypes.c_int

        p_lib.patients_add.argtypes = [
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
        ]
        p_lib.patients_add.restype = ctypes.c_int

        p_lib.patients_update.argtypes = [
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
        ]
        p_lib.patients_update.restype = ctypes.c_int

        p_lib.patients_delete.argtypes = [ctypes.c_char_p]
        p_lib.patients_delete.restype = ctypes.c_int

        p_lib.patients_init()
        _patients_lib = p_lib

        # Load appointments DLL
        a_lib = _load_library("appointments")
        a_lib.appointments_init.argtypes = []
        a_lib.appointments_init.restype = None

        a_lib.appointments_count.argtypes = []
        a_lib.appointments_count.restype = ctypes.c_int

        a_lib.appointments_get_at.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
        ]
        a_lib.appointments_get_at.restype = ctypes.c_int

        a_lib.appointments_add.argtypes = [
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
        ]
        a_lib.appointments_add.restype = ctypes.c_int

        a_lib.appointments_update_status.argtypes = [
            ctypes.c_char_p,
            ctypes.c_char_p,
        ]
        a_lib.appointments_update_status.restype = ctypes.c_int

        a_lib.appointments_cancel.argtypes = [ctypes.c_char_p]
        a_lib.appointments_cancel.restype = ctypes.c_int

        a_lib.appointments_delete.argtypes = [ctypes.c_char_p]
        a_lib.appointments_delete.restype = ctypes.c_int

        a_lib.appointments_delete_by_patient.argtypes = [ctypes.c_char_p]
        a_lib.appointments_delete_by_patient.restype = ctypes.c_int

        a_lib.appointments_init()
        _appointments_lib = a_lib

        _init_error = None
        return True
    except Exception as e:
        _init_error = str(e)
        return False


def is_backend_available() -> bool:
    """Return True if C libraries are loaded and ready."""
    return init_backend()


def get_backend_error():
    """Return initialization error message if any."""
    return _init_error


def get_patients_count() -> int:
    if not init_backend():
        return 0
    return _patients_lib.patients_count()


def get_all_patients() -> list[dict]:
    if not init_backend():
        return []

    count = _patients_lib.patients_count()
    records = []

    id_buf = ctypes.create_string_buffer(ID_LEN)
    name_buf = ctypes.create_string_buffer(NAME_LEN)
    age_val = ctypes.c_int()
    gender_buf = ctypes.create_string_buffer(GENDER_LEN)
    phone_buf = ctypes.create_string_buffer(PHONE_LEN)
    blood_buf = ctypes.create_string_buffer(BLOOD_LEN)

    for i in range(count):
        ok = _patients_lib.patients_get_at(
            i, id_buf, name_buf, ctypes.byref(age_val), gender_buf, phone_buf, blood_buf
        )
        if ok:
            records.append({
                "Patient ID": id_buf.value.decode("utf-8", errors="replace"),
                "Name": name_buf.value.decode("utf-8", errors="replace"),
                "Age": int(age_val.value),
                "Gender": gender_buf.value.decode("utf-8", errors="replace"),
                "Phone": phone_buf.value.decode("utf-8", errors="replace"),
                "Blood Group": blood_buf.value.decode("utf-8", errors="replace"),
            })
    return records


def get_patients_df() -> pd.DataFrame:
    records = get_all_patients()
    if not records:
        return pd.DataFrame(columns=[
            "Patient ID", "Name", "Age", "Gender", "Phone", "Blood Group"
        ])
    return pd.DataFrame(records)


def find_patient_by_id(patient_id: str) -> dict | None:
    """Search patient using C hash table O(1) lookup."""
    if not init_backend():
        return None

    id_buf = ctypes.create_string_buffer(ID_LEN)
    name_buf = ctypes.create_string_buffer(NAME_LEN)
    age_val = ctypes.c_int()
    gender_buf = ctypes.create_string_buffer(GENDER_LEN)
    phone_buf = ctypes.create_string_buffer(PHONE_LEN)
    blood_buf = ctypes.create_string_buffer(BLOOD_LEN)

    ok = _patients_lib.patients_find(
        patient_id.encode("utf-8"),
        id_buf, name_buf, ctypes.byref(age_val), gender_buf, phone_buf, blood_buf
    )
    if ok:
        return {
            "Patient ID": id_buf.value.decode("utf-8", errors="replace"),
            "Name": name_buf.value.decode("utf-8", errors="replace"),
            "Age": int(age_val.value),
            "Gender": gender_buf.value.decode("utf-8", errors="replace"),
            "Phone": phone_buf.value.decode("utf-8", errors="replace"),
            "Blood Group": blood_buf.value.decode("utf-8", errors="replace"),
        }
    return None


def add_patient(patient_id: str, name: str, age: int, gender: str, phone: str, blood_group: str) -> tuple[bool, str]:
    if not init_backend():
        return False, f"C backend unavailable: {_init_error}"

    code = _patients_lib.patients_add(
        patient_id.encode("utf-8"),
        name.encode("utf-8"),
        int(age),
        gender.encode("utf-8"),
        phone.encode("utf-8"),
        blood_group.encode("utf-8")
    )
    if code == 1:
        return True, "Patient registered successfully in C hash table!"
    elif code == -1:
        return False, "Invalid patient details provided."
    elif code == -2:
        return False, f"Patient ID '{patient_id}' already exists in C hash table."
    elif code == -3:
        return False, f"Phone number '{phone}' is already registered."
    return False, f"Failed to register patient (code {code})."


def delete_patient(patient_id: str) -> tuple[bool, str]:
    if not init_backend():
        return False, f"C backend unavailable: {_init_error}"

    code = _patients_lib.patients_delete(patient_id.encode("utf-8"))
    if code == 1:
        return True, f"Patient '{patient_id}' deleted from C hash table."
    return False, f"Patient '{patient_id}' not found."



def get_appointments_count() -> int:
    if not init_backend():
        return 0
    return _appointments_lib.appointments_count()


def get_all_appointments() -> list[dict]:
    if not init_backend():
        return []

    count = _appointments_lib.appointments_count()
    records = []

    token_buf = ctypes.create_string_buffer(TOKEN_LEN)
    patient_buf = ctypes.create_string_buffer(PERSON_LEN)
    doctor_buf = ctypes.create_string_buffer(PERSON_LEN)
    dept_buf = ctypes.create_string_buffer(DEPT_LEN)
    date_buf = ctypes.create_string_buffer(DATE_LEN)
    time_buf = ctypes.create_string_buffer(TIME_LEN)
    priority_buf = ctypes.create_string_buffer(PRIORITY_LEN)
    status_buf = ctypes.create_string_buffer(STATUS_LEN)

    for i in range(count):
        ok = _appointments_lib.appointments_get_at(
            i, token_buf, patient_buf, doctor_buf, dept_buf,
            date_buf, time_buf, priority_buf, status_buf
        )
        if ok:
            raw_date_str = date_buf.value.decode("utf-8", errors="replace")
            # Parse date to date object for pandas compatibility
            parsed_date = None
            try:
                parsed_date = datetime.strptime(raw_date_str, "%Y-%m-%d").date()
            except ValueError:
                parsed_date = date.today()

            records.append({
                "Token": token_buf.value.decode("utf-8", errors="replace"),
                "Patient": patient_buf.value.decode("utf-8", errors="replace"),
                "Doctor": doctor_buf.value.decode("utf-8", errors="replace"),
                "Department": dept_buf.value.decode("utf-8", errors="replace"),
                "Date": parsed_date,
                "Time": time_buf.value.decode("utf-8", errors="replace"),
                "Priority": priority_buf.value.decode("utf-8", errors="replace"),
                "Status": status_buf.value.decode("utf-8", errors="replace"),
            })
    return records


def get_appointments_df() -> pd.DataFrame:
    records = get_all_appointments()
    if not records:
        return pd.DataFrame(columns=[
            "Token", "Patient", "Doctor", "Department",
            "Date", "Time", "Priority", "Status"
        ])
    return pd.DataFrame(records)


def add_appointment(token: str, patient: str, doctor: str, department: str,
                    appointment_date, appointment_time, priority: str, status: str) -> tuple[bool, str]:
    if not init_backend():
        return False, f"C backend unavailable: {_init_error}"

    # Format date as YYYY-MM-DD
    if isinstance(appointment_date, (date, datetime)):
        date_str = appointment_date.strftime("%Y-%m-%d")
    else:
        date_str = str(appointment_date)

    # Format time as HH:MM
    if hasattr(appointment_time, "strftime"):
        time_str = appointment_time.strftime("%H:%M")
    else:
        time_str = str(appointment_time)

    code = _appointments_lib.appointments_add(
        token.encode("utf-8"),
        patient.encode("utf-8"),
        doctor.encode("utf-8"),
        department.encode("utf-8"),
        date_str.encode("utf-8"),
        time_str.encode("utf-8"),
        priority.encode("utf-8"),
        status.encode("utf-8")
    )

    if code == 1:
        return True, "Appointment booked and inserted into C priority min-heap!"
    elif code == -1:
        return False, "Invalid appointment details provided."
    elif code == -2:
        return False, f"Appointment token '{token}' already exists."
    elif code == -3:
        return False, f"Doctor '{doctor}' already has an appointment scheduled at {date_str} {time_str}."
    return False, f"Failed to add appointment (code {code})."


def update_appointment_status(token: str, new_status: str) -> tuple[bool, str]:
    if not init_backend():
        return False, f"C backend unavailable: {_init_error}"

    code = _appointments_lib.appointments_update_status(
        token.encode("utf-8"),
        new_status.encode("utf-8")
    )
    if code == 1:
        return True, f"Appointment '{token}' updated to '{new_status}' in C min-heap."
    return False, f"Appointment token '{token}' not found."


def cancel_appointment(token: str) -> tuple[bool, str]:
    if not init_backend():
        return False, f"C backend unavailable: {_init_error}"

    code = _appointments_lib.appointments_cancel(token.encode("utf-8"))
    if code == 1:
        return True, f"Appointment '{token}' cancelled in C min-heap."
    return False, f"Appointment token '{token}' not found."


def delete_appointment(token: str) -> tuple[bool, str]:
    if not init_backend():
        return False, f"C backend unavailable: {_init_error}"

    code = _appointments_lib.appointments_delete(token.encode("utf-8"))
    if code == 1:
        return True, f"Appointment '{token}' deleted from C min-heap and CSV."
    return False, f"Appointment token '{token}' not found."


def delete_appointments_by_patient(patient_name: str) -> int:
    if not init_backend():
        return 0

    return _appointments_lib.appointments_delete_by_patient(patient_name.encode("utf-8"))


