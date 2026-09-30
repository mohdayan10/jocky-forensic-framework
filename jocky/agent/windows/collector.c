/*
 * JOCKY Spectre Agent — Main Collector
 * Dispatches to forensic collection routines using direct syscall stubs.
 * Collects: processes, network, file metadata, persistence, drivers.
 *
 * Compiled with: cl /O2 /GS- collector.c syscalls.c /link ntdll.lib
 */

#include <windows.h>
#include <winternl.h>
#include "syscalls.h"

#define COLLECT_PROCESSES       0x01
#define COLLECT_NETWORK         0x02
#define COLLECT_FILE_METADATA   0x04
#define COLLECT_PERSISTENCE     0x08
#define COLLECT_DRIVERS         0x10

typedef struct _EVIDENCE_ITEM {
    char    id[16];
    DWORD   artifactType;
    BYTE    sha256[32];
    DWORD   dataSize;
    BYTE    *data;
    struct _EVIDENCE_ITEM *next;
} EVIDENCE_ITEM;

typedef struct _COLLECTION_RESULT {
    DWORD           totalItems;
    EVIDENCE_ITEM   *head;
    DWORD           collectFlags;
} COLLECTION_RESULT;

static SYSCALL_TABLE g_syscalls;

/* Enumerate processes via NtQuerySystemInformation using direct syscalls */
static DWORD collect_processes(COLLECTION_RESULT *result) {
    BYTE buffer[1024 * 256];
    ULONG returnLen = 0;

    NTSTATUS status = DirectNtQuerySystemInformation(
        5,  /* SystemProcessInformation */
        buffer, sizeof(buffer), &returnLen);

    if (status != 0) return 0;

    DWORD count = 0;
    PSYSTEM_PROCESS_INFORMATION proc = (PSYSTEM_PROCESS_INFORMATION)buffer;

    while (TRUE) {
        count++;
        if (proc->NextEntryOffset == 0) break;
        proc = (PSYSTEM_PROCESS_INFORMATION)((BYTE*)proc + proc->NextEntryOffset);
    }

    return count;
}

/* Enumerate network connections via NtDeviceIoControlFile */
static DWORD collect_network(COLLECTION_RESULT *result) {
    /* Uses direct syscall to query TCP/UDP connection table
     * via \Device\Nsi (Network Store Interface) */
    return 0;  /* Stub — full implementation in production build */
}

/* Enumerate files matching path filters with modification time check */
static DWORD collect_file_metadata(COLLECTION_RESULT *result,
                                    const wchar_t **paths, DWORD pathCount,
                                    ULONGLONG modifiedWithinSeconds) {
    DWORD count = 0;

    for (DWORD i = 0; i < pathCount; i++) {
        WIN32_FIND_DATAW findData;
        wchar_t searchPath[MAX_PATH];
        wsprintfW(searchPath, L"%s\\*", paths[i]);

        HANDLE hFind = FindFirstFileW(searchPath, &findData);
        if (hFind == INVALID_HANDLE_VALUE) continue;

        do {
            if (findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) continue;

            /* Check modification time filter */
            FILETIME now;
            GetSystemTimeAsFileTime(&now);
            ULONGLONG nowU = ((ULONGLONG)now.dwHighDateTime << 32) | now.dwLowDateTime;
            ULONGLONG modU = ((ULONGLONG)findData.ftLastWriteTime.dwHighDateTime << 32)
                           | findData.ftLastWriteTime.dwLowDateTime;
            ULONGLONG diffSeconds = (nowU - modU) / 10000000ULL;

            if (diffSeconds <= modifiedWithinSeconds) {
                count++;
            }
        } while (FindNextFileW(hFind, &findData));

        FindClose(hFind);
    }

    return count;
}

/* Check registry persistence locations */
static DWORD collect_persistence(COLLECTION_RESULT *result) {
    DWORD count = 0;
    HKEY hKey;
    LPCSTR runKeys[] = {
        "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
        "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnce",
        "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon",
    };

    for (int i = 0; i < 3; i++) {
        if (RegOpenKeyExA(HKEY_LOCAL_MACHINE, runKeys[i], 0,
                          KEY_READ, &hKey) == ERROR_SUCCESS) {
            DWORD valueCount;
            RegQueryInfoKeyA(hKey, NULL, NULL, NULL, NULL, NULL, NULL,
                            &valueCount, NULL, NULL, NULL, NULL);
            count += valueCount;
            RegCloseKey(hKey);
        }
    }

    /* Also check scheduled tasks via COM */
    return count;
}

/* Enumerate loaded kernel drivers */
static DWORD collect_drivers(COLLECTION_RESULT *result) {
    BYTE buffer[1024 * 64];
    ULONG returnLen = 0;

    NTSTATUS status = DirectNtQuerySystemInformation(
        11,  /* SystemModuleInformation */
        buffer, sizeof(buffer), &returnLen);

    if (status != 0) return 0;

    DWORD count = *(DWORD*)buffer;  /* First DWORD is module count */
    return count;
}

/* Main collection entry point — dispatched from hollowed/injected context */
COLLECTION_RESULT* collector_run(DWORD flags) {
    static COLLECTION_RESULT result = {0};
    result.collectFlags = flags;
    result.totalItems = 0;

    syscall_init(&g_syscalls);

    if (flags & COLLECT_PROCESSES)
        result.totalItems += collect_processes(&result);
    if (flags & COLLECT_NETWORK)
        result.totalItems += collect_network(&result);
    if (flags & COLLECT_FILE_METADATA) {
        const wchar_t *paths[] = {
            L"C:\\Users\\*\\AppData\\Local\\Temp",
            L"C:\\Users\\*\\AppData\\Roaming"
        };
        result.totalItems += collect_file_metadata(&result, paths, 2, 72*3600);
    }
    if (flags & COLLECT_PERSISTENCE)
        result.totalItems += collect_persistence(&result);
    if (flags & COLLECT_DRIVERS)
        result.totalItems += collect_drivers(&result);

    return &result;
}
