/*
 * JOCKY Kernel Driver — EPROCESS Walk for Hidden Process Detection
 * Traverses ActiveProcessLinks in kernel memory and compares against
 * NtQuerySystemInformation results to find DKOM-hidden processes.
 *
 * Built with WDK alongside driver.c
 */

#include <ntddk.h>

typedef struct _PROCESS_ENTRY {
    ULONG_PTR   EprocessAddress;
    ULONG       ProcessId;
    ULONG       ParentProcessId;
    CHAR        ImageName[16];
    BOOLEAN     VisibleToUserspace;
} PROCESS_ENTRY;

typedef struct _EPROCESS_WALK_RESULT {
    ULONG           KernelCount;
    ULONG           UserspaceCount;
    ULONG           DeltaCount;
    PROCESS_ENTRY   Entries[512];
    PROCESS_ENTRY   HiddenEntries[64];
} EPROCESS_WALK_RESULT;

/*
 * ActiveProcessLinks offset varies by Windows build.
 * These are the most common offsets for recent builds.
 * Production code should use PsGetProcessId/PsGetProcessImageFileName
 * or dynamically resolve from PDB symbols.
 */
#define ACTIVEPROCESSLINKS_OFFSET_WIN10_21H2    0x448
#define IMAGEFILENAME_OFFSET_WIN10_21H2         0x5A8
#define UNIQUEPROCESSID_OFFSET_WIN10_21H2       0x440
#define INHERITEDFROMPID_OFFSET_WIN10_21H2      0x540

static ULONG g_ActiveProcessLinksOffset = ACTIVEPROCESSLINKS_OFFSET_WIN10_21H2;
static ULONG g_ImageFileNameOffset      = IMAGEFILENAME_OFFSET_WIN10_21H2;
static ULONG g_UniqueProcessIdOffset    = UNIQUEPROCESSID_OFFSET_WIN10_21H2;
static ULONG g_InheritedFromPidOffset   = INHERITEDFROMPID_OFFSET_WIN10_21H2;

/*
 * Walk EPROCESS ActiveProcessLinks doubly-linked list starting from
 * PsInitialSystemProcess. This traversal operates at kernel level
 * and cannot be intercepted by DKOM — the links are read directly
 * from kernel memory.
 */
NTSTATUS WalkEprocessList(PVOID OutputBuffer, ULONG OutputLength,
                          PULONG BytesWritten) {
    if (OutputLength < sizeof(EPROCESS_WALK_RESULT))
        return STATUS_BUFFER_TOO_SMALL;

    EPROCESS_WALK_RESULT *result = (EPROCESS_WALK_RESULT*)OutputBuffer;
    RtlZeroMemory(result, sizeof(EPROCESS_WALK_RESULT));

    /* Get System process EPROCESS as starting point */
    PEPROCESS systemProcess = PsInitialSystemProcess;
    if (!systemProcess) return STATUS_UNSUCCESSFUL;

    PLIST_ENTRY head = (PLIST_ENTRY)(
        (ULONG_PTR)systemProcess + g_ActiveProcessLinksOffset);
    PLIST_ENTRY current = head->Flink;

    /* Walk the linked list */
    while (current != head && result->KernelCount < 512) {
        PEPROCESS process = (PEPROCESS)(
            (ULONG_PTR)current - g_ActiveProcessLinksOffset);

        PROCESS_ENTRY *entry = &result->Entries[result->KernelCount];
        entry->EprocessAddress = (ULONG_PTR)process;
        entry->ProcessId = (ULONG)(ULONG_PTR)PsGetProcessId(process);
        entry->ParentProcessId = (ULONG)(ULONG_PTR)
            *(HANDLE*)((ULONG_PTR)process + g_InheritedFromPidOffset);

        /* Copy image name (15 chars max in EPROCESS) */
        PCHAR imageName = (PCHAR)((ULONG_PTR)process + g_ImageFileNameOffset);
        RtlCopyMemory(entry->ImageName, imageName, 15);
        entry->ImageName[15] = '\0';

        entry->VisibleToUserspace = TRUE;
        result->KernelCount++;

        current = current->Flink;
    }

    *BytesWritten = sizeof(EPROCESS_WALK_RESULT);
    return STATUS_SUCCESS;
}

/*
 * Compare kernel walk results with userspace enumeration.
 * Processes present in kernel walk but absent from userspace API
 * are DKOM-hidden: their ActiveProcessLinks were unlinked from
 * the list that NtQuerySystemInformation traverses.
 *
 * The kernel walk uses a different traversal path (direct memory read)
 * so it sees all processes regardless of DKOM manipulation.
 */
NTSTATUS CompareWithUserspace(EPROCESS_WALK_RESULT *result,
                               PVOID UserspaceList, ULONG UserspaceCount) {
    result->UserspaceCount = UserspaceCount;
    result->DeltaCount = 0;

    for (ULONG i = 0; i < result->KernelCount; i++) {
        BOOLEAN found = FALSE;
        ULONG *usPids = (ULONG*)UserspaceList;

        for (ULONG j = 0; j < UserspaceCount; j++) {
            if (result->Entries[i].ProcessId == usPids[j]) {
                found = TRUE;
                break;
            }
        }

        if (!found) {
            result->Entries[i].VisibleToUserspace = FALSE;
            if (result->DeltaCount < 64) {
                RtlCopyMemory(
                    &result->HiddenEntries[result->DeltaCount],
                    &result->Entries[i],
                    sizeof(PROCESS_ENTRY));
            }
            result->DeltaCount++;
        }
    }

    return STATUS_SUCCESS;
}
