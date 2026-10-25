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

#define TABLE_SIZE 20011
#define MAX_PATIENTS 10000
#define ID_LEN 24
#define NAME_LEN 100
#define GENDER_LEN 16
#define PHONE_LEN 20
#define BLOOD_LEN 8
#define DATA_FILE "patients.csv"

typedef struct {
    char id[ID_LEN];
    char name[NAME_LEN];
    int age;
    char gender[GENDER_LEN];
    char phone[PHONE_LEN];
    char blood_group[BLOOD_LEN];
    int used;
    int deleted;
} Patient;

static Patient table[TABLE_SIZE];
static Patient records[MAX_PATIENTS];
static int record_count = 0;
static int initialized = 0;

static unsigned long hash_id(const char *s) {
    unsigned long h = 5381;
    while (*s) h = ((h << 5) + h) + (unsigned char)*s++;
    return h % TABLE_SIZE;
}

static int find_slot(const char *id, int for_insert) {
    unsigned long start = hash_id(id);
    int first_deleted = -1;
    for (int i = 0; i < TABLE_SIZE; i++) {
        int pos = (int)((start + i) % TABLE_SIZE);
        if (table[pos].used && !table[pos].deleted &&
            strcmp(table[pos].id, id) == 0) return pos;
        if (table[pos].deleted && first_deleted < 0) first_deleted = pos;
        if (!table[pos].used) return (for_insert && first_deleted >= 0) ? first_deleted : pos;
    }
    return (for_insert ? first_deleted : -1);
}

static void rebuild_table(void) {
    memset(table, 0, sizeof(table));
    for (int i = 0; i < record_count; i++) {
        int p = find_slot(records[i].id, 1);
        if (p >= 0) {
            table[p] = records[i];
            table[p].used = 1;
            table[p].deleted = 0;
        }
    }
}

static void save_data(void) {
    FILE *f = fopen(DATA_FILE, "w");
    if (!f) return;
    fprintf(f, "id,name,age,gender,phone,blood_group\n");
    for (int i = 0; i < record_count; i++) {
        fprintf(f, "%s,%s,%d,%s,%s,%s\n", records[i].id, records[i].name,
                records[i].age, records[i].gender, records[i].phone,
                records[i].blood_group);
    }
    fclose(f);
}

static void load_data(void) {
    FILE *f = fopen(DATA_FILE, "r");
    if (f) {
        char line[512];
        fgets(line, sizeof(line), f); /* header */
        while (fgets(line, sizeof(line), f) && record_count < MAX_PATIENTS) {
            Patient p = {0};
            char *ctx = NULL;
            char *token = strtok_s(line, ",\r\n", &ctx);
            if (!token) continue; strncpy(p.id, token, ID_LEN - 1);
            token = strtok_s(NULL, ",\r\n", &ctx); if (!token) continue; strncpy(p.name, token, NAME_LEN - 1);
            token = strtok_s(NULL, ",\r\n", &ctx); if (!token) continue; p.age = atoi(token);
            token = strtok_s(NULL, ",\r\n", &ctx); if (!token) continue; strncpy(p.gender, token, GENDER_LEN - 1);
            token = strtok_s(NULL, ",\r\n", &ctx); if (!token) continue; strncpy(p.phone, token, PHONE_LEN - 1);
            token = strtok_s(NULL, ",\r\n", &ctx); if (!token) continue; strncpy(p.blood_group, token, BLOOD_LEN - 1);
            records[record_count++] = p;
        }
        fclose(f);
    }
    rebuild_table();
}

API void patients_init(void) {
    if (!initialized) { load_data(); initialized = 1; }
}

API int patients_count(void) {
    patients_init();
    return record_count;
}

API int patients_get_at(int index, char *id, char *name, int *age,
                        char *gender, char *phone, char *blood_group) {
    patients_init();
    if (index < 0 || index >= record_count) return 0;
    Patient *p = &records[index];
    strcpy(id, p->id); strcpy(name, p->name); *age = p->age;
    strcpy(gender, p->gender); strcpy(phone, p->phone);
    strcpy(blood_group, p->blood_group);
    return 1;
}

API int patients_find(const char *id, char *out_id, char *out_name, int *out_age,
                      char *out_gender, char *out_phone, char *out_blood_group) {
    patients_init();
    int pos = find_slot(id, 0);
    if (pos < 0) return 0;
    Patient *p = &table[pos];
    strcpy(out_id, p->id); strcpy(out_name, p->name); *out_age = p->age;
    strcpy(out_gender, p->gender); strcpy(out_phone, p->phone);
    strcpy(out_blood_group, p->blood_group);
    return 1;
}

API int patients_add(const char *id, const char *name, int age, const char *gender,
                     const char *phone, const char *blood_group) {
    patients_init();
    if (!id || !name || !gender || !phone || !blood_group ||
        !id[0] || !name[0] || age < 0 || age > 120 || record_count >= MAX_PATIENTS)
        return -1;
    for (int i = 0; i < record_count; i++) {
        if (strcmp(records[i].id, id) == 0) return -2;
        if (strcmp(records[i].phone, phone) == 0) return -3;
    }
    Patient p = {0};
    strncpy(p.id, id, ID_LEN - 1); strncpy(p.name, name, NAME_LEN - 1);
    p.age = age; strncpy(p.gender, gender, GENDER_LEN - 1);
    strncpy(p.phone, phone, PHONE_LEN - 1); strncpy(p.blood_group, blood_group, BLOOD_LEN - 1);
    records[record_count++] = p;
    rebuild_table();
    save_data();
    return 1;
}

API int patients_update(const char *id, const char *name, int age, const char *gender,
                       const char *phone, const char *blood_group) {
    patients_init();
    for (int i = 0; i < record_count; i++) {
        if (strcmp(records[i].id, id) == 0) {
            for (int j = 0; j < record_count; j++)
                if (j != i && strcmp(records[j].phone, phone) == 0) return -3;
            strncpy(records[i].name, name, NAME_LEN - 1);
            records[i].age = age;
            strncpy(records[i].gender, gender, GENDER_LEN - 1);
            strncpy(records[i].phone, phone, PHONE_LEN - 1);
            strncpy(records[i].blood_group, blood_group, BLOOD_LEN - 1);
            rebuild_table(); save_data(); return 1;
        }
    }
    return 0;
}

API int patients_delete(const char *id) {
    patients_init();
    for (int i = 0; i < record_count; i++) {
        if (strcmp(records[i].id, id) == 0) {
            for (int j = i; j < record_count - 1; j++) records[j] = records[j + 1];
            record_count--;
            rebuild_table(); save_data(); return 1;
        }
    }
    return 0;
}
