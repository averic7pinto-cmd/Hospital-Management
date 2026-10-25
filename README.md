# MediCare Hospital Management System (C + Python Streamlit)

A hybrid Hospital Management application combining high-performance **C backend algorithms** with an interactive **Streamlit frontend**.

## Architecture & Data Structures

- **Patients Backend (`patients.c` / `patients.dll`)**:
  - Implements an **Open-Addressing Hash Table** with linear probing for \(O(1)\) patient ID lookups.
  - Automatically enforces unique constraints on Patient ID and phone numbers.
  - Full CRUD operations: `patients_add`, `patients_find`, `patients_update`, `patients_delete`.
  - Automatic CSV persistence to `patients.csv`.

- **Appointments Backend (`appointments.c` / `appointments.dll`)**:
  - Implements a **Priority Min-Heap** ordered by Date, Time, and Emergency/High/Normal priority.
  - Automatic schedule collision detection (prevents booking the same doctor at the same date and time).
  - Operations: `appointments_add` (sift-up), `appointments_update_status`, `appointments_cancel`.
  - Automatic CSV persistence to `appointments.csv`.

- **Python Bridge (`c_backend.py` & `hospital_data.py`)**:
  - Uses Python's `ctypes` library to bind directly to the compiled C DLLs.
  - Synchronizes C in-memory data structures with Streamlit's `session_state` DataFrames.
  - Handles cross-platform library loading and error reporting.

- **Frontend (`app.py`, `pages/`)**:
  - **Dashboard (`app.py`)**: Real-time KPIs, queue overview, recent visits, and C backend status indicator.
  - **Appointments (`1_Appointments.py`)**: Book visits into C min-heap, detect collisions, update status, cancel visits.
  - **Patients (`2_Patients.py`)**: Register patients into C hash table, search directory, query specific slots via \(O(1)\) hash lookup, delete patients.
  - **Doctors (`3_Doctors.py`)**: Browse medical staff and manage availability.
  - **Waiting Queue (`4_Waiting_Queue.py`)**: Live priority-ordered queue backed by C min-heap logic.
  - **Reports (`5_Reports.py`)**: Hospital analytics and charts.

---

## Compilation (Windows 64-bit)

Compile the C source code into 64-bit dynamic libraries using MinGW-w64 (UCRT64):

```powershell
$env:PATH = "C:\msys64\ucrt64\bin;$env:PATH"
gcc -shared -o patients.dll patients.c
gcc -shared -o appointments.dll appointments.c
```

> **Note**: Your compiler bitness must match your Python interpreter (64-bit Python requires 64-bit DLLs).

---

## Running the Application

```powershell
streamlit run app.py
```
