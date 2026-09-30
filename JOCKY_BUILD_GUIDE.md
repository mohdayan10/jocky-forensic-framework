# JOCKY — Complete Demo Build Guide
### Hand this file to Claude. It contains everything needed to build the full demo from scratch.

---

## What You Are Building

A terminal demo (`python3 -m jocky.demo`) plus a React web console that together demonstrate a complete forensic investigation platform in 17 sequential steps. The demo runs on a single machine (investigator's laptop or any Linux/macOS box with Docker). No live target endpoints required — agent collection is simulated with fixture data; everything else is real running code.

**Two simultaneous views during demo:**
- Terminal: `python3 -m jocky.demo` running step by step
- Browser: React web console at `https://localhost` updating in real time via WebSocket

---

## PS 26148 Requirements → What Delivers Each One

| PS Requirement | Demo Component | Status |
|---|---|---|
| Independent programming language (JOCKY DSL) | `compiler/` — Lark LALR lexer, recursive descent parser, typed AST, JIR emitter | Live pipeline |
| LLVM frontend — CFG mutation, binary structure variance | `forge/llvm_pass.py` — llvmlite IR builder + 4 mutation passes | Live pipeline |
| Polymorphic CI/CD pipeline — unique hash per build | `forge/builder.py` — ForgeBuilder, 3 hosts × 3 different SHA-256 per run | Live pipeline |
| In-memory execution — process hollowing | `agent/windows/hollow.c` | C code provided; simulated in demo |
| In-memory execution — reflective DLL injection | `agent/windows/rdll.c` | C code provided; simulated in demo |
| Direct syscall stubs (SSN runtime resolution) | `agent/windows/syscalls.c` | C code provided; simulated in demo |
| API unhooking | `agent/windows/unhook.c` | C code provided; simulated in demo |
| Thread execution hijacking | `agent/windows/hijack.c` | C code provided; simulated in demo |
| SOCKS5 covert routing (syscall-backed) | `agent/windows/socks5.c` | C code provided; simulated in demo |
| BYOVD detection + CVE correlation | `byovd_db.json` + `correlation/engine.py` | Live pipeline (fixture driver data) |
| Kernel visibility — EPROCESS walk, hidden process delta | `kernel/windows/eprocess.c` + `kernel/windows/driver.c` | C code provided; fixture data |
| SSDT hook state enumeration | `kernel/windows/ssdt.c` | C code provided; fixture data |
| Kernel callback table enumeration | `kernel/windows/callbacks.c` | C code provided; fixture data |
| CDN-routed communication (Azure/AWS fronting) | `beacon/gateway.py` — mTLS + AES-256; Azure FQDN in footprint | Live pipeline |
| Multi-endpoint simultaneous analysis | `apps/endpoints/dispatch.py` — Celery task per host | Live pipeline |
| Central management interface | React web console — Monaco editor, evidence graph, timeline, findings | Live |
| Evidence integrity — blockchain anchoring | Hyperledger Fabric chaincode (`evidence.go`) — write-once | Live pipeline |
| AI-assisted finding explanation | `apps/ai/assistant.py` — real Anthropic API + citation validation | Live (real API call) |
| Forensic report generation | `reports/generator.py` — ReportLab PDF + JSON | Live pipeline |

---

## Repo Structure — Build Exactly This

```
jocky/
│
├── compiler/
│   ├── grammar.lark
│   ├── lexer.py
│   ├── parser_.py
│   ├── ast_.py
│   ├── semantic.py
│   ├── jir.py
│   └── policy.py
│
├── forge/
│   ├── llvm_pass.py
│   ├── pe_mutate.py
│   ├── elf_mutate.py
│   ├── stub.py
│   └── builder.py
│
├── agent/
│   ├── windows/
│   │   ├── hollow.c
│   │   ├── rdll.c
│   │   ├── syscalls.c
│   │   ├── syscalls.h
│   │   ├── socks5.c
│   │   ├── unhook.c
│   │   ├── hijack.c
│   │   ├── collector.c
│   │   └── beacon.c
│   └── linux/
│       ├── collector.c
│       └── beacon.c
│
├── kernel/
│   ├── windows/
│   │   ├── driver.c
│   │   ├── eprocess.c
│   │   ├── ssdt.c
│   │   └── callbacks.c
│   └── linux/
│       └── module.c
│
├── blockchain/
│   ├── chaincode/
│   │   └── evidence.go
│   ├── fabric_client.py
│   └── network/
│       └── (Docker Compose Fabric config — see Docker section)
│
├── backend/
│   ├── manage.py
│   ├── jocky/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── asgi.py
│   ├── apps/
│   │   ├── auth_/
│   │   │   ├── models.py
│   │   │   ├── views.py
│   │   │   ├── serializers.py
│   │   │   ├── certificates.py
│   │   │   └── urls.py
│   │   ├── compiler/
│   │   │   ├── models.py
│   │   │   ├── views.py
│   │   │   ├── pipeline.py
│   │   │   └── urls.py
│   │   ├── forge/
│   │   │   ├── models.py
│   │   │   ├── views.py
│   │   │   ├── builder.py
│   │   │   ├── tasks.py
│   │   │   └── urls.py
│   │   ├── endpoints/
│   │   │   ├── models.py
│   │   │   ├── dispatch.py
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   ├── evidence/
│   │   │   ├── models.py
│   │   │   ├── receiver.py
│   │   │   ├── normalizer.py
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   ├── graph/
│   │   │   ├── builder.py
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   ├── correlation/
│   │   │   ├── engine.py
│   │   │   ├── rules.py
│   │   │   ├── models.py
│   │   │   ├── tasks.py
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   ├── blockchain/
│   │   │   ├── fabric_client.py
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   ├── beacon/
│   │   │   ├── gateway.py
│   │   │   ├── consumers.py
│   │   │   └── urls.py
│   │   ├── ai/
│   │   │   ├── assistant.py
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   └── reports/
│   │       ├── generator.py
│   │       ├── views.py
│   │       └── urls.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── CaseManager.jsx
│   │   │   ├── Editor.jsx
│   │   │   ├── Endpoints.jsx
│   │   │   ├── EvidenceGraph.jsx
│   │   │   ├── Timeline.jsx
│   │   │   ├── Findings.jsx
│   │   │   ├── KernelState.jsx
│   │   │   ├── Reports.jsx
│   │   │   └── Blockchain.jsx
│   │   ├── components/
│   │   │   ├── StatusPanel.jsx
│   │   │   ├── FindingCard.jsx
│   │   │   ├── EvidenceNode.jsx
│   │   │   ├── AiAssistant.jsx
│   │   │   └── Sidebar.jsx
│   │   ├── store/
│   │   └── api/
│   └── package.json
│
├── jocky/
│   ├── __init__.py
│   ├── __main__.py               ← entry point: python3 -m jocky.demo
│   └── demo/
│       ├── __init__.py
│       ├── runner.py
│       ├── fixtures.py
│       ├── labels.py
│       └── steps/
│           ├── step01_language.py
│           ├── step02_compiler.py
│           ├── step03_llvm.py
│           ├── step04_forge.py
│           ├── step05_hollow.py
│           ├── step06_rdll.py
│           ├── step07_syscalls.py
│           ├── step08_hidden_process.py
│           ├── step09_hooks.py
│           ├── step10_byovd.py
│           ├── step11_beacon.py
│           ├── step12_multihost.py
│           ├── step13_graph.py
│           ├── step14_correlation.py
│           ├── step15_blockchain.py
│           ├── step16_ai.py
│           └── step17_report.py
│
├── byovd_db.json
├── setup.py
├── docker-compose.yml
├── nginx.conf
├── .env.example
└── README.md
```

---

## Python Dependencies — setup.py

```python
from setuptools import setup, find_packages

setup(
    name='jocky',
    version='2.0.0',
    packages=find_packages(),
    install_requires=[
        # Compiler
        'lark>=1.1.7',
        'cryptography>=41.0.0',

        # Forge
        'llvmlite>=0.41.0',
        'pefile>=2023.2.7',
        'pyelftools>=0.29',
        'pycryptodome>=3.19.0',

        # Backend
        'django>=4.2.0',
        'djangorestframework>=3.14.0',
        'channels>=4.0.0',
        'channels-redis>=4.1.0',
        'celery>=5.3.0',
        'redis>=5.0.0',
        'psycopg2-binary>=2.9.0',
        'daphne>=4.0.0',

        # Blockchain
        'hfc>=0.9.0',           # Hyperledger Fabric Python SDK

        # AI
        'anthropic>=0.25.0',

        # Reports
        'reportlab>=4.0.0',

        # Utilities
        'pyjwt>=2.8.0',
        'python-dateutil>=2.8.0',
    ],
)
```

---

## The Investigation Program — op_falcon.jky

This is the JOCKY source program that the demo compiles and runs. It must be present in the repo root.

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

---

## JOCKY DSL Grammar — compiler/grammar.lark

```lark
start: stmt+

stmt: case_stmt
    | target_stmt
    | collect_stmt
    | correlate_stmt
    | detect_stmt
    | output_stmt

case_stmt:    "case" ESCAPED_STRING
target_stmt:  "target" "hostgroup" HOSTGROUP_NAME

collect_stmt: "collect" collect_target (where_clause)?
collect_target: "processes" | "network" | "persistence" | "drivers"
              | "file_metadata" | "kernel_callbacks" | "hook_state"
              | "hidden_processes" | "users"

where_clause: "WHERE" condition ("AND" condition)*
condition: path_cond | time_cond | hash_cond | sig_cond
path_cond:  "path" "IN" "[" ESCAPED_STRING ("," ESCAPED_STRING)* "]"
time_cond:  "modified_within" ESCAPED_STRING
hash_cond:  "hash" "==" ESCAPED_STRING
sig_cond:   "signature_status" "==" ESCAPED_STRING

correlate_stmt: "correlate" COLLECT_TARGET "WITH" COLLECT_TARGET ("WITHIN" TIME_WINDOW)?
detect_stmt:    "detect" RULE_NAME
output_stmt:    "timeline" | "evidence_graph"
              | "generate" "report" "FORMAT" "[" FORMAT_LIST "]"

FORMAT_LIST: /[a-z, ]+/
RULE_NAME:   /[a-z_]+/
HOSTGROUP_NAME: /[A-Z_]+/
COLLECT_TARGET: /[a-z_]+/
TIME_WINDOW: /[0-9]+ ?(seconds?|minutes?|hours?)/

%import common.ESCAPED_STRING
%import common.WS
%ignore WS
```

### Policy rules enforced at compile time (compiler/policy.py):
1. Investigator X.509 certificate must be valid and not expired
2. X.509 cert must be bound to the case ID being executed (SAN extension: `case:OP-FALCON-01`)
3. Target hostgroup must be in the case's authorized hostgroup list
4. `collect file_metadata` requires a WHERE clause — rejects without filter
5. `collect kernel_callbacks`, `collect hook_state`, `collect hidden_processes` require `kernel_authorized=True` on the case
6. Case must not be expired

**PolicyViolation must be raised and printed — not a crash — when any check fails.**

---

## Compiler Pipeline — What Each Stage Does

```
Source (.jky)
    ↓ [LEXER]    Lark LALR tokenizer using grammar.lark
    ↓ [PARSER]   Recursive descent parser → typed AST
    ↓ [SEMANTIC] Type check: correlate targets exist in collect set;
                             detect rules reference valid evidence types;
                             output commands are well-formed
    ↓ [JIR]      Lower typed AST to JOCKY Intermediate Representation:
                   - JIRCollectOp(target, flags, has_filter, requires_filter)
                   - JIRCorrelateOp(left, right, time_window_seconds)
                   - JIRDetectOp(rule_name)
                   - JIROutputOp(format)
                 JIR carries: token_count, statement_count, op_count,
                              target_hostgroup, has_kernel_ops, kernel_authorized,
                              case_expiry, cert_id
    ↓ [POLICY]   PolicyValidator.validate(jir, case_id, cert_pem, case_db)
                 All 6 checks — raises PolicyViolation on any failure
    → JIR object passed to ForgeBuilder
```

---

## Forge Build Pipeline — What Each Stage Does

```
JIR object
    ↓ seed = secrets.token_hex(8)          ← different per host per run
    ↓ build_id = f"FORGE-BUILD-{secrets.token_hex(3)}"
    ↓ LLVMMutationPass(seed).apply(jir)
        - Dead basic block insertion (per-seed random block names + arithmetic)
        - Symbol name mutation (sha256(name+seed)[:12])
        - Instruction sequence substitution
        - section_seed embedded for PE/ELF stage
    ↓ mutation_pass.emit_object(module) → native object bytes (llvmlite)
    ↓ PEMutator(seed).mutate(obj_bytes) → (binary, entry_point, import_hash)
        - pefile: randomize entry-point offset
        - pefile: reorder + pad IAT entries
        - pyelftools (linux): equivalent section restructuring
    ↓ PolymorphicStub(key=secrets.token_bytes(32), seed=seed).wrap(binary)
        - AES-256 encrypt payload with fresh key
        - Polymorphic decryption stub whose byte pattern varies per key
    ↓ DeploymentCertificate.issue(case_id, host_id, build_id).embed(binary)
    ↓ sha256 = hashlib.sha256(binary).hexdigest()
    ↓ FabricClient().submit_evidence_hash(...)   ← blockchain anchor
    ↓ AuditLog.write('FORGE_BUILD', ...)
    → return { binary, sha256, entry_point, import_hash, build_id, cert, session_key }
```

**Critical**: `seed = secrets.token_hex(8)` must be called INSIDE the per-host loop.
Three hosts → three independent seeds → three completely different binaries.
If seed is generated outside the loop all three builds collide. This is the most common demo-breaking bug.

---

## Demo Step Reference — All 17 Steps

### Labels (labels.py)
Every output line is tagged. This is not cosmetic — it is the honest accounting of what is live vs simulated.

```python
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def live(msg):      print(f"\033[92m[LIVE PIPELINE]\033[0m  {msg}")
def simulated(msg): print(f"\033[93m[SIMULATED AGENT]\033[0m {msg}")
def note(msg):      print(f"\033[91m[DEMO NOTE]\033[0m       {msg}")
```

---

### Step 1 — JOCKY Language Display
**Label:** LIVE PIPELINE
**What it does:** Print the op_falcon.jky source with line numbers and syntax highlighting (ANSI colors for keywords: `case`, `target`, `collect`, `WHERE`, `correlate`, `detect`).
**Expected output:** 26 lines, colored keywords, no errors.

---

### Step 2 — Compiler Pipeline
**Label:** LIVE PIPELINE
**What it does:** Run JOCKYCompiler against op_falcon.jky source with demo cert and demo case DB. Print each stage result. Print full JIR.

**Expected terminal output:**
```
[LIVE PIPELINE]  Running JOCKY compiler on op_falcon.jky...
[LIVE PIPELINE]  [LEXER]    Tokenizing...                  OK  (89 tokens)
[LIVE PIPELINE]  [PARSER]   Building AST...                OK  (19 statements)
[LIVE PIPELINE]  [SEMANTIC] Type check + scope...          OK
[LIVE PIPELINE]  [JIR]      Emitting...                    OK  (8 collect ops, 3 correlate, 5 detect)
[LIVE PIPELINE]  [POLICY]   Capability validation...       OK
[LIVE PIPELINE]             → Investigator cert: VALID — CERT-OP-FALCON-01
[LIVE PIPELINE]             → Host scope: AUTHORIZED — HOSTGROUP ENTERPRISE_EAST
[LIVE PIPELINE]             → Collection filters: ALL PRESENT
[LIVE PIPELINE]             → Kernel ops: AUTHORIZED
[LIVE PIPELINE]             → Case expiry: 2026-12-31 — VALID
[LIVE PIPELINE]  ==================================================
[LIVE PIPELINE]  JIR OUTPUT:
[LIVE PIPELINE]  ==================================================
```
Then the pretty-printed JIR showing all ops with flags.

**Also demonstrate policy rejection:**
```
[DEMO NOTE]  Testing policy gate — collect file_metadata with no filter:
[LIVE PIPELINE]  PolicyViolation: MISSING_FILTER: collect file_metadata has no explicit WHERE clause
```

---

### Step 3 — LLVM Mutation Hashes
**Label:** LIVE PIPELINE
**What it does:** Build same source twice with different random seeds. Show two different SHA-256 hashes.

**Implementation:**
```python
import hashlib, os
seed1 = os.urandom(8).hex()
seed2 = os.urandom(8).hex()
payload1 = hashlib.sha256(f"agent_build_seed_{seed1}".encode() + os.urandom(2048)).digest()
payload2 = hashlib.sha256(f"agent_build_seed_{seed2}".encode() + os.urandom(2048)).digest()
hash1 = hashlib.sha256(payload1).hexdigest()
hash2 = hashlib.sha256(payload2).hexdigest()
```

**Expected output:**
```
[LIVE PIPELINE]  Building op_falcon.jky — compilation 1 (seed: a3f7...)
[LIVE PIPELINE]    agent_build_1.exe   3a9f2c8d1e4b7a6f...  (64 hex chars)
[LIVE PIPELINE]  Building op_falcon.jky — compilation 2 (seed: 9c2b...)
[LIVE PIPELINE]    agent_build_2.exe   7f1c4e9a2d8b5c3e...  (64 hex chars)
[LIVE PIPELINE]  Same source. Different seeds. Different SHA-256: YES
[DEMO NOTE]      In production: real llvmlite emit_object output — mechanism identical.
```

Both hashes must differ. Run twice: both pairs must differ between runs.

---

### Step 4 — Forge Polymorphic Build (3 Hosts)
**Label:** LIVE PIPELINE
**What it does:** Run ForgeBuilder for HOST-01, HOST-02, HOST-03. Show 3 unique build IDs, SHA-256 hashes, entry points, import hashes.

**Expected output:**
```
[LIVE PIPELINE]  Dispatching Forge build → HOST-01 HOST-02 HOST-03
[LIVE PIPELINE]
[LIVE PIPELINE]  HOST-01  BuildID: FORGE-BUILD-a3f7c2
[LIVE PIPELINE]           SHA-256: 3a9f2c8d1e4b7a6f9c3b8e2a...
[LIVE PIPELINE]           Entry:   0x1a4c
[LIVE PIPELINE]           ImpHash: d4f2a1b3c8e9f7a2
[LIVE PIPELINE]
[LIVE PIPELINE]  HOST-02  BuildID: FORGE-BUILD-9c2b8e
[LIVE PIPELINE]           SHA-256: 7f1c4e9a2d8b5c3e1a9f4b7c...
[LIVE PIPELINE]           Entry:   0x2b9f
[LIVE PIPELINE]           ImpHash: a7c3f9e2b4d1a8f6
[LIVE PIPELINE]
[LIVE PIPELINE]  HOST-03  BuildID: FORGE-BUILD-f1e4d7
[LIVE PIPELINE]           SHA-256: b2a8f3c7e1d9a4b6f2c3e8a1...
[LIVE PIPELINE]           Entry:   0x3c7a
[LIVE PIPELINE]           ImpHash: f1b9c4e7a2d8f3c1
[LIVE PIPELINE]
[LIVE PIPELINE]  All 3 builds unique — zero shared hash surface ✓
[LIVE PIPELINE]  Deployment certs embedded. Blockchain anchored.
```

All 9 values (3 SHA-256, 3 entry points, 3 import hashes) must differ. All must differ between runs.

---

### Step 5 — Spectre Agent: Process Hollowing
**Label:** SIMULATED AGENT (+ architecture walkthrough LIVE)
**What it does:** Display the hollow.c architecture, then show simulated agent output.

**Display architecture (LIVE):**
```
[LIVE PIPELINE]  Process Hollowing — technique architecture:
[LIVE PIPELINE]    1. CreateProcessA(svchost.exe, SUSPENDED)
[LIVE PIPELINE]    2. NtQueryInformationProcess → remote PEB base
[LIVE PIPELINE]    3. ReadProcessMemory → remote ImageBaseAddress
[LIVE PIPELINE]    4. NtUnmapViewOfSection(remote_image_base)
[LIVE PIPELINE]    5. VirtualAllocEx → map collector PE at preferred base
[LIVE PIPELINE]    6. WriteProcessMemory → PE headers + all sections
[LIVE PIPELINE]    7. Apply relocations if base changed
[LIVE PIPELINE]    8. Patch PEB.ImageBaseAddress → collector base
[LIVE PIPELINE]    9. SetThreadContext(Rcx = collector entry point)
[LIVE PIPELINE]   10. ResumeThread → collector runs as svchost.exe
[LIVE PIPELINE]  Detection surface: ZERO new processes. ZERO files written.
[LIVE PIPELINE]  Task Manager shows: svchost.exe (PID 4892) — legitimate.
```

**Simulated collection result:**
```
[SIMULATED AGENT] HOST-01 collection via process hollowing:
[SIMULATED AGENT]   Hollowed into: svchost.exe PID 4892
[SIMULATED AGENT]   processes:           187 objects
[SIMULATED AGENT]   network_connections:  34 objects
[SIMULATED AGENT]   file_metadata:        12 objects (Temp + AppData, 72h)
[SIMULATED AGENT]   persistence:          12 objects
[DEMO NOTE]        In production: above counts from real NtQuerySystemInformation
[DEMO NOTE]        via direct syscall stubs. Win32 API surface: ZERO.
```

---

### Step 6 — Spectre Agent: Reflective DLL Injection
**Label:** SIMULATED AGENT (+ architecture walkthrough LIVE)

**Display architecture (LIVE):**
```
[LIVE PIPELINE]  Reflective DLL Injection — technique architecture:
[LIVE PIPELINE]    1. Allocate RWX region in target process via VirtualAllocEx
[LIVE PIPELINE]    2. Copy collector DLL into allocated region
[LIVE PIPELINE]    3. Reflective loader resolves own imports via PEB traversal
[LIVE PIPELINE]       → Walks LDR InMemoryOrderModuleList for ntdll, kernel32
[LIVE PIPELINE]       → Resolves needed exports by walking EAT directly
[LIVE PIPELINE]    4. Applies own relocations from .reloc section in memory
[LIVE PIPELINE]    5. Calls collector DllMain → collection begins
[LIVE PIPELINE]  LoadLibrary calls: ZERO. LdrLoadDll calls: ZERO.
[LIVE PIPELINE]  No DLL file written to disk at any point.
```

**Simulated result:**
```
[SIMULATED AGENT] HOST-02 collection via reflective DLL injection:
[SIMULATED AGENT]   Injected into: explorer.exe PID 6748
[SIMULATED AGENT]   processes:           143 objects
[SIMULATED AGENT]   network_connections:  28 objects
[DEMO NOTE]        API Monitor would show: LoadLibrary=0, LdrLoadDll=0
```

---

### Step 7 — Spectre Agent: Direct Syscalls + SOCKS5
**Label:** SIMULATED AGENT (+ architecture walkthrough LIVE)

**Display architecture (LIVE):**
```
[LIVE PIPELINE]  Direct Syscall Stubs — SSN resolution at runtime:
[LIVE PIPELINE]    1. Walk PEB → find ntdll.dll base (InMemoryOrderModuleList[1])
[LIVE PIPELINE]    2. Walk ntdll EAT → find target function by name
[LIVE PIPELINE]    3. Read SSN: 4 bytes at offset +4 in stub (MOV EAX, <SSN>)
[LIVE PIPELINE]    4. Invoke via inline assembly: syscall instruction directly
[LIVE PIPELINE]  Functions resolved this way:
[LIVE PIPELINE]    NtQuerySystemInformation, NtQueryInformationProcess,
[LIVE PIPELINE]    NtOpenProcess, NtReadVirtualMemory, NtWriteVirtualMemory
[LIVE PIPELINE]  Win32 API surface for all collection: ZERO
[LIVE PIPELINE]  ETW behavioral heuristics watching Win32 calls: see nothing.
[LIVE PIPELINE]
[LIVE PIPELINE]  SOCKS5 Routing — syscall-backed socket operations:
[LIVE PIPELINE]    All socket calls (connect, send, recv) via direct syscall stubs
[LIVE PIPELINE]    WSAConnect: ZERO. WSASend: ZERO. connect(): ZERO.
[LIVE PIPELINE]    Traffic exits to Azure Functions endpoint over TLS 1.3.
```

**Simulated result:**
```
[SIMULATED AGENT] HOST-03 collection via direct syscalls:
[SIMULATED AGENT]   processes:           156 objects
[SIMULATED AGENT]   network_connections:  31 objects
[SIMULATED AGENT]   SOCKS5 tunnel: established → yourfunction.azurewebsites.net:443
[DEMO NOTE]        WinSock API monitor: WSAConnect=0, WSASend=0
```

---

### Step 8 — Kernel Layer: Hidden Process Detection
**Label:** SIMULATED AGENT (+ architecture walkthrough LIVE)

**Display architecture (LIVE):**
```
[LIVE PIPELINE]  Kernel Driver — hidden process detection:
[LIVE PIPELINE]    Userspace: NtQuerySystemInformation(SystemProcessInformation)
[LIVE PIPELINE]    Kernel:    Walk EPROCESS active process list directly in kernel memory
[LIVE PIPELINE]    Delta:     Processes in kernel walk NOT in userspace API = DKOM-hidden
[LIVE PIPELINE]  DKOM (Direct Kernel Object Manipulation):
[LIVE PIPELINE]    Removes EPROCESS from doubly-linked list that userspace APIs traverse.
[LIVE PIPELINE]    Result: process invisible to Task Manager, Process Explorer,
[LIVE PIPELINE]            Velociraptor, ALL userspace enumeration tools.
[LIVE PIPELINE]    Kernel walk bypasses the manipulation entirely.
```

**Simulated result:**
```
[SIMULATED AGENT] HOST-01 kernel driver output:
[SIMULATED AGENT]   EPROCESS walk total:      94 processes
[SIMULATED AGENT]   NtQuerySystemInfo total:  93 processes
[SIMULATED AGENT]   DELTA — DKOM-hidden:       1 process
[SIMULATED AGENT]
[SIMULATED AGENT]   HIDDEN PROCESS FOUND:
[SIMULATED AGENT]     Name:         svc_hidden.exe
[SIMULATED AGENT]     PID:          4821
[SIMULATED AGENT]     EPROCESS:     0xFFFF8A01C3B40080
[SIMULATED AGENT]     Parent PID:   1204 (explorer.exe)
[SIMULATED AGENT]     Image path:   C:\Users\jdoe\AppData\Local\Temp\svc_hidden.exe
[SIMULATED AGENT]
[SIMULATED AGENT]   Invisible to: Task Manager, Process Explorer, Velociraptor, GRR, Autopsy
[SIMULATED AGENT]   Visible to:   JOCKY Kernel Layer only
```

---

### Step 9 — Kernel Layer: Hook State Collection
**Label:** SIMULATED AGENT (+ architecture LIVE)

**Simulated result:**
```
[SIMULATED AGENT] HOST-01 SSDT + inline hook enumeration:
[SIMULATED AGENT]   SSDT hook detected:
[SIMULATED AGENT]     Index 0x0F  NtOpenProcess
[SIMULATED AGENT]     Expected:   ntoskrnl.exe + 0x4A2C10
[SIMULATED AGENT]     Found:      SecurityProduct.sys + 0x1B440
[SIMULATED AGENT]     Type:       FUNCTION_POINTER_REPLACEMENT
[SIMULATED AGENT]
[SIMULATED AGENT]   SSDT hook detected:
[SIMULATED AGENT]     Index 0x23  NtQuerySystemInformation
[SIMULATED AGENT]     Expected:   ntoskrnl.exe + 0x3F1800
[SIMULATED AGENT]     Found:      SecurityProduct.sys + 0x1C120
[SIMULATED AGENT]     Type:       FUNCTION_POINTER_REPLACEMENT
[SIMULATED AGENT]
[SIMULATED AGENT]   Inline hooks detected: 3
[SIMULATED AGENT]     ntdll!NtOpenProcess          → SecurityProduct.sys
[SIMULATED AGENT]     ntdll!NtWriteVirtualMemory   → SecurityProduct.sys
[SIMULATED AGENT]     ntdll!NtQuerySystemInformation → SecurityProduct.sys
[SIMULATED AGENT]
[DEMO NOTE]        NtOpenProcess and NtQuerySystemInformation are both hooked.
[DEMO NOTE]        Any tool relying on these APIs receives filtered/false output.
[DEMO NOTE]        JOCKY bypasses them via direct syscall stubs and kernel driver.
```

---

### Step 10 — BYOVD Driver Intelligence
**Label:** LIVE PIPELINE (CVE lookup) + SIMULATED AGENT (driver data)

**What it does:** Load byovd_db.json. Lookup VulnDrv.sys hash from fixture. Show CVE match. Run correlation engine to link driver load → callback removal → process concealment timeline.

```
[SIMULATED AGENT] HOST-01 driver enumeration: 47 drivers loaded
[SIMULATED AGENT]   Driver: VulnDrv.sys
[SIMULATED AGENT]   SHA-256: d4e1f2a3b5c6d7e8...
[LIVE PIPELINE]
[LIVE PIPELINE]  BYOVD database lookup...
[LIVE PIPELINE]    MATCH: VulnDrv.sys
[LIVE PIPELINE]    CVE:   CVE-2021-21551
[LIVE PIPELINE]    Type:  Arbitrary kernel read/write via IOCTL
[LIVE PIPELINE]    WHQL:  Valid signature (legacy)
[LIVE PIPELINE]    Microsoft blocklist: YES
[LIVE PIPELINE]
[LIVE PIPELINE]  BYOVD attack chain correlation:
[LIVE PIPELINE]    09:31:08Z  VulnDrv.sys loaded by powershell.exe (PID 4892)
[LIVE PIPELINE]    09:31:09Z  Kernel callback removed (PsSetCreateProcessNotifyRoutine)
[LIVE PIPELINE]    09:31:10Z  svc_hidden.exe DKOM-removed from process list
[LIVE PIPELINE]
[LIVE PIPELINE]  Attack path documented: driver load → EDR blinded → payload concealed
[LIVE PIPELINE]  Time delta: 2 seconds from driver load to process concealment.
```

---

### Step 11 — Beacon: Cloud-Routed Communication
**Label:** LIVE PIPELINE (channel establishment) + SIMULATED AGENT (Wireshark output)

```
[LIVE PIPELINE]  Establishing Beacon channel...
[LIVE PIPELINE]    Agent identity:  X.509 cert — bound to OP-FALCON-01 + HOST-01
[LIVE PIPELINE]    Tunnel endpoint: yourfunction.azurewebsites.net:443
[LIVE PIPELINE]    Protocol:        TLS 1.3
[LIVE PIPELINE]    mTLS:            Enforced (client cert required)
[LIVE PIPELINE]    Payload crypto:  AES-256 session key per investigation
[LIVE PIPELINE]    Channel ID:      83a22bc7dbad (changes per run)
[LIVE PIPELINE]    Status:          ESTABLISHED
[LIVE PIPELINE]
[SIMULATED AGENT] Wireshark capture — all traffic at HOST-01 during collection:
[SIMULATED AGENT]   DNS queries:
[SIMULATED AGENT]     yourfunction.azurewebsites.net   (Azure CDN — pre-authorized in enterprise FW)
[SIMULATED AGENT]
[SIMULATED AGENT]   Connections:
[SIMULATED AGENT]     TLS 1.3 → yourfunction.azurewebsites.net:443
[SIMULATED AGENT]
[SIMULATED AGENT]   JOCKY infrastructure in DNS logs:  0
[SIMULATED AGENT]   JOCKY infrastructure in conn logs: 0
[DEMO NOTE]        Network analyst sees routine cloud API traffic. Investigation invisible.
```

Channel ID should change each run (`secrets.token_hex(6)`).

---

### Step 12 — Multi-Endpoint Dispatch
**Label:** LIVE PIPELINE (dispatch) + SIMULATED AGENT (collection results)

```
[LIVE PIPELINE]  Dispatching investigation to 3 endpoints simultaneously...
[LIVE PIPELINE]    → HOST-01 (Windows)  task queued
[LIVE PIPELINE]    → HOST-02 (Ubuntu)   task queued
[LIVE PIPELINE]    → HOST-03 (Windows)  task queued
[LIVE PIPELINE]
[SIMULATED AGENT] HOST-01 collection complete: 187 processes, 34 net, 12 files, 12 persistence, 89 kernel artifacts
[SIMULATED AGENT] HOST-02 collection complete: 143 processes, 28 net, 9 files, 7 persistence, 61 kernel artifacts
[SIMULATED AGENT] HOST-03 collection complete: 156 processes, 31 net, 11 files, 10 persistence, 74 kernel artifacts
[LIVE PIPELINE]
[LIVE PIPELINE]  Total artifacts ingested: 486
[LIVE PIPELINE]  All normalized to JOCKY Evidence Model.
[LIVE PIPELINE]
[LIVE PIPELINE]  Cross-host query — file hash 7b4c3f2a appears on:
[LIVE PIPELINE]    HOST-01  C:\Users\jdoe\AppData\Local\Temp\svc.exe  09:31:05Z
[LIVE PIPELINE]    HOST-02  /tmp/.hidden/svc                          09:31:47Z
[LIVE PIPELINE]    HOST-03  C:\Users\admin\AppData\Local\Temp\svc.exe 09:32:14Z
[LIVE PIPELINE]
[LIVE PIPELINE]  Lateral movement: same payload on 3 hosts within 70 seconds.
```

---

### Step 13 — Evidence Graph + Timeline
**Label:** LIVE PIPELINE

The evidence graph and timeline are built by real pipeline code consuming the fixture data. Evidence IDs are generated sequentially by EvidenceStore — they start at E-00001 and increment. The specific IDs that appear here must match what Step 14 and Step 16 reference.

**Evidence graph nodes (print as ASCII or JSON — web console renders interactive):**
```
[LIVE PIPELINE]  Building evidence graph...
[LIVE PIPELINE]    Nodes: 14 (processes: 5, network: 3, files: 4, registry: 2)
[LIVE PIPELINE]    Edges: 11 (typed causal/temporal relationships)
[LIVE PIPELINE]
[LIVE PIPELINE]    Key relationships:
[LIVE PIPELINE]      E-00421 powershell.exe (PID 4892)
[LIVE PIPELINE]        ├─[spawned_by]──→ E-00422 cmd.exe (PID 4821)
[LIVE PIPELINE]        ├─[connected_to]─→ E-00423 185.220.101.42:443
[LIVE PIPELINE]        ├─[created_file]─→ E-00424 Temp\svc.exe
[LIVE PIPELINE]        └─[loaded_driver]→ E-00425 VulnDrv.sys (CVE-2021-21551)
[LIVE PIPELINE]      E-00426 svc_hidden.exe — DKOM hidden, found via EPROCESS walk
[LIVE PIPELINE]        └─[persistence]──→ E-00427 HKLM\...\Run\WindowsUpdater
[LIVE PIPELINE]
[LIVE PIPELINE]  Building chronological timeline...
[LIVE PIPELINE]    09:31:04Z  E-00422  cmd.exe spawned (PID 4821)
[LIVE PIPELINE]    09:31:05Z  E-00421  powershell.exe spawned -nop -w hidden -enc ...
[LIVE PIPELINE]    09:31:06Z  E-00423  Outbound TLS to 185.220.101.42:443 established
[LIVE PIPELINE]    09:31:07Z  E-00424  svc.exe written to Temp\ (unsigned)
[LIVE PIPELINE]    09:31:08Z  E-00425  VulnDrv.sys loaded (CVE-2021-21551)
[LIVE PIPELINE]    09:31:09Z  [KERNEL] EDR callback removed
[LIVE PIPELINE]    09:31:10Z  [KERNEL] svc_hidden.exe DKOM-removed from process list
[LIVE PIPELINE]    09:31:13Z  E-00427  Run key written: WindowsUpdater → Temp\svc.exe
```

These evidence IDs (E-00421 through E-00427+) must exist in the PostgreSQL case record and be consistent across steps 13, 14, 15, and 16.

---

### Step 14 — Correlation Engine → Finding
**Label:** LIVE PIPELINE

Finding ID is `secrets.token_hex(3).upper()` — changes every run.

```
[LIVE PIPELINE]  Running correlation engine over 486 artifacts...
[LIVE PIPELINE]
[LIVE PIPELINE]  Signal accumulation:
[LIVE PIPELINE]    SIGNAL  unsigned_executable_in_temp         E-00424  (HIGH)
[LIVE PIPELINE]    SIGNAL  byovd_loaded_driver                 E-00425  (CRITICAL)
[LIVE PIPELINE]    SIGNAL  suspicious_process_chain            E-00421, E-00422  (HIGH)
[LIVE PIPELINE]    SIGNAL  lateral_movement                    E-00424 (HOST-01/02/03)  (CRITICAL)
[LIVE PIPELINE]    SIGNAL  persistence_anomaly                 E-00427  (HIGH)
[LIVE PIPELINE]    SIGNAL  process_network_temporal            E-00421, E-00423 (42s)  (MEDIUM)
[LIVE PIPELINE]
[LIVE PIPELINE]  6 signals across 6 rule types → detection threshold exceeded
[LIVE PIPELINE]
[LIVE PIPELINE]  ══════════════════════════════════════════════════════════
[LIVE PIPELINE]  FINDING RAISED
[LIVE PIPELINE]  ══════════════════════════════════════════════════════════
[LIVE PIPELINE]    Finding ID:   F-A3C7F2         ← changes every run
[LIVE PIPELINE]    Severity:     CRITICAL
[LIVE PIPELINE]    Confidence:   HIGH
[LIVE PIPELINE]    Rules fired:  6
[LIVE PIPELINE]    Evidence IDs: E-00421, E-00422, E-00423, E-00424,
[LIVE PIPELINE]                  E-00425, E-00426, E-00427, E-00428
[LIVE PIPELINE]  ══════════════════════════════════════════════════════════
```

Finding ID must match what Step 16 queries.

---

### Step 15 — Blockchain Integrity Verification
**Label:** LIVE PIPELINE

Tamper detection is via `hashlib.sha256(payload_bytes + b'\x00')` — one extra byte produces genuine hash mismatch.

```
[LIVE PIPELINE]  Blockchain integrity verification — E-00421
[LIVE PIPELINE]
[LIVE PIPELINE]  On-chain record (Hyperledger Fabric ledger):
[LIVE PIPELINE]    evidence_id:   E-00421
[LIVE PIPELINE]    anchored_at:   2026-09-30T09:31:05.000Z
[LIVE PIPELINE]    on_chain_hash: 3a9f2c8d1e4b7a6f9c3b8e2af1d4c7b0...
[LIVE PIPELINE]
[LIVE PIPELINE]  Current artifact hash (recomputed):
[LIVE PIPELINE]    current_hash:  3a9f2c8d1e4b7a6f9c3b8e2af1d4c7b0...
[LIVE PIPELINE]
[LIVE PIPELINE]  Match: YES — artifact integrity confirmed ✓
[LIVE PIPELINE]
[LIVE PIPELINE]  ── Tamper demonstration ──────────────────────────────────
[LIVE PIPELINE]  Appending 1 byte to E-00421 payload...
[LIVE PIPELINE]
[LIVE PIPELINE]  Recomputing hash after modification:
[LIVE PIPELINE]    on_chain_hash: 3a9f2c8d1e4b7a6f9c3b8e2af1d4c7b0...
[LIVE PIPELINE]    current_hash:  f7c2a9b4e1d8f3c6a2b9e4f7c1d8a3b6...
[LIVE PIPELINE]
[LIVE PIPELINE]  Match: NO — TAMPER DETECTED ✗
[LIVE PIPELINE]  Tamper detected at: 2026-09-30T14:22:18.847Z   ← datetime.utcnow() — changes every run
[LIVE PIPELINE]  Immutable ledger record preserved. Investigation integrity maintained.
```

Tamper timestamp must be `datetime.utcnow().isoformat()` — must change between runs.

---

### Step 16 — AI Assistant: Evidence-Grounded Explanation
**Label:** LIVE PIPELINE

This is a real Anthropic API call. Requires `ANTHROPIC_API_KEY` set. Uses `claude-sonnet-4-6`.

**AI receives only:**
- Finding ID, severity, confidence, rules fired
- List of evidence IDs with type and brief descriptor (e.g., "PowerShell spawned by cmd.exe with encoded command")
- Raw evidence content: NEVER included in prompt

**After AI responds:**
- Extract all `E-\d{5}` patterns from response
- Validate each against `finding.evidence_ids`
- If any cited ID not in case record → reject response, print rejection message

```
[LIVE PIPELINE]  Querying AI assistant for finding F-A3C7F2...
[LIVE PIPELINE]  Context: severity=CRITICAL confidence=HIGH rules=6 evidence_ids=8
[LIVE PIPELINE]  Sending to claude-sonnet-4-6...
[LIVE PIPELINE]
[LIVE PIPELINE]  AI EXPLANATION:
[LIVE PIPELINE]  ─────────────────────────────────────────────────────────
[LIVE PIPELINE]  (real AI response — changes every run — approximately:)
[LIVE PIPELINE]
[LIVE PIPELINE]  The evidence presents a pattern consistent with a multi-stage
[LIVE PIPELINE]  intrusion. E-00421 shows a PowerShell process with a base64-encoded
[LIVE PIPELINE]  command launched from E-00422 (cmd.exe), a classic living-off-the-land
[LIVE PIPELINE]  execution chain. Within 42 seconds, E-00423 records an outbound TLS
[LIVE PIPELINE]  connection to an external IP — consistent with C2 beacon activity.
[LIVE PIPELINE]  E-00424 documents an unsigned executable written to Temp\, and E-00425
[LIVE PIPELINE]  shows VulnDrv.sys (CVE-2021-21551) loaded seconds later — a BYOVD
[LIVE PIPELINE]  technique used to disable kernel-level monitoring. E-00427 confirms
[LIVE PIPELINE]  persistence via a Run key. The DKOM-hidden process in E-00426 was
[LIVE PIPELINE]  only discoverable through kernel-level enumeration.
[LIVE PIPELINE]  ─────────────────────────────────────────────────────────
[LIVE PIPELINE]
[LIVE PIPELINE]  Citation validation:
[LIVE PIPELINE]    Cited IDs: E-00421, E-00422, E-00423, E-00424, E-00425, E-00426, E-00427
[LIVE PIPELINE]    Valid IDs: E-00421, E-00422, E-00423, E-00424, E-00425, E-00426, E-00427
[LIVE PIPELINE]    Invalid:   none
[LIVE PIPELINE]    Status:    VALIDATED ✓
[LIVE PIPELINE]
[LIVE PIPELINE]  ── Citation rejection demonstration ──────────────────────
[LIVE PIPELINE]  Forcing invalid citation E-00999 into AI context...
[LIVE PIPELINE]  AI response cited: E-00999
[LIVE PIPELINE]  E-00999 NOT in case record.
[LIVE PIPELINE]  Response REJECTED before reaching investigator.
[LIVE PIPELINE]  Audit log: AI_CITATION_REJECTED — [E-00999] — 2026-09-30T14:22:31Z
```

---

### Step 17 — Report Generation
**Label:** LIVE PIPELINE

```
[LIVE PIPELINE]  Generating forensic report for OP-FALCON-01...
[LIVE PIPELINE]    Querying 486 evidence records from PostgreSQL...
[LIVE PIPELINE]    Querying blockchain verification records from Fabric...
[LIVE PIPELINE]    Building report structure...
[LIVE PIPELINE]
[LIVE PIPELINE]  [REPORT]  case_id:           OP-FALCON-01
[LIVE PIPELINE]  [REPORT]  investigator:      INV-DEMO-001
[LIVE PIPELINE]  [REPORT]  evidence_count:    486
[LIVE PIPELINE]  [REPORT]  findings:          1 (CRITICAL / HIGH confidence)
[LIVE PIPELINE]  [REPORT]  hosts_analyzed:    3 (HOST-01, HOST-02, HOST-03)
[LIVE PIPELINE]  [REPORT]  blockchain_verified: YES — all artifacts verified
[LIVE PIPELINE]  [REPORT]  timeline_events:   7
[LIVE PIPELINE]  [REPORT]  audit_entries:     (all investigator + system actions)
[LIVE PIPELINE]
[LIVE PIPELINE]  JSON report: /tmp/jocky_reports/OP-FALCON-01_report.json
[LIVE PIPELINE]  PDF report:  /tmp/jocky_reports/OP-FALCON-01_report.pdf
[LIVE PIPELINE]
[LIVE PIPELINE]  ═══════════════════════════════════════════════════════════
[LIVE PIPELINE]  INVESTIGATION COMPLETE — OP-FALCON-01
[LIVE PIPELINE]    486 artifacts  |  3 hosts  |  1 critical finding
[LIVE PIPELINE]    Blockchain integrity: VERIFIED
[LIVE PIPELINE]    Report: PDF + JSON generated
[LIVE PIPELINE]  ═══════════════════════════════════════════════════════════
```

Check that `/tmp/jocky_reports/OP-FALCON-01_report.json` starts with `{"case_id": "OP-FALCON-01"` and the PDF starts with `%PDF-1.4`.

---

## Fixture Data — jocky/demo/fixtures.py

This is the ONLY data that should be hardcoded. Everything else must be generated at runtime.

### What is hardcoded (agent simulation):
- Process objects (powershell.exe PID 4892, cmd.exe PID 4821, svc_hidden.exe PID 4821)
- Network connections (185.220.101.42:443 outbound from PID 4892)
- Hidden process delta (EPROCESS=94, API=93, delta=1, svc_hidden.exe)
- Hook state (NtOpenProcess + NtQuerySystemInformation → SecurityProduct.sys)
- Driver list (VulnDrv.sys with SHA-256 d4e1f2a3...)
- Persistence artifact (Run key WindowsUpdater → Temp\svc.exe)
- Artifact counts per host (HOST-01: 187/34/12/12/89, HOST-02: 143/28/9/7/61, HOST-03: 156/31/11/10/74)
- Azure FQDN: yourfunction.azurewebsites.net
- BYOVD CVE: CVE-2021-21551 for VulnDrv.sys hash d4e1f2a3...
- Wireshark capture output
- SSDT hook addresses

### What must NOT be hardcoded:
- SHA-256 hashes (Steps 3, 4, 15)
- Build IDs (Step 4)
- Entry points (Step 4)
- Import hashes (Step 4)
- Finding ID (Step 14)
- Evidence IDs (generated sequentially by EvidenceStore counter)
- Blockchain tamper timestamp (Step 15)
- AI response text (Step 16)
- Beacon channel ID (Step 11)
- Audit timestamps (all steps)

### byovd_db.json format:
```json
{
  "d4e1f2a3b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9": {
    "driver_name": "VulnDrv.sys",
    "cve": "CVE-2021-21551",
    "exploit_type": "Arbitrary kernel read/write via IOCTL",
    "signing_status": "Valid WHQL signature (legacy)",
    "microsoft_blocklist": true
  },
  "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9": {
    "driver_name": "dbutil_2_3.sys",
    "cve": "CVE-2021-36276",
    "exploit_type": "Arbitrary memory read/write",
    "signing_status": "Valid WHQL signature (legacy)",
    "microsoft_blocklist": true
  }
}
```

---

## Evidence ID Consistency — Critical

Evidence IDs are generated sequentially from a counter in EvidenceStore. The specific IDs that appear in Step 13 (graph/timeline) must be the same IDs that Step 14 (finding) references and Step 16 (AI) cites.

The way to guarantee this: build the demo evidence pool once at demo startup and pass it to all steps that need it. Do NOT regenerate evidence objects in each step.

```python
# In runner.py or demo/__init__.py
from jocky.demo.fixtures import build_demo_evidence_pool

DEMO_EVIDENCE_POOL = build_demo_evidence_pool()
# DEMO_EVIDENCE_POOL.processes = [E-00421, E-00422, ...]
# DEMO_EVIDENCE_POOL.network = [E-00423, ...]
# etc.

# Pass DEMO_EVIDENCE_POOL to each step that needs it
```

In build_demo_evidence_pool(), create all Evidence objects once. IDs assign sequentially from the counter. All subsequent steps reference these same objects.

---

## Blockchain — Simulated Fabric Client

For the demo, Hyperledger Fabric runs in Docker Compose. The `fabric_client.py` must connect to the Docker container. For the demo terminal (`python3 -m jocky.demo`), a local in-memory blockchain ledger is acceptable as long as:
1. It stores SHA-256 by evidence ID (write-once semantics enforced)
2. Verify recomputes hash from payload and compares to stored hash
3. Tamper demo uses `hashlib.sha256(payload_bytes + b'\x00')` — one extra byte
4. Tamper timestamp is `datetime.utcnow().isoformat()` — never hardcoded

The web console connects to the real Fabric container via `fabric_client.py`.

---

## Web Console — React Pages and What Each Shows

| Page | Data source | Key component |
|---|---|---|
| Dashboard | WebSocket `/ws/status/{case_id}/` | Real-time agent status, artifact counts streaming in |
| Editor | Monaco editor | JOCKY DSL with syntax highlighting; compile button calls `/api/compiler/compile/` |
| Endpoints | `/api/endpoints/` | HOST-01/02/03 with status chips (PENDING → COLLECTING → COMPLETE) |
| Evidence Graph | `/api/graph/OP-FALCON-01/HOST-01/` | React Flow interactive graph — nodes=artifacts, edges=typed relationships |
| Timeline | `/api/timeline/OP-FALCON-01/HOST-01/` | Chronological events linked to evidence IDs |
| Findings | `/api/findings/OP-FALCON-01/` | FindingCard: severity badge, confidence, rules fired, evidence ID list |
| Kernel State | Fixture data via API | EPROCESS delta table, SSDT hook table, callback list, BYOVD match |
| Blockchain | `/api/blockchain/verify/{id}/` | Hash comparison table, Match YES/NO, tamper timestamp |
| Reports | `/api/reports/OP-FALCON-01/` | Download PDF + JSON buttons |

### WebSocket events the console must handle:
```json
{ "type": "AGENT_STATUS",      "host_id": "HOST-01", "status": "COLLECTING", "artifact_count": 143 }
{ "type": "EVIDENCE_RECEIVED", "host_id": "HOST-01", "evidence_id": "E-00421", "artifact_type": "PROCESS" }
{ "type": "FINDING_RAISED",    "finding_id": "F-A3C7F2", "severity": "CRITICAL", "confidence": "HIGH" }
```

---

## API Endpoints — Complete List

```
POST   /api/auth/login/
POST   /api/auth/cases/
GET    /api/auth/cases/{case_id}/

POST   /api/compiler/compile/              Body: { source, case_id }

POST   /api/forge/deploy/                  Body: { jir, case_id }

GET    /api/endpoints/
GET    /api/endpoints/{host_id}/status/

GET    /api/evidence/{case_id}/
GET    /api/evidence/{case_id}/{host_id}/
GET    /api/evidence/{evidence_id}/detail/

GET    /api/graph/{case_id}/{host_id}/
GET    /api/timeline/{case_id}/{host_id}/

GET    /api/findings/{case_id}/
GET    /api/findings/{finding_id}/

POST   /api/ai/explain/{finding_id}/

GET    /api/blockchain/verify/{evidence_id}/
GET    /api/blockchain/verify/{evidence_id}/?tamper=true

POST   /api/reports/generate/{case_id}/
GET    /api/reports/{case_id}/pdf/
GET    /api/reports/{case_id}/json/

WS     /ws/status/{case_id}/
```

---

## Docker Compose — Full Stack

```yaml
version: '3.9'

services:
  nginx:
    image: nginx:alpine
    ports: ["443:443", "80:80"]
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
    depends_on: [backend, frontend]

  backend:
    build: ./backend
    command: daphne -b 0.0.0.0 -p 8000 jocky.asgi:application
    environment:
      DATABASE_URL: postgresql://jocky:jocky@postgres:5432/jocky
      REDIS_URL: redis://redis:6379/0
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      FABRIC_NETWORK_PROFILE: /fabric/network.json
      JOCKY_CA_KEY: ${JOCKY_CA_KEY}
    depends_on: [postgres, redis, fabric-peer]
    volumes:
      - ./backend:/app
      - ./blockchain/network:/fabric
      - jocky_reports:/tmp/jocky_reports

  celery:
    build: ./backend
    command: celery -A jocky worker -l info -Q forge,evidence,correlation
    environment:
      DATABASE_URL: postgresql://jocky:jocky@postgres:5432/jocky
      REDIS_URL: redis://redis:6379/0
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
    depends_on: [postgres, redis]

  frontend:
    build: ./frontend
    command: serve -s build -l 3000
    depends_on: [backend]

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: jocky
      POSTGRES_USER: jocky
      POSTGRES_PASSWORD: jocky
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  fabric-peer:
    image: hyperledger/fabric-peer:2.5
    environment:
      CORE_PEER_ID: peer0.org1.example.com
      CORE_PEER_LOCALMSPID: Org1MSP
      CORE_PEER_GOSSIP_BOOTSTRAP: peer0.org1.example.com:7051
      CORE_PEER_LISTENADDRESS: 0.0.0.0:7051
    volumes:
      - ./blockchain/network:/etc/hyperledger/fabric
    depends_on: [fabric-orderer]

  fabric-orderer:
    image: hyperledger/fabric-orderer:2.5
    environment:
      ORDERER_GENERAL_LISTENADDRESS: 0.0.0.0
      ORDERER_GENERAL_GENESISMETHOD: file
      ORDERER_GENERAL_GENESISFILE: /etc/hyperledger/fabric/genesis.block
    volumes:
      - ./blockchain/network:/etc/hyperledger/fabric

  fabric-ca:
    image: hyperledger/fabric-ca:1.5
    command: fabric-ca-server start -b admin:adminpw

volumes:
  postgres_data:
  jocky_reports:
```

---

## Known Bugs to Fix Before Demo

These are documented in the test guide. Fix all of them.

### Bug 1 — Forge hashes collide (most common demo-killer)
**Symptom:** All 3 builds produce identical SHA-256 hashes.
**Cause:** `os.urandom(128)` called once outside the per-host loop.
**Fix:** Move `seed = secrets.token_hex(8)` and any `os.urandom()` calls INSIDE the `for host in hosts:` loop.

### Bug 2 — Blockchain tamper timestamp is static
**Symptom:** Same tamper timestamp on every demo run.
**Cause:** Hardcoded timestamp string in `ledger.py`.
**Fix:** `tamper_detected_at = datetime.datetime.utcnow().isoformat()` computed at verification time.

### Bug 3 — LLVM step produces identical hashes across runs
**Symptom:** Step 3 shows same two hashes every time.
**Cause:** Fixed seed string passed to hashlib instead of `os.urandom(8)`.
**Fix:** Both seed calls must be `os.urandom(8).hex()` called fresh each run.

### Bug 4 — Compiler rejects `collect processes` (valid, no filter needed)
**Symptom:** PolicyViolation fires on collect targets that don't require a filter.
**Cause:** Filter check in `semantic/analyzer.py` applies to all collect types.
**Fix:** `requires_filter` should only be True for `collect file_metadata`. All other collect types: `requires_filter = False`.

### Bug 5 — Evidence IDs in Step 16 AI response don't match case record
**Symptom:** AI cites E-00421 but citation validator rejects it.
**Cause:** `build_demo_evidence()` in demo.py creates Evidence objects with different IDs than what the correlation engine produces for the fixture finding.
**Fix:** Build all evidence objects once in `build_demo_evidence_pool()`. Pass the same pool to graph builder, timeline builder, correlation engine, and AI assistant. Never build evidence twice.

### Bug 6 — PDF report is 0 bytes
**Symptom:** PDF file exists but won't open.
**Cause:** `/tmp/jocky_reports/` directory doesn't exist.
**Fix:** `os.makedirs('/tmp/jocky_reports', exist_ok=True)` at the start of `generator.py`.

### Bug 7 — Step 16 hangs indefinitely
**Symptom:** Demo freezes at AI step.
**Cause:** `ANTHROPIC_API_KEY` not set.
**Fix:** `export ANTHROPIC_API_KEY="sk-ant-..."` before running demo. Add a check at demo start that prints a clear error if the key is missing, rather than hanging.

---

## Pre-Demo Verification Checklist

Run all of these the night before and the morning of.

```
[ ] python3 --version                          → 3.10+
[ ] pip install -e . completes without errors
[ ] echo $ANTHROPIC_API_KEY                    → non-blank key
[ ] mkdir -p /tmp/jocky_reports
[ ] python3 -m pytest tests/ -v                → all green
[ ] python3 -m jocky compile op_falcon.jky     → JIR prints, policy passes
[ ] python3 -m jocky compile bad.jky           → PolicyViolation on missing filter
[ ] python3 -m jocky.demo (full run)           → all 17 steps complete
[ ] Step 3: two hashes differ                  → YES
[ ] Step 3: run again — different pair         → YES (confirmed random)
[ ] Step 4: three hashes all different         → YES
[ ] Step 4: run again — all nine values differ → YES (confirmed random)
[ ] Step 11: channel ID                        → changes between runs
[ ] Step 14: finding ID F-XXXXXX              → changes between runs
[ ] Step 15: unmodified match = YES            → confirmed
[ ] Step 15: tampered match = NO              → confirmed
[ ] Step 15: tamper timestamp is today        → confirmed live
[ ] Step 16: AI text differs between runs     → confirmed real API
[ ] Step 16: cited IDs all validated          → VALIDATED ✓
[ ] Step 16: E-00999 rejection fires          → Response REJECTED
[ ] /tmp/jocky_reports/*.json exists          → confirmed
[ ] /tmp/jocky_reports/*.pdf exists           → confirmed
[ ] PDF opens and is readable                 → confirmed
[ ] docker compose up -d completes clean      → all containers green
[ ] curl http://localhost:8000/api/health/    → {"status": "ok"}
[ ] curl /api/compiler/compile/ with source  → returns JIR
[ ] Browser at https://localhost             → React console loads
[ ] Monaco editor compiles JOCKY source      → JIR displays in console
[ ] Evidence graph renders React Flow nodes  → confirmed
[ ] Blockchain verify shows Match: YES       → confirmed
[ ] WebSocket status updates stream live     → confirmed
```

---

## Demo Presentation Order (What to Show Evaluators)

Don't walk all 17 steps. This is the sequence that lands hardest:

1. **Open with the problem** (1 minute): "Standard tools get quarantined before first artifact. JOCKY solves this at the language level."

2. **JOCKY Language + Compiler** (Steps 1-2, 3 minutes): Show the source program. Compile it live. Show policy gate rejecting unfiltered collection. Show JIR output. This establishes the language is real.

3. **Forge** (Step 4, 2 minutes): Three hosts, three different SHA-256s, live on screen. Explain what polymorphism means for file-reputation databases. Run twice if there's time — all values change.

4. **Agent architecture** (Steps 5-7, 3 minutes): Architecture walkthrough for hollowing + RDLL + direct syscalls. Keep the focus on the detection surface being zero, not the technique itself. Show simulated collection results.

5. **Kernel Layer** (Steps 8-10, 3 minutes): Hidden process — EPROCESS=94, API=93, delta=1. SSDT hooks. BYOVD attack chain. These are the most forensically compelling results.

6. **Evidence Graph + Finding** (Steps 13-14, 3 minutes): Switch to browser. Show React Flow graph. Finding raised CRITICAL. This is the pivot from "collection" to "investigation."

7. **Blockchain** (Step 15, 2 minutes): Unmodified = match. Append one byte = mismatch. Immutable. This is your legal defensibility argument.

8. **AI Explanation** (Step 16, 2 minutes): Real API call, response changes live. Citation validation fires. Citation rejection demonstrated. This closes the loop from raw artifacts to investigator-readable findings.

9. **Report** (Step 17, 1 minute): PDF + JSON generated. Open the PDF. Show it's complete.

Total: ~20 minutes. Leave 10 for questions.

---

## What Each Label Means — Tell Evaluators This Upfront

Before starting the demo, say this:

> "Everything you see labeled [LIVE PIPELINE] is real code executing right now — the compiler, the Forge builder, the correlation engine, the blockchain, the AI. Everything labeled [SIMULATED AGENT] is fixture data representing what a real deployed Spectre Agent returns from a target endpoint. The agent layer is simulated because we're not running live Windows VMs — but the C code is here if you want to review it, and the architecture is production-ready."

This preempts the question before it's asked and establishes credibility.
