
"""
C Backend Adapter for Hospital Management System.

Connects Python (Streamlit frontend) to C modules:
- patients.c: Hash table + CSV persistence
- appointments.c: Min-heap / priority queue + CSV persistence

Windows uses .dll files.
Linux (Streamlit Cloud) compiles and uses .so files.
"""

import ctypes
import os
import sys
import subprocess
from datetime import date, datetime
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

# Buffer sizes matching the C structures
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
    """Load a Windows DLL or compile and load a Linux shared library."""

    if sys.platform == "win32":
        dll_path = BASE_DIR / f"{name}.dll"

        if not dll_path.is_file():
            raise FileNotFoundError(
                f"Missing {dll_path.name}. Compile {name}.c first."
            )

        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(str(BASE_DIR))

        return ctypes.CDLL(str(dll_path))

    if sys.platform.startswith("linux"):
        source_path = BASE_DIR / f"{name}.c"
        library_path = BASE_DIR / f"lib{name}.so"

        if not source_path.is_file():
            raise FileNotFoundError(
                f"Missing C source file: {source_path.name}"
            )

        needs_compile = (
            not library_path.is_file()
            or source_path.stat().st_mtime > library_path.stat().st_mtime
        )

        if needs_compile:
            try:
                result = subprocess.run(
                    [
                        "gcc",
                        "-shared",
                        "-fPIC",
                        "-O2",
                        "-o",
                        str(library_path),
                        str(source_path),
                    ],
                    cwd=str(BASE_DIR),
                    capture_output=True,
                    text=True,
                    check=True,
                )
            except subprocess.CalledProcessError as exc:
                raise RuntimeError(
                    f"Compilation failed for {source_path.name}:\n"
                    f"{exc.stderr or exc.stdout or str(exc)}"
                ) from exc

        return ctypes.CDLL(str(library_path))

    raise OSError(f"Unsupported operating system: {sys.platform}")


def init_backend():
    """Load both C libraries and configure their function signatures."""
    global _patients_lib, _appointments_lib, _init_error

    if _patients_lib is not None and _appointments_lib is not None:
        return True

    try:
        # ---------------- PATIENTS ----------------
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

        # ---------------- APPOINTMENTS ----------------
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

        a_lib.appointments_delete_by_patient.argtypes = [
            ctypes.c_char_p
        ]
        a_lib.appointments_delete_by_patient.restype = ctypes.c_int

        a_lib.appointments_init()

        # Assign globals only after both libraries initialize.
        _patients_lib = p_lib
        _appointments_lib = a_lib
        _init_error = None
        return True

    except Exception as exc:
        _patients_lib = None
        _appointments_lib = None
        _init_error = str(exc)
        return False


def is_backend_available() -> bool:
    return init_backend()


def get_backend_error():
    return _init_error


def get_patients_count() -> int:
    if not init_backend():
        return 0
    return _patients_lib.patients_count()


def get_all_patients() -> list[dict]:
    if not init_backend():
        return []

    records = []
    count = _patients_lib.patients_count()

    for i in range(count):
        id_buf = ctypes.create_string_buffer(ID_LEN)
        name_buf = ctypes.create_string_buffer(NAME_LEN)
        age_val = ctypes.c_int()
        gender_buf = ctypes.create_string_buffer(GENDER_LEN)
        phone_buf = ctypes.create_string_buffer(PHONE_LEN)
        blood_buf = ctypes.create_string_buffer(BLOOD_LEN)

        ok = _patients_lib.patients_get_at(
            i,
            id_buf,
            name_buf,
            ctypes.byref(age_val),
            gender_buf,
            phone_buf,
            blood_buf,
        )

        if ok:
            records.append({
                "Patient ID": id_buf.value.decode("utf-8", errors="replace"),
                "Name": name_buf.value.decode("utf-8", errors="replace"),
                "Age": age_val.value,
                "Gender": gender_buf.value.decode("utf-8", errors="replace"),
                "Phone": phone_buf.value.decode("utf-8", errors="replace"),
                "Blood Group": blood_buf.value.decode("utf-8", errors="replace"),
            })

    return records


def get_patients_df() -> pd.DataFrame:
    columns = [
        "Patient ID", "Name", "Age", "Gender", "Phone", "Blood Group"
    ]
    return pd.DataFrame(get_all_patients(), columns=columns)


def find_patient_by_id(patient_id: str) -> dict | None:
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
        id_buf,
        name_buf,
        ctypes.byref(age_val),
        gender_buf,
        phone_buf,
        blood_buf,
    )

    if not ok:
        return None

    return {
        "Patient ID": id_buf.value.decode("utf-8", errors="replace"),
        "Name": name_buf.value.decode("utf-8", errors="replace"),
        "Age": age_val.value,
        "Gender": gender_buf.value.decode("utf-8", errors="replace"),
        "Phone": phone_buf.value.decode("utf-8", errors="replace"),
        "Blood Group": blood_buf.value.decode("utf-8", errors="replace"),
    }


def add_patient(
    patient_id: str,
    name: str,
    age: int,
    gender: str,
    phone: str,
    blood_group: str,
) -> tuple[bool, str]:
    if not init_backend():
        return False, f"C backend unavailable: {_init_error}"

    code = _patients_lib.patients_add(
        patient_id.encode("utf-8"),
        name.encode("utf-8"),
        int(age),
        gender.encode("utf-8"),
        phone.encode("utf-8"),
        blood_group.encode("utf-8"),
    )

    if code == 1:
        return True, "Patient registered successfully in C hash table!"
    if code == -1:
        return False, "Invalid patient details provided."
    if code == -2:
        return False, f"Patient ID '{patient_id}' already exists."
    if code == -3:
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

    records = []
    count = _appointments_lib.appointments_count()

    for i in range(count):
        token_buf = ctypes.create_string_buffer(TOKEN_LEN)
        patient_buf = ctypes.create_string_buffer(PERSON_LEN)
        doctor_buf = ctypes.create_string_buffer(PERSON_LEN)
        dept_buf = ctypes.create_string_buffer(DEPT_LEN)
        date_buf = ctypes.create_string_buffer(DATE_LEN)
        time_buf = ctypes.create_string_buffer(TIME_LEN)
        priority_buf = ctypes.create_string_buffer(PRIORITY_LEN)
        status_buf = ctypes.create_string_buffer(STATUS_LEN)

        ok = _appointments_lib.appointments_get_at(
            i,
            token_buf,
            patient_buf,
            doctor_buf,
            dept_buf,
            date_buf,
            time_buf,
            priority_buf,
            status_buf,
        )

        if ok:
            raw_date = date_buf.value.decode("utf-8", errors="replace")
            try:
                parsed_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
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
    columns = [
        "Token", "Patient", "Doctor", "Department",
        "Date", "Time", "Priority", "Status"
    ]
    return pd.DataFrame(get_all_appointments(), columns=columns)


def add_appointment(
    token: str,
    patient: str,
    doctor: str,
    department: str,
    appointment_date,
    appointment_time,
    priority: str,
    status: str,
) -> tuple[bool, str]:
    if not init_backend():
        return False, f"C backend unavailable: {_init_error}"

    if isinstance(appointment_date, (date, datetime)):
        date_str = appointment_date.strftime("%Y-%m-%d")
    else:
        date_str = str(appointment_date)

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
        status.encode("utf-8"),
    )

    if code == 1:
        return True, "Appointment booked and inserted into C priority min-heap!"
    if code == -1:
        return False, "Invalid appointment details provided."
    if code == -2:
        return False, f"Appointment token '{token}' already exists."
    if code == -3:
        return False, (
            f"Doctor '{doctor}' already has an appointment scheduled "
            f"at {date_str} {time_str}."
        )

    return False, f"Failed to add appointment (code {code})."


def update_appointment_status(token: str, new_status: str) -> tuple[bool, str]:
    if not init_backend():
        return False, f"C backend unavailable: {_init_error}"

    code = _appointments_lib.appointments_update_status(
        token.encode("utf-8"),
        new_status.encode("utf-8"),
    )

    if code == 1:
        return True, f"Appointment '{token}' updated to '{new_status}'."

    return False, f"Appointment token '{token}' not found."


def cancel_appointment(token: str) -> tuple[bool, str]:
    if not init_backend():
        return False, f"C backend unavailable: {_init_error}"

    code = _appointments_lib.appointments_cancel(token.encode("utf-8"))

    if code == 1:
        return True, f"Appointment '{token}' cancelled."

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

    return _appointments_lib.appointments_delete_by_patient(
        patient_name.encode("utf-8")
    )
