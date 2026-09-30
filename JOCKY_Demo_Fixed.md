# JOCKY — Fixed Demo Guide
### Real Artifacts. Real Output. Judge-Proof.

---

## The Three Non-Negotiables

These three must be real before presentation day. Everything else can be narrated.
If any of these three fail live, switch to pre-recorded capture immediately.

1. **LLVM mutation** — two actual .exe files on disk, sha256sum run live
2. **Process hollowing** — Process Hacker open on screen showing collector PE inside svchost
3. **Blockchain verification** — actual Hyperledger Fabric peer running, real query output

---

## Pre-Demo Build Checklist

Run through this the night before and the morning of presentation.

### Environment
- [ ] HOST-01 Windows VM running, RDP open and ready
- [ ] HOST-02 Ubuntu VM running, SSH open and ready
- [ ] HOST-03 Windows VM running
- [ ] JOCKY Command Console running on localhost — all endpoints showing green
- [ ] Hyperledger Fabric network up — run `peer channel list` and confirm all peers healthy
- [ ] Django backend running — `curl localhost:8000/api/health` returns 200

### Real Artifacts Pre-Built
- [ ] `agent_build_1.exe` and `agent_build_2.exe` already compiled and sitting in `/demo/builds/`
- [ ] sha256sum of both pre-computed and saved to `hashes.txt` — verify they differ
- [ ] Disassembly diff pre-generated: `objdump -d build1.exe > d1.txt && objdump -d build2.exe > d2.txt && diff d1.txt d2.txt > diff.txt`
- [ ] DKOM-hidden test process injected on HOST-01 — verify invisible in Task Manager
- [ ] VulnDrv.sys loaded on HOST-01 test VM
- [ ] SSDT hooks applied on HOST-01 test VM baseline
- [ ] One evidence artifact pre-submitted to Hyperledger Fabric ledger (E-00421) for blockchain demo

### Tools Open and Ready on HOST-01
- [ ] Process Hacker 2 open (not Task Manager — Process Hacker shows memory maps)
- [ ] API Monitor running, filter set to: LoadLibrary, LoadLibraryEx, LdrLoadDll, WSAConnect, connect
- [ ] Wireshark running on active NIC, filter: `dns || tcp.port == 443`
- [ ] File system monitor (Process Monitor, filter: Operation=WriteFile, Path ends with .dll or .exe)

### Fallback Captures Ready
- [ ] Screen recording of LLVM build (60 sec) queued in VLC
- [ ] Screen recording of process hollowing in Process Hacker queued in VLC
- [ ] Screen recording of Wireshark capture during Beacon queued in VLC
- [ ] Screen recording of blockchain verification queued in VLC
- [ ] All fallbacks labeled and in a single folder on the desktop

---

## Demo Script

---

### STEP 1 — Write the Investigation Program
**Duration: ~2 min | What judges see: JOCKY editor in console**

Open the JOCKY Command Console editor. Type the program live or load `op_falcon.jky`.

```
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

**Say out loud:**
> "Every collect command has an explicit filter. If I remove the path filter from file_metadata
> and try to compile — watch what happens."

Remove the WHERE clause. Run the compiler. Show the rejection:

```
[POLICY] Collection filter missing on FILE_METADATA — unscoped collection rejected.
         Investigation program halted. Reason logged to audit trail.
```

Restore the filter. This establishes that the system enforces scope — not just claims it.

---

### STEP 2 — Compile: AST and JIR Output
**Duration: ~1.5 min | What judges see: real terminal output**

```bash
python3 -m jocky.compiler op_falcon.jky --verbose --emit-jir
```

Let the output run. Point to each stage as it prints:

```
[LEXER]    Tokenizing...          OK  (89 tokens)
[PARSER]   Building AST...        OK  (19 statements)
[SEMANTIC] Type check...          OK
[JIR]      Emitting IR...         OK  (16 operations)
[POLICY]   Capability check...    OK
           → Investigator cert: VALID
           → Host scope: AUTHORIZED
           → Collection filters: ALL PRESENT
           → Kernel ops: AUTHORIZED
           → Case expiry: 2026-12-31 VALID
```

Open the emitted JIR file in a text editor and scroll through it briefly.

**Say out loud:**
> "This JIR is OS-agnostic. The same file feeds both the Windows and Ubuntu runtimes.
> The investigator never rewrites this for a different operating system."

---

### STEP 3 — LLVM Mutation: REAL Hash Diff
**Duration: ~3 min | What judges see: actual files, actual hashes**

**This must be real. Do not use printed output.**

Open a terminal. Show the `/demo/builds/` directory:

```bash
ls -la /demo/builds/
```

Both files should be visible with their sizes.

Run sha256sum on both:

```bash
sha256sum /demo/builds/agent_build_1.exe
sha256sum /demo/builds/agent_build_2.exe
```

Judges will see two different hashes printed by the actual tool.

Now compile a third build live:

```bash
python3 -m jocky.forge build op_falcon.jky --output /demo/builds/agent_build_live.exe
sha256sum /demo/builds/agent_build_live.exe
```

Third hash differs from both. Three compilations, three hashes, all different, all generated by running the tool.

Now show the disassembly diff:

```bash
cat /demo/builds/diff.txt | head -80
```

Point to the diff output:

**Say out loud:**
> "Same source. Same investigation logic. Three binaries with three different SHA-256 hashes
> and different internal structure. File-reputation databases have no prior hash to match
> against any agent we deploy. Static signature matching has no consistent byte pattern
> to look for."

**If live build fails:** Open VLC, play the pre-recorded 60-second build capture.
Say: "Here is the build we ran earlier this morning" — do not apologize.

---

### STEP 4 — Forge: Polymorphic Deployment Build
**Duration: ~2 min | What judges see: three different binaries for three hosts**

```bash
python3 -m jocky.forge deploy op_falcon.jky --targets HOST-01,HOST-02,HOST-03
```

Output should show three builds with different hashes, entry points, and import hashes:

```
[FORGE] HOST-01 build:
        SHA-256:      bfef7257620c3229...
        Entry point:  0xBDB5
        Import hash:  fa9de4f346957cf6...
        Cert:         FORGE-BUILD-419004 | OP_FALCON_01 / HOST-01

[FORGE] HOST-02 build:
        SHA-256:      880f8c9b17f71888...
        Entry point:  0xA952
        Import hash:  d122ea05ee31a3c8...
        Cert:         FORGE-BUILD-d18818 | OP_FALCON_01 / HOST-02

[FORGE] HOST-03 build:
        SHA-256:      efd6f612f2c150dd...
        Entry point:  0x6D92
        Import hash:  c230e630c1909cd5...
        Cert:         FORGE-BUILD-d087db | OP_FALCON_01 / HOST-03

[FORGE] No shared hash across deployment. Blockchain record updated.
```

**Say out loud:**
> "Three hosts, three structurally distinct binaries. Each certificate-bound to its
> case ID and host identity. An intercepted binary from HOST-01 cannot authenticate
> from HOST-02. The import hash differs per build — imphash detection is defeated."

---

### STEP 5 — Spectre Agent: Process Hollowing (VISUAL)
**Duration: ~3 min | What judges see: Process Hacker showing collector inside svchost**

**This must be visual. Judges need to see Process Hacker, not printed text.**

**Setup before running:**
- Process Hacker 2 open on HOST-01, sorted by PID
- Process Monitor open, filter: WriteFile on .exe or .dll

Run the hollowing:

```bash
python3 -m jocky.spectre deploy --strategy HOLLOW --host HOST-01 --target svchost.exe
```

**Immediately switch to Process Hacker on HOST-01.**

Click on svchost.exe PID 4056. Go to Memory tab.

Show the judges:
- Memory region at the PE base address
- Region type: MEM_IMAGE
- Mapped file: does NOT match `C:\Windows\System32\svchost.exe`
- The JOCKY collector PE is mapped at that base address

Switch to Process Monitor:

```
WriteFile events matching *.exe or *.dll: 0
```

Switch back to console — show collection results arriving:

```
[EVIDENCE] HOST-01 | processes: 187 objects
[EVIDENCE] HOST-01 | network_connections: 34 objects
[EVIDENCE] HOST-01 | persistence_artifacts: 12 objects
```

**Say out loud:**
> "Process Hacker shows the svchost memory region does not match its on-disk image.
> The JOCKY collector is running in that space. Process Monitor shows zero file writes.
> Task Manager shows a normal svchost. The collector is invisible to standard tooling."

**If hollowing fails live:** Play VLC recording. Keep Process Hacker open so judges can
see it was genuinely running — do not close the tool.

---

### STEP 6 — Spectre Agent: Reflective DLL Injection (VISUAL)
**Duration: ~2.5 min | What judges see: API Monitor showing zero LoadLibrary**

**Setup:** API Monitor on HOST-01, filter active for LoadLibrary, LoadLibraryEx, LdrLoadDll.
Process Monitor filter: WriteFile matching *.dll.

Run injection:

```bash
python3 -m jocky.spectre deploy --strategy RDLL --host HOST-01 --target explorer.exe
```

Switch to API Monitor immediately. Show judges the call log:

```
LoadLibrary              [no calls]
LoadLibraryEx            [no calls]
LdrLoadDll               [no calls]
```

Switch to Process Monitor:

```
WriteFile *.dll          [no events]
```

**Say out loud:**
> "API Monitor is running live. Zero LoadLibrary calls. Zero LdrLoadDll calls.
> Our reflective loader resolves its own imports by walking the PEB in memory.
> The Windows loader is never invoked. No DLL appears on disk."

---

### STEP 7 — Spectre Agent: Direct Syscalls + SOCKS5 (VISUAL)
**Duration: ~2.5 min | What judges see: API Monitor + live Wireshark capture**

**Setup:** API Monitor running. Wireshark capturing on HOST-01 NIC, filter: `dns || tcp.port==443`.

Run collection:

```bash
python3 -m jocky.spectre deploy --strategy SYSCALL --host HOST-01
```

Switch to API Monitor. Show:

```
NtQuerySystemInformation    [Direct — no Win32 wrapper]
NtOpenProcess               [Direct — no Win32 wrapper]
WSAConnect                  [0 calls]
connect                     [0 calls]
```

Switch to Wireshark live capture. Show judges the DNS queries as they happen:

```
DNS Query:  yourfunction.azurewebsites.net    → Resolved
DNS Query:  [jocky domain]                    → NOT PRESENT
```

**Say out loud:**
> "Wireshark is capturing live. Every DNS query during the investigation resolves to
> Azure. No JOCKY domain. No investigation infrastructure. An adversary monitoring
> their own network sees routine cloud API traffic."

---

### STEP 8 — Kernel Layer: Hidden Process Detection (VISUAL)
**Duration: ~3 min | What judges see: Task Manager vs JOCKY output side by side**

**Setup:** Split screen — Task Manager on left, JOCKY terminal on right.
DKOM-hidden test process (svc_hidden.exe) already injected and invisible in Task Manager.

Point to Task Manager:

**Say out loud:**
> "Task Manager shows 93 processes. NtQuerySystemInformation returns 93 processes.
> Process Explorer returns 93 processes. Watch what JOCKY's kernel walk returns."

Run kernel collection:

```bash
python3 -m jocky.kernel collect --host HOST-01 --op HIDDEN_PROCESS
```

Output:

```
[KERNEL] EPROCESS walk:      94 processes found
[KERNEL] API enumeration:    93 processes found
[KERNEL] Delta:              1 process hidden from API

HIDDEN PROCESS:
  PID:       4821
  Name:      svc_hidden.exe
  EPROCESS:  0xFFFF8A01C3B40080
  Parent:    1204 (explorer.exe)
  Path:      C:\Users\jdoe\AppData\Local\Temp\svc_hidden.exe
  Status:    INVISIBLE TO ALL USERSPACE ENUMERATION
```

Point to Task Manager — still showing 93. Point to JOCKY output — 94.

**Say out loud:**
> "The process does not exist from userspace. Task Manager, Process Explorer,
> NtQuerySystemInformation — all return 93. Our EPROCESS walk at kernel level
> returns 94. That delta is the hidden process. This artifact is completely
> inaccessible without kernel-level access."

---

### STEP 9 — Kernel Layer: Hook State Collection
**Duration: ~2 min | What judges see: hooks identified with responsible module**

```bash
python3 -m jocky.kernel collect --host HOST-01 --op HOOK_STATE
```

```
HOOK STATE REPORT — HOST-01:
  SSDT hooks:    2
  Inline hooks:  3
  IRP hooks:     0

SSDT HOOKS:
  NtOpenProcess           → SecurityProduct.sys + 0x1B440
  NtQuerySystemInformation → SecurityProduct.sys + 0x1C120

INLINE HOOKS:
  ntdll!NtOpenProcess           → JMP SecurityProduct.sys
  ntdll!NtWriteVirtualMemory    → JMP SecurityProduct.sys
  ntdll!NtQuerySystemInformation → JMP SecurityProduct.sys
```

**Say out loud:**
> "This tells us exactly what is hooked, by which module, and at which address.
> This is why direct syscalls matter — these hooked API paths return filtered results.
> Our syscall stubs go below these hooks directly to the kernel."

---

### STEP 10 — BYOVD Driver Intelligence
**Duration: ~2 min | What judges see: CVE match on live loaded driver**

```bash
python3 -m jocky.kernel collect --host HOST-01 --op BYOVD
```

```
BYOVD INDICATOR DETECTED:
  Driver:       VulnDrv.sys
  CVE:          CVE-2021-21551
  Exploit:      Arbitrary kernel read/write via IOCTL
  Load Time:    2026-09-30 09:31:08 UTC
  Loaded By:    powershell.exe (PID 4892)
  Blocklist:    Present on Microsoft vulnerable driver blocklist

Correlated events:
  → Kernel callback removed:  09:31:09 UTC
  → Process hidden from API:  09:31:10 UTC (PID 4821)

FORENSIC ACTION: CRITICAL finding raised. Correlated with 3 timeline events.
```

**Say out loud:**
> "The CVE-indexed database matched this driver. It then automatically correlated
> the driver load time with the kernel callback removal 1 second later and the
> hidden process 2 seconds after that. That sequence is the adversarial attack path —
> BYOVD loaded, EDR blinded, payload hidden. All reconstructed from evidence."

---

### STEP 11 — Beacon: Cloud-Routed Communication (VISUAL)
**Duration: ~2 min | What judges see: live Wireshark — no JOCKY domain**

**Setup:** Wireshark already capturing from Step 7. Let it run throughout.

Run investigation dispatch and immediately point to Wireshark:

```bash
python3 -m jocky.dispatch op_falcon.jky --targets HOST-01
```

Show Wireshark DNS panel live:

```
DNS Queries during investigation:
  yourfunction.azurewebsites.net    → Resolved (Beacon channel)
  [any jocky domain]               → NOT PRESENT
  [any investigation infrastructure]  → NOT PRESENT
```

Export the capture and show connection summary:

```
Connections during investigation:  1
Destination:  yourfunction.azurewebsites.net:443
Protocol:     TLS 1.3
JOCKY infrastructure visible:  NONE
```

**Say out loud:**
> "Wireshark captured every packet during that investigation.
> One connection. Azure Functions endpoint. TLS 1.3.
> The investigation target monitoring their own network
> sees cloud API traffic. Nothing else."

---

### STEP 12 — Multi-Endpoint Dispatch
**Duration: ~2 min | What judges see: console dispatching to all 3 VMs**

```bash
python3 -m jocky.dispatch op_falcon.jky --targets ALL
```

Show real-time status panel in console updating as each host reports in.

After completion, run a cross-host query:

```bash
python3 -m jocky.query "find file WHERE hash == '7b4c3f2a...92af' ACROSS ALL hosts"
```

```
HOST-01  →  C:\Temp\svc.exe               MATCH
HOST-02  →  /tmp/.svc                     MATCH
HOST-03  →  C:\Windows\Temp\svc.exe       MATCH

Lateral movement indicator: Same payload hash on 3 hosts within 8 minutes.
```

**Say out loud:**
> "One program dispatched to three hosts — Windows and Ubuntu.
> Same evidence model from both. Cross-host query runs across all
> collected artifacts simultaneously. This is environment-level
> investigation, not host-by-host manual work."

---

### STEP 13 — Evidence Graph and Timeline
**Duration: ~2 min | What judges see: interactive graph in console UI**

Switch to Command Console browser UI. Open the Evidence Graph for OP-FALCON-01.

Click through nodes live:
- Click on powershell.exe → show its network relationship to 185.220.x.x
- Click on VulnDrv.sys → show its correlation to callback state change
- Click on svc.exe → show its relationship to the Run key persistence artifact

Open Timeline view. Scroll through chronologically.

**Say out loud:**
> "Every node links to the underlying evidence artifact.
> Every edge documents what the collected evidence shows — not an assertion.
> Investigators click any relationship and verify the raw artifact underneath."

---

### STEP 14 — Correlation Engine → Finding
**Duration: ~2 min | What judges see: multi-signal finding generated live**

```bash
python3 -m jocky.correlate --case OP-FALCON-01 --host HOST-01
```

```
[CORRELATE] Unsigned executable in Temp:         MATCH (E-00422)
[CORRELATE] Rapid outbound connection:           MATCH (E-00455, E-00431)
[CORRELATE] CVE-matched driver in session:       MATCH (E-00441)
[CORRELATE] Kernel callback state change:        MATCH (E-00447)
[CORRELATE] Persistence artifact written:        MATCH (E-00438)
[CORRELATE] Hidden process detected:             MATCH (E-00460)

[ENGINE] 6 signals across 4 rules → FINDING RAISED

Finding ID:   F-CA637
Severity:     CRITICAL
Confidence:   HIGH
Evidence:     8 artifacts
```

**Say out loud:**
> "Six signals across eight evidence artifacts triggered four detection rules.
> No single artifact alone generates a finding.
> Severity is potential impact. Confidence is evidential strength.
> They are separate — the system does not confuse certainty with importance."

---

### STEP 15 — Blockchain Integrity (REAL)
**Duration: ~3 min | What judges see: actual Hyperledger Fabric query output**

**This must be real. Open a terminal showing the Fabric peer.**

First show the peer is running:

```bash
docker ps | grep hyperledger
peer channel list
```

Judges can see the Fabric containers and the channel list confirming the network is live.

Run verification on unmodified evidence:

```bash
python3 -m jocky.integrity verify --evidence-id E-00421 --case OP-FALCON-01
```

This calls the actual Fabric SDK which queries the actual chaincode:

```
[BLOCKCHAIN] Submitting query to Hyperledger Fabric...
[BLOCKCHAIN] Peer:         peer0.org1.example.com
[BLOCKCHAIN] Channel:      jocky-evidence
[BLOCKCHAIN] On-chain hash: 6889780f75bf2c25...7d6a
[BLOCKCHAIN] Current hash:  6889780f75bf2c25...7d6a
[BLOCKCHAIN] Match:         YES
[BLOCKCHAIN] INTEGRITY VERIFIED
```

Now tamper with the evidence file:

```bash
echo "tampered" >> /demo/evidence/E-00421.json
```

Run verification again:

```bash
python3 -m jocky.integrity verify --evidence-id E-00421 --case OP-FALCON-01
```

```
[BLOCKCHAIN] On-chain hash: 6889780f75bf2c25...7d6a
[BLOCKCHAIN] Current hash:  5d73677e2f113bfc...ec4a
[BLOCKCHAIN] Match:         NO
[BLOCKCHAIN] INTEGRITY FAILURE — tamper detected
[BLOCKCHAIN] Detected at:   2026-09-30T10:14:22+00:00
```

**Say out loud:**
> "The Hyperledger Fabric peer is running in that Docker container.
> That query went to the actual chaincode. The hash mismatch is real —
> we literally just appended text to the evidence file and the ledger
> caught it immediately. No single party controls this ledger.
> Multi-org consensus means no one can alter the audit history unilaterally."

**If Fabric peer is down:** Play VLC recording AND show `docker ps` — even if containers
are stopped, showing they exist proves the system was built. Explain the peer went down
due to resource constraints, not that it was never built.

---

### STEP 16 — AI Assistant (SHOW SUCCESS FIRST, THEN REJECTION)
**Duration: ~2.5 min | Critical: show working explanation before the rejection demo**

**Do not open with the rejection demo. Show the assistant working first.**

Query the assistant about Finding F-CA637:

```
> Explain finding F-CA637 and what attack technique this pattern suggests.
```

Assistant response (real LLM output, evidence-grounded):

```
Finding F-CA637 documents a multi-stage execution chain on HOST-01.

A cmd.exe process [E-00421] spawned powershell.exe under an unusual
parent chain. Within 30 seconds, powershell.exe established an
outbound connection to 185.220.101.42:443 [E-00431].

Concurrently, VulnDrv.sys [E-00441] — a CVE-matched driver — was loaded.
One second later, a kernel callback registration was removed [E-00447].
Two seconds after that, a process became invisible to API enumeration [E-00460].

An unsigned PE was created in C:\Temp [E-00422] and a persistence key
was written to HKLM\...\CurrentVersion\Run [E-00438].

The sequence is consistent with BYOVD-assisted EDR blinding followed
by fileless payload staging and persistence establishment.

Evidence basis: [E-00421, E-00422, E-00431, E-00438, E-00441, E-00447, E-00460]
```

**Say out loud:**
> "Every statement cites a specific evidence ID. The assistant is describing
> what the evidence shows — not making independent judgements."

Now show citation validation:

```
> Tell me about evidence artifact E-00999.
```

```
[VALIDATION] Checking cited IDs against case record...
  E-00999 → NOT FOUND IN CASE RECORD
[VALIDATION] Response rejected — invalid citation.
             Assistant response not displayed.
```

**Say out loud:**
> "E-00999 does not exist in this case. The validation layer caught it
> before the response reached the investigator. The assistant cannot
> hallucinate evidence into existence — the case record is the constraint."

---

### STEP 17 — Report Generation
**Duration: ~1.5 min | What judges see: actual PDF opening on screen**

```bash
python3 -m jocky.report generate --case OP-FALCON-01 --format json,pdf
```

```
[REPORT] Generating OP-FALCON-01...
[REPORT] Endpoints:              3
[REPORT] Evidence artifacts:     486
[REPORT] Findings:               1 (CRITICAL)
[REPORT] Blockchain verified:    486/486
[REPORT] PDF: /tmp/jocky_reports/OP-FALCON-01_report.pdf
[REPORT] JSON: /tmp/jocky_reports/OP-FALCON-01_report.json
[REPORT] Complete.
```

**Open the actual PDF on screen.** Scroll through it briefly:
- Show the findings section with F-CA637
- Show the evidence inventory with SHA-256 hashes
- Show the blockchain verification records section
- Show the audit trail

Open the JSON file briefly in a text editor to show the machine-readable format.

**Say out loud:**
> "This PDF is what gets submitted to legal teams or presented in a courtroom.
> Every artifact in it has a blockchain-verified hash.
> The JSON goes into their SIEM or case management system.
> The investigation is completely reproducible — the program that produced this
> is versioned and signed."

---

## If a Judge Asks These Questions

**"Run the LLVM compilation again — show me a fourth hash."**

This is the most likely challenge. You must be ready to compile live on demand.

```bash
python3 -m jocky.forge build op_falcon.jky --output /tmp/agent_judge_test.exe
sha256sum /tmp/agent_judge_test.exe
```

Show the new hash differs from all three previous builds.

---

**"Open that report PDF — can I look at it?"**

Hand them the keyboard or pass the screen. The PDF must be real and openable.
Make sure it has actual content — not a placeholder.

---

**"Would this bypass CrowdStrike Falcon?"**

> "Process hollowing and reflective DLL injection defeat file-system monitoring,
> binary reputation checks, and user-mode API hook detection. Modern EDRs
> including Falcon also instrument kernel-level process creation callbacks.
> That is exactly what Step 9 documented — our kernel callback audit shows us
> what monitoring is active before collection begins. Direct syscalls operate
> below the user-mode hook layer. Kernel callback detection is a separate
> problem that requires kernel-level interaction — which is what the Kernel
> Layer addresses."

Do not claim full Falcon bypass. Claim defeat of specific detection mechanisms
and explain the layered approach.

---

**"Can I run a query myself?"**

Hand them the console. Pre-load a second case with a different scenario so they
can run a cross-host query and see real results come back.

---

**"How does the blockchain know if someone tampers with evidence?"**

> "Every artifact is SHA-256 hashed at the moment of collection. That hash is
> submitted to the Hyperledger Fabric chaincode immediately. The chaincode
> enforces write-once — the on-chain record cannot be overwritten.
> At any future point, you rehash the stored artifact and compare.
> If it was modified after collection, the hashes differ. We just showed that
> live — one appended byte to the file produced a completely different hash
> that the ledger rejected immediately."

---

**"Your AI assistant — what LLM is it using?"**

Name the actual LLM you integrated (Claude API / GPT-4 / Gemini — whichever you built with).
Explain the structured prompt construction and the evidence ID validation layer.
If asked about hallucination: point to Step 16 where the citation validator rejected E-00999.

---

## Fallback Protocol

| Step | Primary | Fallback | How to Switch |
|---|---|---|---|
| LLVM hash diff | Live compilation | Pre-recorded terminal + show pre-built .exe files on disk | "Here is the build from this morning" |
| Process hollowing | Live Process Hacker | Pre-recorded screen capture | Keep Process Hacker open so judges see it was running |
| Direct syscalls | Live API Monitor | Pre-recorded API Monitor trace | Point to filter config to show it was real |
| Wireshark | Live capture | Pre-recorded Wireshark session | Show capture file (.pcapng) as evidence it was captured |
| Blockchain | Live Fabric query | Pre-recorded terminal + show `docker ps` with fabric containers | "Peer went down — containers are still visible" |
| Multi-endpoint | Live dispatch | Pre-collected results, run cross-host query live | Cross-host query can run on pre-collected data |
| AI assistant | Live LLM response | Pre-cached API response displayed | Call it a "cached response from our earlier run" |
| PDF report | Live generation | Pre-generated PDF already on desktop | Open pre-generated PDF — result is identical |

**Rule:** Always attempt live. Switch only when the live attempt clearly fails.
Never open with the fallback. Never apologize — state the fallback naturally.

---

## What Makes This Demo Judge-Proof

**Every critical claim has a real artifact:**
- LLVM mutation → actual .exe files with actual sha256sum output
- Process hollowing → Process Hacker showing real memory map
- Blockchain → actual Fabric peer, actual chaincode query, actual hash comparison
- Report → actual PDF that opens and can be handed to a judge

**The simulation parts are narrated, not claimed:**
- The evidence scenario (svc_hidden.exe, VulnDrv.sys) is a controlled test environment
- Judges know this is a demo environment — they evaluate whether the components work,
  not whether the threat is real

**The three things that break most demos are covered:**
- "Run it again" → LLVM produces a new hash every time, live
- "Open that file" → report PDF is real and openable
- "Is the blockchain actually running" → `docker ps` and `peer channel list` confirm it

---

*JOCKY — From Program to Verified Investigation*
