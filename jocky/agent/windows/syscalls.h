/*
 * JOCKY Spectre Agent — Direct Syscall Stub Header
 * Runtime SSN resolution from ntdll .text section.
 * Zero Win32 API calls for all collection operations.
 */

#ifndef JOCKY_SYSCALLS_H
#define JOCKY_SYSCALLS_H

#include <windows.h>

typedef struct _SYSCALL_ENTRY {
    DWORD   ssn;          /* System Service Number */
    PVOID   address;      /* Address in ntdll */
    LPCSTR  name;         /* Function name */
} SYSCALL_ENTRY;

typedef struct _SYSCALL_TABLE {
    SYSCALL_ENTRY NtQuerySystemInformation;
    SYSCALL_ENTRY NtQueryInformationProcess;
    SYSCALL_ENTRY NtOpenProcess;
    SYSCALL_ENTRY NtReadVirtualMemory;
    SYSCALL_ENTRY NtWriteVirtualMemory;
    SYSCALL_ENTRY NtAllocateVirtualMemory;
    SYSCALL_ENTRY NtProtectVirtualMemory;
    SYSCALL_ENTRY NtCreateThreadEx;
    SYSCALL_ENTRY NtClose;
} SYSCALL_TABLE;

BOOL    syscall_init(SYSCALL_TABLE *table);
DWORD   syscall_resolve_ssn(PVOID ntdllBase, LPCSTR funcName);
PVOID   syscall_find_ntdll(void);

/* Direct syscall invocation via inline assembly */
NTSTATUS NTAPI DirectNtQuerySystemInformation(
    ULONG SystemInformationClass,
    PVOID SystemInformation,
    ULONG SystemInformationLength,
    PULONG ReturnLength
);

NTSTATUS NTAPI DirectNtOpenProcess(
    PHANDLE ProcessHandle,
    ACCESS_MASK DesiredAccess,
    POBJECT_ATTRIBUTES ObjectAttributes,
    PCLIENT_ID ClientId
);

NTSTATUS NTAPI DirectNtReadVirtualMemory(
    HANDLE ProcessHandle,
    PVOID BaseAddress,
    PVOID Buffer,
    SIZE_T BufferSize,
    PSIZE_T NumberOfBytesRead
);

#endif /* JOCKY_SYSCALLS_H */
