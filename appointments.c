#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#ifdef _WIN32
  #if defined(__MINGW32__) && !defined(__MINGW64_VERSION_MAJOR)
    /* Classic MinGW (32-bit) does not declare strtok_s in string.h, while MinGW-w64 does */
    char *strtok_s(char *str, const char *delim, char **context);
  #endif
#else
  #define strtok_s strtok_r
#endif

#ifdef _WIN32
#define API __declspec(dllexport)
#else
#define API
#endif

#define MAX_APPOINTMENTS 10000
#define TOKEN_LEN 24
#define PERSON_LEN 100
#define DEPT_LEN 64
#define DATE_LEN 16
#define TIME_LEN 16
#define PRIORITY_LEN 16
#define STATUS_LEN 24
#define DATA_FILE "appointments.csv"

typedef struct {
    char token[TOKEN_LEN];
    char patient[PERSON_LEN];
    char doctor[PERSON_LEN];
    char department[DEPT_LEN];
    char date[DATE_LEN];       /* YYYY-MM-DD */
    char time[TIME_LEN];       /* HH:MM, 24-hour */
    char priority[PRIORITY_LEN];
    char status[STATUS_LEN];
} Appointment;

static Appointment heap[MAX_APPOINTMENTS];
static int heap_size = 0;
static int initialized = 0;

static int compare(const Appointment *a, const Appointment *b) {
    int c = strcmp(a->date, b->date);
    if (c != 0) return c;
    c = strcmp(a->time, b->time);
    if (c != 0) return c;
    /* For identical times, Emergency then High then Normal */
    int pa = strcmp(a->priority, "Emergency") == 0 ? 0 :
             strcmp(a->priority, "High") == 0 ? 1 : 2;
    int pb = strcmp(b->priority, "Emergency") == 0 ? 0 :
             strcmp(b->priority, "High") == 0 ? 1 : 2;
    return pa - pb;
}

static void swap(Appointment *a, Appointment *b) {
    Appointment t = *a; *a = *b; *b = t;
}

static void sift_up(int i) {
    while (i > 0) {
        int p = (i - 1) / 2;
        if (compare(&heap[p], &heap[i]) <= 0) break;
        swap(&heap[p], &heap[i]); i = p;
    }
}

static void sift_down(int i) {
    while (1) {
        int l = 2 * i + 1, r = 2 * i + 2, smallest = i;
        if (l < heap_size && compare(&heap[l], &heap[smallest]) < 0) smallest = l;
        if (r < heap_size && compare(&heap[r], &heap[smallest]) < 0) smallest = r;
        if (smallest == i) break;
        swap(&heap[i], &heap[smallest]); i = smallest;
    }
}

static void heapify(void) {
    for (int i = heap_size / 2 - 1; i >= 0; i--) sift_down(i);
}

static void save_data(void) {
    FILE *f = fopen(DATA_FILE, "w");
    if (!f) return;
    fprintf(f, "token,patient,doctor,department,date,time,priority,status\n");
    /* Save all heap items; display order is handled by the Python layer. */
    for (int i = 0; i < heap_size; i++) {
        Appointment *a = &heap[i];
        fprintf(f, "%s,%s,%s,%s,%s,%s,%s,%s\n", a->token, a->patient,
                a->doctor, a->department, a->date, a->time, a->priority, a->status);
    }
    fclose(f);
}

static void load_data(void) {
    FILE *f = fopen(DATA_FILE, "r");
    if (f) {
        char line[768];
        fgets(line, sizeof(line), f);
        while (fgets(line, sizeof(line), f) && heap_size < MAX_APPOINTMENTS) {
            Appointment a = {0};
            char *ctx = NULL;
            char *t = strtok_s(line, ",\r\n", &ctx); if (!t) continue; strncpy(a.token, t, TOKEN_LEN-1);
            t = strtok_s(NULL, ",\r\n", &ctx); if (!t) continue; strncpy(a.patient, t, PERSON_LEN-1);
            t = strtok_s(NULL, ",\r\n", &ctx); if (!t) continue; strncpy(a.doctor, t, PERSON_LEN-1);
            t = strtok_s(NULL, ",\r\n", &ctx); if (!t) continue; strncpy(a.department, t, DEPT_LEN-1);
            t = strtok_s(NULL, ",\r\n", &ctx); if (!t) continue; strncpy(a.date, t, DATE_LEN-1);
            t = strtok_s(NULL, ",\r\n", &ctx); if (!t) continue; strncpy(a.time, t, TIME_LEN-1);
            t = strtok_s(NULL, ",\r\n", &ctx); if (!t) continue; strncpy(a.priority, t, PRIORITY_LEN-1);
            t = strtok_s(NULL, ",\r\n", &ctx); if (!t) continue; strncpy(a.status, t, STATUS_LEN-1);
            heap[heap_size++] = a;
        }
        fclose(f);
    }
    heapify();
}

API void appointments_init(void) {
    if (!initialized) { load_data(); initialized = 1; }
}

API int appointments_count(void) {
    appointments_init(); return heap_size;
}

API int appointments_get_at(int index, char *token, char *patient, char *doctor,
                            char *department, char *date, char *time,
                            char *priority, char *status) {
    appointments_init();
    if (index < 0 || index >= heap_size) return 0;
    Appointment *a = &heap[index];
    strcpy(token, a->token); strcpy(patient, a->patient); strcpy(doctor, a->doctor);
    strcpy(department, a->department); strcpy(date, a->date); strcpy(time, a->time);
    strcpy(priority, a->priority); strcpy(status, a->status);
    return 1;
}

API int appointments_add(const char *token, const char *patient, const char *doctor,
                         const char *department, const char *date, const char *time,
                         const char *priority, const char *status) {
    appointments_init();
    if (!token || !patient || !doctor || !department || !date || !time ||
        !priority || !status || !token[0] || heap_size >= MAX_APPOINTMENTS) return -1;
    for (int i = 0; i < heap_size; i++) {
        if (strcmp(heap[i].token, token) == 0) return -2;
        if (strcmp(heap[i].doctor, doctor) == 0 && strcmp(heap[i].date, date) == 0 &&
            strcmp(heap[i].time, time) == 0 &&
            strcmp(heap[i].status, "Cancelled") != 0) return -3;
    }
    Appointment a = {0};
    strncpy(a.token, token, TOKEN_LEN-1); strncpy(a.patient, patient, PERSON_LEN-1);
    strncpy(a.doctor, doctor, PERSON_LEN-1); strncpy(a.department, department, DEPT_LEN-1);
    strncpy(a.date, date, DATE_LEN-1); strncpy(a.time, time, TIME_LEN-1);
    strncpy(a.priority, priority, PRIORITY_LEN-1); strncpy(a.status, status, STATUS_LEN-1);
    heap[heap_size] = a; sift_up(heap_size); heap_size++; save_data(); return 1;
}

API int appointments_update_status(const char *token, const char *status) {
    appointments_init();
    for (int i = 0; i < heap_size; i++) {
        if (strcmp(heap[i].token, token) == 0) {
            strncpy(heap[i].status, status, STATUS_LEN-1);
            save_data(); return 1;
        }
    }
    return 0;
}

API int appointments_cancel(const char *token) {
    return appointments_update_status(token, "Cancelled");
}

API int appointments_delete(const char *token) {
    appointments_init();
    for (int i = 0; i < heap_size; i++) {
        if (strcmp(heap[i].token, token) == 0) {
            heap[i] = heap[heap_size - 1];
            heap_size--;
            heapify();
            save_data();
            return 1;
        }
    }
    return 0;
}

API int appointments_delete_by_patient(const char *patient) {
    appointments_init();
    int count = 0;
    int i = 0;
    while (i < heap_size) {
        if (strcmp(heap[i].patient, patient) == 0) {
            heap[i] = heap[heap_size - 1];
            heap_size--;
            count++;
        } else {
            i++;
        }
    }
    if (count > 0) {
        heapify();
        save_data();
    }
    return count;
}

