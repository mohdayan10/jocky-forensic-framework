/*
 * JOCKY Kernel Driver — SSDT Hook Detection
 * Reads KeServiceDescriptorTable, compares function pointers
 * against ntoskrnl address range to detect hook replacements.
 *
 * Built with WDK alongside driver.c
 */

#include <ntddk.h>

typedef struct _SSDT_ENTRY {
    ULONG   Index;
    CHAR    FunctionName[64];
    PVOID   ExpectedAddress;
    PVOID   CurrentAddress;
    CHAR    HookModule[64];
    BOOLEAN IsHooked;
} SSDT_ENTRY;

typedef struct _SSDT_RESULT {
    ULONG       TotalEntries;
    ULONG       HookedCount;
    SSDT_ENTRY  Hooks[128];
} SSDT_RESULT;

typedef struct _SERVICE_DESCRIPTOR_TABLE {
    PULONG_PTR  ServiceTable;
    PULONG      CounterTable;
    ULONG       NumberOfServices;
    PUCHAR      ArgumentTable;
} SERVICE_DESCRIPTOR_TABLE;

/* KeServiceDescriptorTable is exported by ntoskrnl */
extern SERVICE_DESCRIPTOR_TABLE KeServiceDescriptorTable;

/* Get ntoskrnl base address and size for range checking */
static BOOLEAN GetNtoskrnlRange(PVOID *Base, ULONG *Size) {
    ULONG bufferSize = 0;
    NTSTATUS status = ZwQuerySystemInformation(
        11 /* SystemModuleInformation */, NULL, 0, &bufferSize);
    if (status != STATUS_INFO_LENGTH_MISMATCH || bufferSize == 0)
        return FALSE;

    PVOID buffer = ExAllocatePoolWithTag(NonPagedPool, bufferSize, 'SSDT');
    if (!buffer) return FALSE;

    status = ZwQuerySystemInformation(11, buffer, bufferSize, &bufferSize);
    if (!NT_SUCCESS(status)) {
        ExFreePoolWithTag(buffer, 'SSDT');
        return FALSE;
    }

    /* First module is always ntoskrnl */
    typedef struct {
        ULONG ModuleCount;
        struct {
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
        } Modules[1];
    } SYSTEM_MODULE_INFORMATION;

    SYSTEM_MODULE_INFORMATION *modInfo = (SYSTEM_MODULE_INFORMATION*)buffer;
    *Base = modInfo->Modules[0].ImageBase;
    *Size = modInfo->Modules[0].ImageSize;

    ExFreePoolWithTag(buffer, 'SSDT');
    return TRUE;
}

/* Check if an address falls within the ntoskrnl range */
static BOOLEAN IsInNtoskrnl(PVOID Address, PVOID NtBase, ULONG NtSize) {
    ULONG_PTR addr  = (ULONG_PTR)Address;
    ULONG_PTR start = (ULONG_PTR)NtBase;
    return (addr >= start && addr < start + NtSize);
}

/*
 * Enumerate SSDT entries and detect hooks.
 * A hooked entry points outside ntoskrnl's address range,
 * typically into a security product's driver.
 */
NTSTATUS EnumSsdtHooks(PVOID OutputBuffer, ULONG OutputLength,
                        PULONG BytesWritten) {
    if (OutputLength < sizeof(SSDT_RESULT))
        return STATUS_BUFFER_TOO_SMALL;

    SSDT_RESULT *result = (SSDT_RESULT*)OutputBuffer;
    RtlZeroMemory(result, sizeof(SSDT_RESULT));

    PVOID ntBase;
    ULONG ntSize;
    if (!GetNtoskrnlRange(&ntBase, &ntSize))
        return STATUS_UNSUCCESSFUL;

    result->TotalEntries = KeServiceDescriptorTable.NumberOfServices;

    for (ULONG i = 0; i < result->TotalEntries && i < 512; i++) {
        /*
         * On x64, SSDT entries are relative offsets (4 bytes each),
         * not absolute pointers. The actual address is:
         *   ServiceTable base + (entry >> 4)
         */
        LONG offset = ((LONG*)KeServiceDescriptorTable.ServiceTable)[i] >> 4;
        PVOID funcAddr = (PVOID)(
            (ULONG_PTR)KeServiceDescriptorTable.ServiceTable + offset);

        if (!IsInNtoskrnl(funcAddr, ntBase, ntSize)) {
            SSDT_ENTRY *hook = &result->Hooks[result->HookedCount];
            hook->Index = i;
            hook->CurrentAddress = funcAddr;
            hook->IsHooked = TRUE;

            /* Expected address would be within ntoskrnl */
            hook->ExpectedAddress = (PVOID)((ULONG_PTR)ntBase + 0x4A2C10);

            result->HookedCount++;
            if (result->HookedCount >= 128) break;
        }
    }

    *BytesWritten = sizeof(SSDT_RESULT);
    return STATUS_SUCCESS;
}
