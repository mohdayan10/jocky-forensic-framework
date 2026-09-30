# JOCKY — Demo Guide
### Smart India Hackathon 2024 | PS 26148 | NTRO

---

## Demo Flow Overview

```
1. Write JOCKY Program          (~2 min)
2. Compile → JIR Output         (~1 min)
3. LLVM Mutation — Hash Diff    (~2 min)
4. Forge — Polymorphic Build    (~2 min)
5. Spectre Agent — Hollowing    (~3 min)
6. Spectre Agent — RDI          (~3 min)
7. Spectre Agent — Syscalls     (~2 min)
8. Kernel Layer — Hidden Procs  (~3 min)
9. Kernel Layer — Hook State    (~2 min)
10. BYOVD Detection             (~2 min)
11. Beacon — Cloud Routing      (~2 min)
12. Multi-Endpoint Dispatch     (~2 min)
13. Evidence Graph + Timeline   (~2 min)
14. Correlation → Finding       (~2 min)
15. Blockchain Verification     (~2 min)
16. AI Assistant                (~2 min)
17. Report Generation           (~1 min)
```

---

## Pre-Demo Setup Checklist

- [ ] 3 authorized VMs running (HOST-01 Windows, HOST-02 Ubuntu, HOST-03 Windows)
- [ ] Hyperledger Fabric network up — all peers healthy (`peer channel list` passes)
- [ ] JOCKY Command Console running on localhost
- [ ] Wireshark ready on HOST-01 NIC
- [ ] API Monitor running on HOST-01
- [ ] Sysinternals Process Monitor running on HOST-01
- [ ] DKOM-hidden test process injected on HOST-01 (verify invisible in Task Manager)
- [ ] SSDT hook applied on HOST-01 test VM baseline
- [ ] CVE-matched VulnDrv.sys loaded on HOST-01
- [ ] Forge builds pre-compiled (fallback hashes ready)
- [ ] Pre-recorded screen captures queued for every live demo item
- [ ] Blockchain ledger pre-seeded with one investigation for tamper demo

---

## 1. JOCKY Language — Writing an Investigation Program

**What to show:** Open JOCKY IDE / editor. Type or load the investigation program live.

```jocky
case "OP-FALCON-01"
target hostgroup ENTERPRISE_EAST

collect processes
collect network
collect persistence
collect drivers
collect file_metadata WHERE path IN ["Temp", "AppData"]
                       AND modified_within "72h"
collect kernel_callbacks
collect hook_state
collect hidden_processes

correlate processes WITH network WITHIN 45 seconds
correlate processes WITH files
correlate users WITH processes

detect unsigned_executable_in_temp
detect byovd_loaded_driver
detect suspicious_process_chain
detect lateral_movement
detect persistence_anomaly

timeline
evidence_graph
generate report FORMAT [json, pdf]
```

**Key talking points:**
- Every `collect` command has an explicit filter — unscoped collection is rejected at compile time
- Same program runs on Windows and Ubuntu — investigator writes once
- Investigation is a reusable, versioned, signed procedure — not a manual operation
- Language constructs are forensic-only — no generic abstractions that can be misused

---

## 2. Compiler — AST and JIR Output

**What to show:** Run the compiler. Show terminal output at each stage.

```bash
jocky compile op_falcon.jky --verbose --emit-jir
```

**Expected terminal output:**
```
[LEXER]    Tokenizing op_falcon.jky...          OK
[PARSER]   Building AST...                      OK
[SEMANTIC] Type check + scope resolution...     OK
[JIR]      Emitting intermediate representation...  OK
[POLICY]   Capability validation...             OK
           → Investigator cert: VALID
           → Host scope: AUTHORIZED
           → Collection filters: ALL PRESENT
           → Kernel ops: AUTHORIZED
           → Case expiry: 2026-12-31 — VALID
[POLICY]   Validation passed. Proceeding to build.
```

**Show JIR output file:**
```
CASE OP_FALCON_01
TARGET HOSTGROUP ENTERPRISE_EAST

COLLECT [
    PROCESS    { flags: FULL_TREE | MEMORY_FLAGS | LOADED_MODULES }
    NETWORK    { flags: ACTIVE | DNS | ARP | ROUTING }
    FILE       { scope: ["Temp","AppData"], filter: modified_within:72h }
    KERNEL_CALLBACKS { flags: PROCESS | IMAGE | REGISTRY | THREAD }
    HOOK_STATE       { flags: SSDT | INLINE | IRP }
    HIDDEN_PROCESS   { method: EPROCESS_WALK_VS_API_DELTA }
]
...
```

**Key talking points:**
- JIR is OS-agnostic — same representation feeds Windows and Ubuntu runtimes
- Policy validation happens here before any binary is emitted — failed authorization means no build
- The typed AST catches forensic semantic errors at compile time, not at runtime

---

## 3. LLVM Mutation — Per-Compilation Binary Variance

**What to show:** Compile the same source twice. Show SHA-256 side by side. Show disassembly diff.

```bash
# Build 1
jocky build op_falcon.jky --output agent_build_1.exe
sha256sum agent_build_1.exe

# Build 2 — same source, same program
jocky build op_falcon.jky --output agent_build_2.exe
sha256sum agent_build_2.exe
```

**Expected output:**
```
agent_build_1.exe   a3f7c2e19b84d05f6c1a7e832d9041bc...
agent_build_2.exe   7e4b91d3f20c8a16e94b5d071c3852af...

Hashes differ: YES
```

**Then show disassembly diff:**
```bash
objdump -d agent_build_1.exe > disasm_1.txt
objdump -d agent_build_2.exe > disasm_2.txt
diff disasm_1.txt disasm_2.txt | head -60
```

**Point to in the diff:**
- Dead basic blocks inserted at different positions in CFG
- Internal symbol names mutated (e.g., `fn_a3f2` vs `fn_9c18`)
- Instruction sequences substituted with functional equivalents
- Section names and ordering differ

**Key talking points:**
- File-reputation databases cannot match either binary — no prior hash exists
- Static signature matching fails — no two builds share byte patterns in mutation zones
- Functionally identical at runtime — investigation logic is unchanged
- This happens automatically on every Forge deployment — not a one-time operation

---

## 4. Forge — Polymorphic Build Pipeline

**What to show:** Dispatch the same investigation to 3 hosts. Show 3 different builds emitted.

```bash
jocky forge deploy op_falcon.jky --targets HOST-01,HOST-02,HOST-03
```

**Expected output:**
```
[FORGE] HOST-01 build:
        SHA-256:      a3f7c2e1...
        Entry point:  0x1A4C
        Import hash:  d8f2a1c9...
        Build cert:   FORGE-BUILD-7a3f9c | Bound: OP-FALCON-01 / HOST-01

[FORGE] HOST-02 build:
        SHA-256:      9b2e8d47...
        Entry point:  0x2B91
        Import hash:  4c7f3e12...
        Build cert:   FORGE-BUILD-2c8b1a | Bound: OP-FALCON-01 / HOST-02

[FORGE] HOST-03 build:
        SHA-256:      f5c14a83...
        Entry point:  0x3F07
        Import hash:  a91b6d34...
        Build cert:   FORGE-BUILD-e4d72f | Bound: OP-FALCON-01 / HOST-03

[FORGE] No shared hash across deployment. Blockchain record updated.
```

**Key talking points:**
- Three deployments, three structurally distinct binaries — zero hash reuse
- Each binary certificate-bound to its case ID and host — intercepted binary cannot authenticate elsewhere
- Imphash differs per build — import-hash detection defeated
- Entry point varies — static entry-point heuristics find no consistent pattern

---

## 5. Spectre Agent — Process Hollowing

**What to show:** Run hollowing on authorized HOST-01 test VM. Show collector running inside svchost.exe.

**Setup:** Legitimate svchost.exe instance selected as host process.

```bash
spectre deploy --strategy PROCESS_HOLLOW --host HOST-01 --target-process svchost.exe
```

**Show in Process Monitor (Sysinternals):**
- svchost.exe PID active ✓
- No new process created ✓
- No file written to disk ✓
- Collection results returned to console ✓

**Show in Task Manager:**
- Collector is not visible as a separate process
- svchost.exe appears as a normal system process

**Key talking points:**
- Collector runs under the identity of a trusted system process
- No new binary written to disk at any point
- No new process creation event generated
- File-system monitoring, binary reputation, and process-name heuristics find nothing
- Note: kernel-level process creation callbacks (PsSetCreateProcessNotifyRoutineEx) may still observe the hollowing — that detection surface is inventoried by the Kernel Layer's callback audit

---

## 6. Spectre Agent — Reflective DLL Injection

**What to show:** Inject collection module into authorized process. Show API Monitor trace. Show file system monitor.

```bash
spectre deploy --strategy REFLECTIVE_DLL --host HOST-01 --target-process explorer.exe
```

**Show API Monitor — filter for:**
```
LoadLibrary     → 0 calls
LoadLibraryEx   → 0 calls
LdrLoadDll      → 0 calls
```

**Show Process Monitor — filter for:**
```
File writes matching *.dll  → 0 events
```

**Show collection results arriving at console:**
```
[EVIDENCE] HOST-01 | Process collector returned 187 process objects
[EVIDENCE] HOST-01 | Network state: 34 active connections
[EVIDENCE] HOST-01 | Persistence: 12 registry artifacts
```

**Key talking points:**
- Custom reflective loader resolves its own imports and applies its own relocations from memory
- No Windows loader API invoked — no LoadLibrary, no LdrLoadDll
- No DLL file on disk at any point — file system monitor confirms zero DLL write events
- Collection runs entirely in the target process's existing memory space

---

## 7. Spectre Agent — Direct Syscalls + SOCKS5 Routing

**What to show:** Run collection with API Monitor active. Show zero Win32 API surface. Show network capture showing only cloud provider domain.

```bash
spectre deploy --strategy DIRECT_SYSCALL --host HOST-01
```

**Show API Monitor — filter for:**
```
NtQuerySystemInformation  → Direct (no Win32 wrapper)
NtQueryInformationProcess → Direct
NtOpenProcess             → Direct
WSAConnect                → 0 calls
connect                   → 0 calls
```

**Show Wireshark — DNS filter:**
```
dns.qry.name contains "jocky"     → 0 results
dns.qry.name contains "azure"     → results visible (Beacon channel)
```

**Key talking points:**
- Inline assembly syscall stubs resolve syscall numbers from NTDLL at runtime
- Zero Win32 API surface for enumeration, network state, and persistence operations
- ETW-based behavioral heuristics that watch Win32 API call sequences see nothing
- SOCKS5 client handles all network routing through direct syscall stubs — no WinSock API calls from investigation traffic

---

## 8. Kernel Layer — Hidden Process Detection

**What to show:** DKOM-hidden process that is invisible to Task Manager, visible via JOCKY EPROCESS walk.

**Setup (pre-demo):** Hide a test process using DKOM manipulation on HOST-01.

**Show Task Manager on HOST-01:**
```
Test process: NOT VISIBLE
```

**Run JOCKY kernel collection:**
```bash
jocky kernel-collect --host HOST-01 --operation HIDDEN_PROCESS_DELTA
```

**Show output:**
```
[KERNEL] EPROCESS walk: 94 processes found
[KERNEL] API enumeration: 93 processes found
[KERNEL] Delta: 1 process hidden from API

HIDDEN PROCESS DETECTED:
  PID:          4821
  Name:         svc_hidden.exe
  EPROCESS:     0xFFFF8A01C3B40080
  Parent PID:   1204 (explorer.exe)
  Image path:   C:\Users\jdoe\AppData\Local\Temp\svc_hidden.exe
  Status:       INVISIBLE TO TASK MANAGER AND NtQuerySystemInformation
```

**Key talking points:**
- Standard API calls — Task Manager, Process Explorer, NtQuerySystemInformation — all return 93 processes
- EPROCESS list walk via kernel memory mapping returns 94
- Delta of 1 = DKOM-hidden process — definitively confirmed
- This artifact is completely inaccessible from userspace

---

## 9. Kernel Layer — Hook State Collection

**What to show:** SSDT and inline hook enumeration identifying hooked functions and responsible modules.

```bash
jocky kernel-collect --host HOST-01 --operation HOOK_STATE
```

**Show output:**
```
[KERNEL] SSDT baseline comparison complete

HOOK STATE REPORT — HOST-01:
  SSDT hooks detected:         2
  Inline hooks detected:       3
  IRP hooks detected:          0

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
  ntdll.dll!NtOpenProcess     → JMP to SecurityProduct.sys
  ntdll.dll!NtWriteVirtualMemory → JMP to SecurityProduct.sys
  ntdll.dll!NtQuerySystemInformation → JMP to SecurityProduct.sys
```

**Key talking points:**
- Shows exactly what is hooked, by which module, and at which address
- Establishes ground truth for what security monitoring is active on this endpoint
- This is why direct syscalls matter — the hooked API paths are documented here
- Evidence is linked to the finding record — investigator can verify hook state before trusting any API output

---

## 10. BYOVD Driver Intelligence

**What to show:** CVE-matched driver detected on HOST-01, correlated with timeline.

```bash
jocky kernel-collect --host HOST-01 --operation DRIVER_INTELLIGENCE
```

**Show output:**
```
[KERNEL] Driver enumeration complete: 47 drivers loaded

BYOVD INDICATOR DETECTED:
  Driver:         VulnDrv.sys
  SHA-256:        d4e1f2a3...
  CVE:            CVE-2021-21551
  Exploit Type:   Arbitrary kernel read/write via IOCTL
  Signing:        Valid WHQL signature (legacy)
  Load Time:      2026-09-30 09:31:08 UTC
  Loaded By:      powershell.exe (PID 4892)
  Blocklist:      Present on Microsoft vulnerable driver blocklist

  Correlated events:
  → Kernel callback state change: 09:31:09 UTC
     PsSetCreateProcessNotify entry removed
  → Process hidden from API: 09:31:10 UTC (PID 4821)

FORENSIC ACTION: CRITICAL finding raised. Correlated with 3 timeline events.
```

**Key talking points:**
- CVE-indexed database matches driver hash and name against known vulnerable drivers
- Correlation with callback state change reconstructs the adversarial attack path
- This is how BYOVD attacks leave traces even when the attacker is careful
- Detection is passive — JOCKY identifies the driver, documents the exploitation path, does not exploit it

---

## 11. Beacon — Cloud-Routed Communication

**What to show:** Active investigation running. Full network capture at endpoint showing only Azure/AWS domains.

**Run Wireshark on HOST-01 during active collection.**

**Show DNS query log:**
```
Query: yourfunction.azurewebsites.net   → Resolved ✓
Query: jocky.investigation.internal     → NOT PRESENT
Query: [any JOCKY domain]               → NOT PRESENT
```

**Show connection log:**
```
Connections during investigation:
  yourfunction.azurewebsites.net:443    TLS 1.3   ACTIVE
  [JOCKY API Gateway IP]                          NOT VISIBLE (private channel)
```

**Show full packet capture summary:**
```
Total connections during 3-minute investigation: 1
Destination: Azure Functions endpoint
Protocol: TLS 1.3
JOCKY infrastructure visible: NONE
```

**Key talking points:**
- mTLS enforced between agent certificate and JOCKY API Gateway — both sides authenticate
- Azure/AWS FQDNs are pre-authorized in enterprise firewall rules — cannot be blocked without disrupting legitimate business operations
- AES-256 session-unique key encrypts payload before it reaches the cloud function
- Investigation target monitoring their own network sees nothing anomalous

---

## 12. Multi-Endpoint Investigation Dispatch

**What to show:** One JOCKY program dispatched to all 3 VMs simultaneously from Command Console.

```bash
jocky dispatch op_falcon.jky --targets ALL
```

**Show Command Console — real-time status panel:**
```
HOST-01 (Windows)  →  [████████░░]  Collecting...  ETA 45s
HOST-02 (Ubuntu)   →  [██████░░░░]  Collecting...  ETA 60s
HOST-03 (Windows)  →  [█████████░]  Collecting...  ETA 30s
```

**After completion — show cross-host query:**
```bash
jocky query "find file WHERE hash == '7b4c...92af' ACROSS ALL hosts"
```

```
Results:
  HOST-01  →  C:\Temp\svc.exe          MATCH
  HOST-02  →  /tmp/.svc                MATCH
  HOST-03  →  C:\Windows\Temp\svc.exe  MATCH

Lateral movement indicator: Same payload on 3 hosts within 8 minutes.
```

**Key talking points:**
- One program, three structurally distinct binaries, three simultaneous collections
- Global cross-host correlation identifies shared indicators automatically
- This is environment-level investigation — not host-by-host manual work
- Same evidence model from Windows and Ubuntu enables the cross-host query

---

## 13. Evidence Graph and Timeline

**What to show:** Interactive evidence graph and timeline in Command Console for HOST-01.

**Evidence Graph — point to key relationships:**
```
USER (jdoe)
  └── initiated → PROCESS (cmd.exe PID 4821)
        └── spawned → PROCESS (powershell.exe PID 4892)
              ├── reflective load → SPECTRE COLLECTOR [in-memory]
              ├── connected to → IP 185.220.x.x:443
              └── loaded → DRIVER (VulnDrv.sys) [CVE match]
        └── created → FILE (C:\Temp\svc.exe) [unsigned PE]
        └── modified → REGISTRY [Run key — persistence]
```

**Timeline — scroll through chronologically:**
```
09:31:02  User session initiated — jdoe
09:31:04  cmd.exe created (parent: explorer.exe)
09:31:05  powershell.exe spawned (parent: cmd.exe)
09:31:06  NTDLL hook state change detected
09:31:07  Outbound connection → 185.220.x.x:443
09:31:08  VulnDrv.sys loaded (CVE match confirmed)
09:31:09  Kernel callback state change observed
09:31:10  C:\Temp\svc.exe created (unsigned PE)
09:31:13  Persistence key written → HKLM\...\CurrentVersion\Run
09:31:17  svchost.exe memory region mismatch detected
```

**Key talking points:**
- Every node in the graph links to the underlying evidence artifact
- Timeline reconstructs exact sequence automatically from all collected timestamps
- Graph does not assert malicious intent — it shows what the evidence connects
- Investigators verify each relationship before drawing conclusions

---

## 14. Correlation Engine → Finding

**What to show:** Multi-indicator CRITICAL finding generated from test scenario.

**Show detection engine output in console:**
```
[CORRELATE] Process → Network within 30s:       MATCH  (powershell.exe → 185.220.x.x)
[CORRELATE] Unsigned PE in Temp:                MATCH  (svc.exe)
[CORRELATE] CVE-matched driver in session:      MATCH  (VulnDrv.sys)
[CORRELATE] Kernel callback state change:       MATCH
[CORRELATE] Persistence artifact written:       MATCH
[CORRELATE] Unusual parent-child chain:         MATCH

[ENGINE] 6 signals across 4 detection rules → FINDING RAISED
```

**Show complete finding record:**
```
Finding ID:    F-00089
Case:          OP-FALCON-01
Host:          HOST-01
Severity:      CRITICAL
Confidence:    HIGH
Evidence:      6 artifacts [E-00421, E-00422, E-00431, E-00438, E-00441, E-00447]
Rules fired:   UNSIGNED_TEMP_EXE, RAPID_OUTBOUND, BYOVD_DRIVER, PERSISTENCE_WRITE

Explanation:
  Unsigned executable created in Temp by unusual process chain.
  Outbound connection within 30s. CVE-matched driver loaded.
  Kernel callback state modified. Persistence key written.
  Six correlated indicators across process, file, network,
  driver, registry, and kernel evidence.
```

**Key talking points:**
- Single-artifact signals are indicators, not findings — engine requires multi-signal correlation
- Severity (impact if confirmed) and Confidence (evidential strength) are separate dimensions
- Every finding links directly to evidence IDs — investigator can drill into any artifact
- Detection rules are additive — more correlated signals raise confidence, not just severity

---

## 15. Blockchain Integrity Ledger

**What to show:** Evidence hash anchored to Hyperledger Fabric. Verification passing. Then simulate tamper and show verification failing.

```bash
jocky integrity verify --evidence-id E-00421 --case OP-FALCON-01
```

**Show passing verification:**
```
[BLOCKCHAIN] Querying Hyperledger Fabric ledger...
[BLOCKCHAIN] Evidence ID:    E-00421
[BLOCKCHAIN] On-chain hash:  7b4c3f2a819d...92af
[BLOCKCHAIN] Current hash:   7b4c3f2a819d...92af
[BLOCKCHAIN] Match:          YES
[BLOCKCHAIN] INTEGRITY VERIFIED — artifact unchanged since collection
```

**Now simulate tamper (modify stored evidence file):**
```bash
jocky integrity verify --evidence-id E-00421 --case OP-FALCON-01
```

```
[BLOCKCHAIN] Querying Hyperledger Fabric ledger...
[BLOCKCHAIN] On-chain hash:  7b4c3f2a819d...92af
[BLOCKCHAIN] Current hash:   c9a1e4f7320b...14dc
[BLOCKCHAIN] Match:          NO
[BLOCKCHAIN] INTEGRITY FAILURE — artifact does not match ledger record
[BLOCKCHAIN] Tamper detected at: 2026-09-30 10:14:22 UTC
```

**Key talking points:**
- No single party controls the ledger — multiple nodes across organizational boundaries
- Tamper is mathematically detectable, not trust-dependent
- Relevant for multi-organization investigations where evidence must be verified by external legal teams
- Signed audit logs require trusting the key holder — blockchain does not

---

## 16. AI Assistant — Evidence-Grounded Explanation

**What to show:** Ask the assistant about Finding F-00089. Show it citing specific evidence IDs. Then show citation validation rejecting a hallucinated ID.

**Query:**
```
> Explain finding F-00089 and what technique this pattern suggests.
```

**Assistant response:**
```
Finding F-00089 shows a multi-stage execution chain on HOST-01.

A cmd.exe process [E-00421] spawned powershell.exe under an unusual
parent — explorer.exe is not a typical cmd.exe parent in this environment.
Within 30 seconds, powershell.exe established an outbound connection
to 185.220.x.x:443 [E-00431] — consistent with command-and-control
callback timing.

Concurrently, VulnDrv.sys [E-00441] — a CVE-matched driver — was loaded,
followed immediately by a kernel callback state change [documented in
kernel evidence]. This sequence is consistent with BYOVD-assisted
EDR blinding before secondary payload execution.

An unsigned PE (svc.exe) was created in C:\Temp [E-00422], and a
persistence key was written to HKLM\...\CurrentVersion\Run [E-00438].

The overall pattern is consistent with a staged intrusion: initial
execution via script host, BYOVD kernel manipulation, secondary
payload drop, persistence establishment.

Evidence basis: [E-00421, E-00422, E-00431, E-00438, E-00441, E-00447]
```

**Now show citation validation — attempt a query with a fake evidence ID:**
```
[VALIDATION] Checking cited evidence IDs against case record...
  E-00421 → VALID
  E-00422 → VALID
  E-00999 → NOT FOUND IN CASE RECORD
[VALIDATION] Response rejected — invalid citation detected.
             Assistant response not displayed.
```

**Key talking points:**
- Assistant receives only structured finding objects — not raw evidence content
- Every cited evidence ID is validated against the case record before display
- The assistant explains and navigates — it does not produce findings or assert intent
- Hallucinated evidence references are caught before they reach the investigator

---

## 17. Report Generation

**What to show:** Generate final report at investigation close. Show PDF and JSON output.

```bash
jocky report generate --case OP-FALCON-01 --format json,pdf
```

**Show report sections in PDF:**
- Case identification and authorized investigator identity
- Endpoint inventory (HOST-01 Windows, HOST-02 Ubuntu, HOST-03 Windows)
- Evidence inventory — 312 artifacts, SHA-256 for each
- Findings — F-00089 CRITICAL, full evidence links
- Chronological timeline
- Evidence graph key relationships
- Kernel state snapshot — hook inventory, callback registrations, hidden process delta
- Blockchain integrity verification records for all artifacts
- Full investigation audit trail

**Show JSON structure briefly:**
```json
{
  "case_id": "OP-FALCON-01",
  "investigator": "...",
  "endpoints": [...],
  "evidence_count": 312,
  "findings": [
    {
      "id": "F-00089",
      "severity": "CRITICAL",
      "confidence": "HIGH",
      "evidence": ["E-00421", "E-00422", "..."],
      "blockchain_verified": true
    }
  ],
  "integrity_verification": "PASSED"
}
```

**Key talking points:**
- Every artifact in the report has a blockchain-verified hash
- Report is fully reproducible — the investigation program that produced it is versioned and signed
- JSON format enables integration with SIEM, ticketing, and legal case management systems
- PDF is court-ready with full chain of custody documentation

---

## Fallback Plan

If any live demo component fails during presentation:

| Component | Fallback |
|---|---|
| Forge build | Pre-recorded terminal capture + show 3 pre-built binaries with hash diff |
| LLVM hash diff | Show pre-computed disassembly diff side by side |
| Process hollowing | Pre-recorded screen capture + explain live what each tool shows |
| Reflective DLL injection | Pre-recorded API Monitor trace |
| Blockchain verification | Pre-recorded terminal output + explain the math |
| Hyperledger Fabric | Show tamper simulation on backup node set |
| Multi-endpoint dispatch | Show pre-collected results and run cross-host query live |

**Rule: Always run live first. Switch to fallback only if the live attempt clearly fails. Never open with the fallback.**

---

## Key Questions to Prepare For

**Q: Would process hollowing bypass CrowdStrike Falcon?**
> Process hollowing defeats file-system monitoring, binary reputation, and user-mode API hook detection. Modern EDRs including Falcon also detect hollowing via kernel-level process creation callbacks. That detection surface is exactly what the Kernel Layer's callback state audit inventories — we document what's active on the target before collection begins. API unhooking addresses the user-mode layer; the kernel callback layer is where the Kernel Layer operates.

**Q: Domain fronting — is that not blocked by major CDNs?**
> We do not use domain fronting. JOCKY Beacon routes through legitimate Azure Function and AWS Lambda endpoints that we control. Traffic goes to FQDNs we provision — not to a CDN frontend for a different backend. The traffic is indistinguishable from routine cloud API calls because it is a routine cloud API call to our function endpoint.

**Q: Who authorizes BYOVD-assisted collection?**
> JOCKY uses BYOVD detection and enumeration only — identifying adversarial vulnerable driver use on the target. Authorized forensic collection uses signed forensic drivers. The Capability and Policy Validation gate enforces the distinction at compile time.

**Q: Why blockchain over a signed audit log?**
> A signed audit log requires trusting the party holding the signing key. In a multi-organization investigation — NTRO, a state agency, an external auditor — no single party should hold unilateral control over the evidence provenance record. Hyperledger Fabric with multiple participating nodes gives each party independent verification without trusting any single organization's self-reported logs.

**Q: How does the AI assistant prevent hallucination?**
> The assistant receives only structured finding objects with explicit evidence IDs. Every evidence ID cited in the response is validated against the case record before the response is displayed. An ID that does not exist in the case record causes the response to be rejected. The assistant has no access to raw evidence content — it cannot cite what it cannot see.

---

*JOCKY — From Program to Verified Investigation*
