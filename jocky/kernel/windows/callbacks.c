/*
 * JOCKY Kernel Driver — Kernel Callback Enumeration
 * Enumerates PsSetCreateProcessNotifyRoutine callback array
 * and other notification callbacks to detect tampering.
 *
 * Built with WDK alongside driver.c
 */

#include <ntddk.h>

#define MAX_CALLBACKS 64

typedef enum _CALLBACK_TYPE {
    CALLBACK_PROCESS_CREATE = 0,
    CALLBACK_THREAD_CREATE,
    CALLBACK_IMAGE_LOAD,
    CALLBACK_REGISTRY,
    CALLBACK_OBJECT
} CALLBACK_TYPE;

typedef struct _CALLBACK_ENTRY {
    CALLBACK_TYPE   Type;
    PVOID           CallbackAddress;
    CHAR            OwnerModule[64];
    BOOLEAN         IsActive;
    ULONG           Index;
} CALLBACK_ENTRY;

typedef struct _CALLBACK_RESULT {
    ULONG           TotalCallbacks;
    ULONG           RemovedCount;
    CALLBACK_ENTRY  Entries[MAX_CALLBACKS];
} CALLBACK_RESULT;

/*
 * The callback arrays are internal ntoskrnl structures.
 * PspCreateProcessNotifyRoutine is an array of EX_CALLBACK_ROUTINE_BLOCK
 * pointers. Each block contains the registered callback function.
 *
 * Production code resolves these via pattern scanning in ntoskrnl .text:
 *   1. Find PsSetCreateProcessNotifyRoutine export
 *   2. Scan forward for LEA instruction referencing the array
 *   3. Read array entries (max 64 slots)
 */

/* Structure of internal callback block */
typedef struct _EX_CALLBACK_ROUTINE_BLOCK {
    EX_RUNDOWN_REF  RundownProtect;
    PVOID           Function;       /* PEX_CALLBACK_FUNCTION */
    PVOID           Context;
} EX_CALLBACK_ROUTINE_BLOCK;

/* Find module that owns an address by walking loaded module list */
static BOOLEAN FindOwnerModule(PVOID Address, CHAR *ModuleName, ULONG NameLen) {
    ULONG bufferSize = 0;
    ZwQuerySystemInformation(11, NULL, 0, &bufferSize);
    if (bufferSize == 0) return FALSE;

    PVOID buffer = ExAllocatePoolWithTag(NonPagedPool, bufferSize, 'CBCK');
    if (!buffer) return FALSE;

    NTSTATUS status = ZwQuerySystemInformation(11, buffer, bufferSize, &bufferSize);
    if (!NT_SUCCESS(status)) {
        ExFreePoolWithTag(buffer, 'CBCK');
        return FALSE;
    }

    ULONG moduleCount = *(ULONG*)buffer;
    PVOID moduleEntry = (BYTE*)buffer + sizeof(ULONG);

    typedef struct {
        PVOID  Section;
        PVOID  MappedBase;
        PVOID  ImageBase;
        ULONG  ImageSize;
        ULONG  Flags;
        USHORT LoadOrderIndex;
        USHORT InitOrderIndex;
        USHORT LoadCount;
        USHORT OffsetToFileName;
        CHAR   FullPathName[256];
    } MODULE_ENTRY;

    MODULE_ENTRY *modules = (MODULE_ENTRY*)moduleEntry;
    for (ULONG i = 0; i < moduleCount; i++) {
        ULONG_PTR start = (ULONG_PTR)modules[i].ImageBase;
        ULONG_PTR end   = start + modules[i].ImageSize;
        if ((ULONG_PTR)Address >= start && (ULONG_PTR)Address < end) {
            PCHAR name = &modules[i].FullPathName[modules[i].OffsetToFileName];
            RtlStringCchCopyA(ModuleName, NameLen, name);
            ExFreePoolWithTag(buffer, 'CBCK');
            return TRUE;
        }
    }

    ExFreePoolWithTag(buffer, 'CBCK');
    return FALSE;
}

/*
 * Enumerate process creation notification callbacks.
 * These are the callbacks that EDR products register via
 * PsSetCreateProcessNotifyRoutine(Ex) to monitor process creation.
 *
 * An attacker using BYOVD can remove these callbacks to blind the EDR.
 * JOCKY detects this by enumerating the array and identifying gaps
 * or unexpected ownership.
 */
NTSTATUS EnumCallbacks(PVOID OutputBuffer, ULONG OutputLength,
                        PULONG BytesWritten) {
    if (OutputLength < sizeof(CALLBACK_RESULT))
        return STATUS_BUFFER_TOO_SMALL;

    CALLBACK_RESULT *result = (CALLBACK_RESULT*)OutputBuffer;
    RtlZeroMemory(result, sizeof(CALLBACK_RESULT));

    /*
     * In production, this resolves PspCreateProcessNotifyRoutine via
     * pattern scanning. For reference, the approach:
     *
     * 1. Get PsSetCreateProcessNotifyRoutine address from ntoskrnl export
     * 2. Disassemble forward looking for:
     *      LEA r??, [PspCreateProcessNotifyRoutine]
     * 3. Extract RIP-relative address from LEA instruction
     * 4. Array has 64 slots, each is PVOID (pointer to EX_CALLBACK_ROUTINE_BLOCK)
     * 5. For each non-NULL slot:
     *    - Clear low bits (ExCallback uses low bit as flag)
     *    - Read EX_CALLBACK_ROUTINE_BLOCK.Function
     *    - Identify owning module
     */

    /* Placeholder — production code walks the real callback array */
    result->TotalCallbacks = 0;

    *BytesWritten = sizeof(CALLBACK_RESULT);
    return STATUS_SUCCESS;
}
