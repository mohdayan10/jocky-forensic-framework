# JOCKY — Demo Script v4
### Smart India Hackathon 2024 | PS 26148 | NTRO

---

```
     ██╗ ██████╗  ██████╗██╗  ██╗██╗   ██╗
     ██║██╔═══██╗██╔════╝██║ ██╔╝╚██╗ ██╔╝
     ██║██║   ██║██║     █████╔╝  ╚████╔╝
██   ██║██║   ██║██║     ██╔═██╗   ╚██╔╝
╚█████╔╝╚██████╔╝╚██████╗██║  ██╗   ██║
 ╚════╝  ╚═════╝  ╚═════╝╚═╝  ╚═╝   ╚═╝
  From Program to Verified Investigation
  Smart India Hackathon 2024 | PS 26148 | NTRO


========================================================================
  STEP 1: JOCKY Language — Writing an Investigation Program
========================================================================

Investigation program (op_falcon.jky):
--------------------------------------------------
    1 | case "OP-FALCON-01"
    2 | target hostgroup ENTERPRISE_EAST
    3 |
    4 | collect processes
    5 | collect network
    6 | collect persistence
    7 | collect drivers
    8 | collect file_metadata WHERE path IN ["Temp", "AppData"]
    9 |                        AND modified_within "72h"
   10 | collect kernel_callbacks
   11 | collect hook_state
   12 | collect hidden_processes
   13 |
   14 | correlate processes WITH network WITHIN 45 seconds
   15 | correlate processes WITH files
   16 | correlate users WITH processes
   17 |
   18 | detect unsigned_executable_in_temp
   19 | detect byovd_loaded_driver
   20 | detect suspicious_process_chain
   21 | detect lateral_movement
   22 | detect persistence_anomaly
   23 |
   24 | timeline
   25 | evidence_graph
   26 | generate report FORMAT [json, pdf]
--------------------------------------------------

Key points:
  • Every collect has explicit filters — unscoped collection rejected at compile time
  • Same program runs on Windows and Ubuntu — write once
  • Investigation is a reusable, versioned, signed procedure
  • Language constructs are forensic-only

  [Press Enter to continue...]


========================================================================
  STEP 2: Compiler — AST and JIR Output
========================================================================

[LEXER]    Tokenizing op_falcon.jky...              OK  (89 tokens)
[PARSER]   Building AST...                          OK  (19 statements)
[SEMANTIC] Type check + scope resolution...         OK
[JIR]      Emitting intermediate representation...  OK  (16 operations)
[POLICY]   Capability validation...                 OK
           → Investigator cert: VALID — CERT-DEMO-2024-001
           → Host scope: AUTHORIZED — HOSTGROUP ENTERPRISE_EAST
           → Collection filters: ALL PRESENT
           → Kernel ops: AUTHORIZED
           → Case expiry: 2026-12-31 — VALID
[POLICY]   Validation passed. Proceeding to build.

==================================================
JIR OUTPUT:
==================================================
CASE OP_FALCON_01
TARGET HOSTGROUP ENTERPRISE_EAST

COLLECT [
    PROCESSES        { flags: FULL_TREE | MEMORY_FLAGS | LOADED_MODULES }
    NETWORK          { flags: ACTIVE | DNS | ARP | ROUTING }
    PERSISTENCE      { flags: REGISTRY_RUN_KEYS | SCHEDULED_TASKS |
                              SERVICES | STARTUP_FOLDERS }
    DRIVERS          { flags: LOADED_MODULES | SIGNATURE_CHECK | CVE_MATCH }
    FILE_METADATA    { flags: HASH_SHA256 | SIGNATURE | TIMESTAMPS | PE_HEADER,
                       scope: {"path": ["Temp","AppData"]},
                       filter: modified_within:72h }
    KERNEL_CALLBACKS { flags: PROCESS | IMAGE | REGISTRY | THREAD }
    HOOK_STATE       { flags: SSDT | INLINE | IRP }
    HIDDEN_PROCESSES { flags: EPROCESS_WALK_VS_API_DELTA }
]

CORRELATE [
    PROCESSES WITH NETWORK WITHIN 45s
    PROCESSES WITH FILES
    USERS WITH PROCESSES
]

DETECT [
    UNSIGNED_EXECUTABLE_IN_TEMP
    BYOVD_LOADED_DRIVER
    SUSPICIOUS_PROCESS_CHAIN
    LATERAL_MOVEMENT
    PERSISTENCE_ANOMALY
]

EMIT TIMELINE
EMIT EVIDENCE_GRAPH
GENERATE REPORT [JSON, PDF]

  [Press Enter to continue...]


========================================================================
  STEP 3: LLVM Mutation — Per-Compilation Binary Variance
========================================================================

Building same source twice...

  agent_build_1.exe
  85f00d9444b0006251ac209d7a4b00e1c979db375a2a856d631cceb5477eb4fe

  agent_build_2.exe
  5c997781f53ac938acfbbfa01ad320648560ed20e004f2eff971859af7df4e1f

  Hashes differ: YES

Mutation zones in disassembly:
  • Dead basic blocks inserted at different positions in CFG
  • Internal symbol names mutated per build
  • Instruction sequences substituted with functional equivalents
  • Section names and ordering differ

  [Press Enter to continue...]


========================================================================
  STEP 4: Forge — Polymorphic Build Pipeline
========================================================================

[LEXER]    Tokenizing op_falcon.jky...              OK  (89 tokens)
[PARSER]   Building AST...                          OK  (19 statements)
[SEMANTIC] Type check + scope resolution...         OK
[JIR]      Emitting intermediate representation...  OK  (16 operations)
[POLICY]   Capability validation...                 OK
           → Investigator cert: VALID — CERT-DEMO-2024-001
           → Host scope: AUTHORIZED — HOSTGROUP ENTERPRISE_EAST
           → Collection filters: ALL PRESENT
           → Kernel ops: AUTHORIZED
           → Case expiry: 2026-12-31 — VALID
[POLICY]   Validation passed. Proceeding to build.

[FORGE] Generating 3 polymorphic builds...

[FORGE] HOST-01 build:
        SHA-256:      f42793907771b292...
        Entry point:  0xE26C
        Import hash:  0c9b9823d8ba4c16...
        Build cert:   FORGE-BUILD-e1546d | Bound: OP_FALCON_01 / HOST-01

[FORGE] HOST-02 build:
        SHA-256:      5752417545c80dd3...
        Entry point:  0xF367
        Import hash:  122d00e1f3e532d7...
        Build cert:   FORGE-BUILD-fb8a41 | Bound: OP_FALCON_01 / HOST-02

[FORGE] HOST-03 build:
        SHA-256:      d8d3769e705c7f2d...
        Entry point:  0x0DF4
        Import hash:  40031fedfba709d4...
        Build cert:   FORGE-BUILD-ca13fd | Bound: OP_FALCON_01 / HOST-03

[FORGE] No shared hash across deployment. Blockchain record updated.

  [Press Enter to continue...]


========================================================================
  STEP 5: Spectre Agent — Process Hollowing
========================================================================

[SPECTRE] Strategy: PROCESS HOLLOWING
[SPECTRE] Host: HOST-01
[SPECTRE] Target process: svchost.exe (PID 4489)

Process Hollowing Sequence:
  1. CreateProcess(svchost.exe, SUSPENDED)      → PID 4489
  2. NtUnmapViewOfSection(original image)       → OK
  3. VirtualAllocEx(collector PE base)          → OK
  4. WriteProcessMemory(collector PE sections)  → OK
  5. SetThreadContext(new entry point)          → OK
  6. ResumeThread()                             → OK

Verification:
  New process created:      False
  File written to disk:     False
  Visible in Task Manager:  False
  PEB image path:           C:\Windows\System32\svchost.exe
  Actual in-memory image:   [JOCKY collector PE mapped in memory]

Collection Results:
  [EVIDENCE] HOST-01 | processes: 187 objects
  [EVIDENCE] HOST-01 | network_connections: 34 objects
  [EVIDENCE] HOST-01 | persistence_artifacts: 12 objects
  [EVIDENCE] HOST-01 | file_metadata: 89 objects

  [Press Enter to continue...]


========================================================================
  STEP 6: Spectre Agent — Reflective DLL Injection
========================================================================

[SPECTRE] Strategy: REFLECTIVE DLL INJECTION
[SPECTRE] Host: HOST-01
[SPECTRE] Target process: explorer.exe (PID 4315)

API Monitor — DLL Load APIs:
  LoadLibrary              → 0 calls
  LoadLibraryEx            → 0 calls
  LdrLoadDll               → 0 calls

Process Monitor — File System:
  File writes matching *.dll   → 0 events

Loader: Custom reflective loader
Import resolution: Manual — walks PEB→LDR→InMemoryOrderModuleList
Relocation: Self-applied from .reloc section
Disk artifact: NONE

Collection Results:
  [EVIDENCE] HOST-01 | processes: 187 objects
  [EVIDENCE] HOST-01 | network_connections: 34 objects
  [EVIDENCE] HOST-01 | persistence_artifacts: 12 objects

  [Press Enter to continue...]


========================================================================
  STEP 7: Spectre Agent — Direct Syscalls + SOCKS5
========================================================================

[SPECTRE] Strategy: DIRECT SYSCALLS + SOCKS5 ROUTING
[SPECTRE] Host: HOST-01

API Monitor — Win32 API Surface:
  NtQuerySystemInformation    → Direct (no Win32 wrapper)
  NtQueryInformationProcess   → Direct (no Win32 wrapper)
  NtOpenProcess               → Direct (no Win32 wrapper)
  WSAConnect                  → 0 calls
  connect                     → 0 calls

Syscall resolution: Runtime — reads SSN from NTDLL .text section
Stub type: Inline assembly (syscall instruction)
Total Win32 API calls: 0
ETW observable: False

Wireshark — DNS Query Log:
  yourfunction.azurewebsites.net    → Resolved (Beacon channel)
  [any jocky domain]               → NOT PRESENT

Network Routing:
  yourfunction.azurewebsites.net:443    TLS 1.3   ACTIVE
  JOCKY infrastructure visible: NONE

Collection Results:
  [EVIDENCE] HOST-01 | processes: 187 objects
  [EVIDENCE] HOST-01 | network_connections: 34 objects
  [EVIDENCE] HOST-01 | persistence_artifacts: 12 objects
  [EVIDENCE] HOST-01 | drivers: 47 objects
  [EVIDENCE] HOST-01 | kernel_callbacks: 8 objects
  [EVIDENCE] HOST-01 | hook_state: 5 objects

  [Press Enter to continue...]


========================================================================
  STEP 8: Kernel Layer — Hidden Process Detection
========================================================================

[KERNEL] EPROCESS walk:      94 processes found
[KERNEL] API enumeration:    93 processes found
[KERNEL] Delta:              1 process hidden from API

HIDDEN PROCESS DETECTED:
  PID:          4821
  Name:         svc_hidden.exe
  EPROCESS:     0xFFFF8A01C3B40080
  Parent PID:   1204 (explorer.exe)
  Image path:   C:\Users\jdoe\AppData\Local\Temp\svc_hidden.exe
  Status:       INVISIBLE TO TASK MANAGER AND NtQuerySystemInformation

  [Press Enter to continue...]


========================================================================
  STEP 9: Kernel Layer — Hook State Collection
========================================================================

[KERNEL] SSDT baseline comparison complete

HOOK STATE REPORT — HOST-01:
  SSDT hooks detected:    2
  Inline hooks detected:  3
  IRP hooks detected:     0

SSDT HOOKS:
  Index 0x0F (NtOpenProcess)
    Expected:  ntoskrnl.exe + 0x4A2C10
    Found:     SecurityProduct.sys + 0x1B440
    Type:      FUNCTION POINTER REPLACEMENT

  Index 0x23 (NtQuerySystemInformation)
    Expected:  ntoskrnl.exe + 0x3F1800
    Found:     SecurityProduct.sys + 0x1C120
    Type:      FUNCTION POINTER REPLACEMENT

INLINE HOOKS:
  ntdll.dll!NtOpenProcess            → JMP to SecurityProduct.sys
  ntdll.dll!NtWriteVirtualMemory     → JMP to SecurityProduct.sys
  ntdll.dll!NtQuerySystemInformation → JMP to SecurityProduct.sys

  [Press Enter to continue...]


========================================================================
  STEP 10: BYOVD Driver Intelligence
========================================================================

[KERNEL] Driver enumeration complete: 47 drivers loaded

BYOVD INDICATOR DETECTED:
  Driver:        VulnDrv.sys
  SHA-256:       d4e1f2a3b5c6d7e8f9a0b1c2d3e4f5a6...
  CVE:           CVE-2021-21551
  Exploit Type:  Arbitrary kernel read/write via IOCTL
  Signing:       Valid WHQL signature (legacy)
  Load Time:     2026-09-30 09:31:08 UTC
  Loaded By:     powershell.exe (PID 4892)
  Blocklist:     Present on Microsoft vulnerable driver blocklist

  Correlated events:
    → Kernel callback removed:  09:31:09 UTC  (1 second after driver load)
    → Process hidden from API:  09:31:10 UTC  (2 seconds after driver load)

FORENSIC ACTION: CRITICAL finding raised. Correlated with 3 timeline events.

  [Press Enter to continue...]


========================================================================
  STEP 11: Beacon — Cloud-Routed Communication
========================================================================

[BEACON] Establishing cloud-routed channel for HOST-01...
[BEACON] Channel ID:      84a88938c5c2
[BEACON] Cloud provider:  Microsoft Azure Functions
[BEACON] Endpoint FQDN:   yourfunction.azurewebsites.net
[BEACON] TLS version:     1.3
[BEACON] mTLS active:     True
[BEACON] Session key:     AES-256 (ae07003e410b234c...)

Wireshark — DNS Query Log:
  yourfunction.azurewebsites.net    → Resolved
  jocky.investigation.internal      → NOT PRESENT
  [any JOCKY domain]               → NOT PRESENT

Connection Log:
  yourfunction.azurewebsites.net:443    TLS 1.3   ACTIVE
  JOCKY infrastructure visible: NONE

Packet Capture Summary:
  Total connections during investigation:  1
  Destination:  yourfunction.azurewebsites.net:443
  Protocol:     TLS 1.3
  JOCKY infrastructure visible: NONE

  [Press Enter to continue...]


========================================================================
  STEP 12: Multi-Endpoint Investigation Dispatch
========================================================================

[DISPATCH] Dispatching OP-FALCON-01 to 3 endpoints...

Real-time Status Panel:
------------------------------------------------------------
  HOST-01 (Windows)  →  [██████░░░░]  Collecting...  ETA 45s
  HOST-02 (Ubuntu )  →  [██████░░░░]  Collecting...  ETA 60s
  HOST-03 (Windows)  →  [███████░░░]  Collecting...  ETA 30s
------------------------------------------------------------

Collection Complete:
  HOST-01 (Windows)  →  [██████████]  DONE  (187 artifacts)
  HOST-02 (Ubuntu )  →  [██████████]  DONE  (143 artifacts)
  HOST-03 (Windows)  →  [██████████]  DONE  (156 artifacts)

[DISPATCH] Total evidence collected: 486 artifacts across 3 hosts

[QUERY] find file WHERE hash == '7b4c3f2a...92af' ACROSS ALL hosts

Results:
  HOST-01  →  C:\Temp\svc.exe                MATCH
  HOST-02  →  /tmp/.svc                      MATCH
  HOST-03  →  C:\Windows\Temp\svc.exe        MATCH

Lateral movement indicator: Same payload hash on 3 hosts within 8 minutes.

  [Press Enter to continue...]


========================================================================
  STEP 13: Evidence Graph + Timeline
========================================================================

EVIDENCE GRAPH — HOST-01:
--------------------------------------------------
[USER] jdoe
  └── initiated ──> [PROCESS] cmd.exe PID 4821 (E-00421)
        └── spawned ──> [PROCESS] powershell.exe PID 4892 (E-00455)
              ├── connected_to ──> [NETWORK] 185.220.101.42:443 (E-00431)
              └── loaded ──> [DRIVER] VulnDrv.sys CVE match (E-00441)
        └── created ──> [FILE] C:\Temp\svc.exe unsigned PE (E-00422)
        └── modified ──> [REGISTRY] HKLM\...\CurrentVersion\Run (E-00438)

TIMELINE — HOST-01:
--------------------------------------------------
  09:31:02  User session initiated — jdoe
  09:31:04  cmd.exe created (parent: explorer.exe) [E-00421]
  09:31:05  powershell.exe spawned (parent: cmd.exe) [E-00455]
  09:31:06  NTDLL hook state change detected
  09:31:07  Outbound connection → 185.220.101.42:443 [E-00431]
  09:31:08  VulnDrv.sys loaded — CVE match confirmed [E-00441]
  09:31:09  Kernel callback state change observed [E-00447]
  09:31:10  svc.exe created in Temp — unsigned PE [E-00422]
  09:31:13  Persistence key written → Run key [E-00438]
  09:31:17  svchost.exe memory region mismatch detected

  [Press Enter to continue...]


========================================================================
  STEP 14: Correlation Engine → Finding
========================================================================

[CORRELATE] Unsigned executable in Temp:         MATCH  (E-00422)
[CORRELATE] Rapid outbound connection:           MATCH  (E-00455, E-00431)
[CORRELATE] CVE-matched vulnerable driver:       MATCH  (E-00441)
[CORRELATE] Kernel callback state change:        MATCH  (E-00447)
[CORRELATE] Persistence artifact written:        MATCH  (E-00438, E-00450)
[CORRELATE] Hidden process detected:             MATCH  (E-00460)

[ENGINE] 6 signals across 4 rules → FINDING RAISED

Finding ID:    F-6BF59
Case:          OP-FALCON-01
Host:          HOST-01
Severity:      CRITICAL
Confidence:    HIGH
Evidence:      8 artifacts
               [E-00422, E-00455, E-00431, E-00441,
                E-00438, E-00450, E-00460, E-00447]
Rules fired:   UNSIGNED_TEMP_EXE, RAPID_OUTBOUND,
               BYOVD_DRIVER, PERSISTENCE_WRITE,
               HIDDEN_PROCESS_DELTA, KERNEL_CALLBACK_MOD

Explanation:
  Unsigned executable created in Temp by unusual process chain.
  Outbound connection within 30 seconds of process creation.
  CVE-matched driver loaded. Kernel callback state change detected.
  Persistence key written. Process hidden from API enumeration
  but visible via kernel walk.
  6 correlated indicators across 8 evidence artifacts.

  [Press Enter to continue...]


========================================================================
  STEP 15: Blockchain Integrity Verification
========================================================================

=== Verification (unmodified evidence) ===

[BLOCKCHAIN] Querying Hyperledger Fabric ledger...
[BLOCKCHAIN] Peer:          peer0.org1.example.com
[BLOCKCHAIN] Channel:       jocky-evidence
[BLOCKCHAIN] Evidence ID:   E-00421
[BLOCKCHAIN] On-chain hash: 6889780f75bf2c25...7d6a
[BLOCKCHAIN] Current hash:  6889780f75bf2c25...7d6a
[BLOCKCHAIN] Match:         YES
[BLOCKCHAIN] INTEGRITY VERIFIED — artifact unchanged since collection

=== Verification (tampered evidence) ===

[BLOCKCHAIN] Querying Hyperledger Fabric ledger...
[BLOCKCHAIN] Peer:          peer0.org1.example.com
[BLOCKCHAIN] Channel:       jocky-evidence
[BLOCKCHAIN] Evidence ID:   E-00421
[BLOCKCHAIN] On-chain hash: 6889780f75bf2c25...7d6a
[BLOCKCHAIN] Current hash:  5d73677e2f113bfc...ec4a
[BLOCKCHAIN] Match:         NO
[BLOCKCHAIN] INTEGRITY FAILURE — artifact does not match ledger record
[BLOCKCHAIN] Tamper detected at: 2026-09-30T06:17:03.612790+00:00

  [Press Enter to continue...]


========================================================================
  STEP 16: AI Assistant — Evidence-Grounded Explanation
========================================================================

Query: Explain finding F-6BF59 and what technique this suggests.

[VALIDATION] Checking cited evidence IDs against case record...
  E-00421 → VALID
  E-00422 → VALID
  E-00431 → VALID
  E-00438 → VALID
  E-00441 → VALID
  E-00447 → VALID
  E-00450 → VALID
  E-00455 → VALID
  E-00460 → VALID
[VALIDATION] All citations valid. Displaying response.

[AI] Finding F-6BF59 documents a staged intrusion chain on HOST-01.

  A cmd.exe process [E-00421] spawned powershell.exe under an unusual
  parent chain — explorer.exe initiating cmd.exe is not consistent with
  standard enterprise user activity.

  Within 30 seconds, powershell.exe established an outbound connection
  to 185.220.101.42:443 [E-00431] — timing consistent with a
  command-and-control callback immediately after initial execution.

  Concurrently, VulnDrv.sys [E-00441] — a CVE-2021-21551 matched driver
  with an arbitrary kernel read/write vulnerability — was loaded by
  powershell.exe. One second later, a kernel callback registration was
  removed [E-00447]. Two seconds after that, a process became invisible
  to API enumeration [E-00460]. This three-event sequence is consistent
  with BYOVD-assisted EDR blinding: vulnerable driver loaded, monitoring
  callback removed, payload concealed from userspace visibility.

  An unsigned PE was created in C:\Temp [E-00422] and a persistence key
  was written to HKLM\...\CurrentVersion\Run [E-00438], establishing
  persistence before the hidden process was confirmed by kernel walk.

  Technique pattern: BYOVD-assisted staged intrusion with kernel-level
  EDR blinding, fileless payload staging, and registry persistence
  establishment — consistent with a pre-planned multi-stage operation.

  Cited evidence:
  [E-00421, E-00422, E-00431, E-00438, E-00441, E-00447, E-00450,
   E-00455, E-00460]

--------------------------------------------------

=== Demonstrating citation validation enforcement ===

Query: Tell me about evidence artifact E-00999.

[VALIDATION] Checking cited evidence IDs against case record...
  E-00999 → NOT FOUND IN CASE RECORD
[VALIDATION] Response rejected — invalid citation detected.
             Assistant response not displayed to investigator.

  [Press Enter to continue...]


========================================================================
  STEP 17: Report Generation
========================================================================

[REPORT] Generating report for case OP-FALCON-01...
[REPORT] Endpoints:            3
[REPORT] Evidence artifacts:   486
[REPORT] Findings:             1  (CRITICAL — F-6BF59)
[REPORT] JSON: /tmp/jocky_reports/OP-FALCON-01_report.json
[REPORT] PDF:  /tmp/jocky_reports/OP-FALCON-01_report.pdf
[REPORT] Blockchain verified:  486/486 artifacts
[REPORT] Report generation complete.

Report contents:
  • Case identification and authorized investigator identity
  • 3-endpoint inventory with OS and hardware fingerprint
  • 486 evidence artifacts — SHA-256 and collection metadata for each
  • Finding F-6BF59 — CRITICAL, 8 artifacts, 4 rules fired
  • Chronological timeline — 10 events from 09:31:02 to 09:31:17
  • Evidence graph key relationships
  • Kernel state snapshot: 2 SSDT hooks, 3 inline hooks, 1 hidden process
  • Blockchain integrity: 486/486 artifacts verified against Fabric ledger
  • Full investigation audit trail

  [Press Enter to continue...]


========================================================================
  DEMO COMPLETE
========================================================================

  From Program to Verified Investigation:

  One JOCKY program
    → Policy-validated compilation
    → Structurally unique binary per host — LLVM mutation + Forge
    → Memory-resident fileless collection — Spectre Agent
    → Kernel-level visibility — signed forensic driver
    → Cloud-routed covert communication — Beacon
    → Cross-platform evidence normalization
    → Evidence Graph and Timeline reconstruction
    → Multi-signal correlation engine
    → Blockchain-anchored integrity — 486/486 verified
    → Evidence-grounded AI explanation — citation validated
    → Verified forensic report — JSON and PDF

  JOCKY — From Program to Verified Investigation
  Smart India Hackathon 2024 | PS 26148 | NTRO
```
