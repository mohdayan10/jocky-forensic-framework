# JOCKY Web Console — Build Spec

## Overview

Build the web console that runs alongside the JOCKY demo terminal (`python3 -m jocky.demo`). Terminal on left, browser on right, updates in real time as each step runs.

---

## Pages

### Login
- Simple username/password form
- JWT stored in localStorage
- Redirects to Dashboard on success
- Hardcoded credentials: `investigator` / `jocky2024`

---

### Dashboard
- Three host cards: HOST-01 (Windows), HOST-02 (Ubuntu), HOST-03 (Windows)
- Each card shows:
  - Status chip: PENDING → COLLECTING → COMPLETE
  - Artifact count
  - Agent Build ID (FORGE-BUILD-xxxxxx)
  - Collection progress bar
- Status updates via WebSocket `/ws/status/OP-FALCON-01/`
- Auto-advances as terminal steps run

---

### Editor
- Monaco code editor (dark theme) pre-loaded with `op_falcon.jky` source
- Left panel: editor
- Right panel: compiler output
- "Compile" button calls `POST /api/compiler/compile/`
- On success: JIR output in right panel + green [POLICY] PASSED badge
- On policy violation: red [POLICY] REJECTED badge with violation message
- Syntax highlighting for: `case`, `target`, `collect`, `correlate`, `detect`, `WHERE`, `AND`

---

### Endpoints
Table: Host ID | Platform | Agent Build ID | SHA-256 (truncated 16 chars) | Entry Point | Status

- Populated from Step 4 Forge output
- All three rows show different SHA-256 values

---

### Evidence Graph
- React Flow interactive graph
- Node colors by type:
  - process = blue
  - network = orange
  - file = green
  - registry = purple
  - driver = red
  - kernel = dark red
- Edge labels: spawned, connected_to, created, loaded, modified, persistence
- Click node → side panel with full evidence detail (ID, type, SHA-256, timestamp, host)
- Exact graph from Step 13:
  - cmd.exe → powershell.exe → 185.220.101.42:443
  - cmd.exe → VulnDrv.sys
  - cmd.exe → svc.exe
  - cmd.exe → Run key
  - svc_hidden.exe

---

### Timeline
- Chronological event list
- Each row: timestamp | event description | evidence ID badge | severity chip
- Events from Step 13 (09:31:02 through 09:31:17)
- Evidence ID badges clickable → navigates to artifact in Evidence Graph
- Auto-scrolls as new events arrive via WebSocket

---

### Findings
- Finding card for F-XXXXXX (ID read from API each run)
- Card shows:
  - Severity badge: CRITICAL (red)
  - Confidence badge: HIGH
  - Rules fired list (6 rules)
  - Evidence ID chips (8 chips, each clickable)
- "Ask AI" button → calls `POST /api/ai/explain/{finding_id}/`
- Streams AI explanation into panel below
- Citation validation result shown after load: VALIDATED ✓ (green)

---

### Kernel State
Three sections:

1. **EPROCESS Delta table**
   - EPROCESS Walk: 94 | API Result: 93 | Delta: 1
   - Hidden process row highlighted red: `svc_hidden.exe` PID 4821 `C:\Users\jdoe\AppData\Local\Temp\svc_hidden.exe`

2. **SSDT Hook table**
   - Two rows: NtOpenProcess, NtQuerySystemInformation
   - Columns: expected module vs found module (SecurityProduct.sys), hook type

3. **BYOVD Match card**
   - VulnDrv.sys | CVE-2021-21551 | Arbitrary kernel read/write via IOCTL | Microsoft blocklist: YES
   - Attack chain timeline: driver load → callback removed → process hidden (with timestamps)

---

### Blockchain
Two panels side by side:

- **Left:** Evidence ID input + "Verify" button
  - Shows: on-chain hash, current hash, Match: YES (green) or Match: NO TAMPER DETECTED (red), tamper timestamp if mismatch

- **Right:** "Run Tamper Demo" button
  - Calls tamper endpoint, auto-runs verify, shows mismatch in red
  - Both panels update live

---

### Reports
- Case summary stats: 486 artifacts, 3 hosts, 1 finding
- Download buttons: "Download PDF" and "Download JSON"
  - `GET /api/reports/OP-FALCON-01/pdf/`
  - `GET /api/reports/OP-FALCON-01/json/`
- Report contents checklist (from Step 17 terminal output) with green checkmarks

---

### Sidebar (persistent)
- Fixed left nav with icons + labels for all 9 pages
- Active page highlighted
- Case ID "OP-FALCON-01" at top
- Investigation status indicator: ACTIVE (green)

---

## Tech Stack

### Frontend
- React 18 + React Router v6
- Tailwind CSS dark theme throughout (`bg-gray-900`, `bg-gray-800`)
- Monaco Editor (`@monaco-editor/react`) for Editor page
- React Flow (`reactflow`) for Evidence Graph
- Recharts for charts
- Native browser WebSocket → `ws://localhost:8000/ws/status/OP-FALCON-01/`
- Axios for all HTTP → `http://localhost:8000/api/`

### Backend
- Django Channels WebSocket consumer at `/ws/status/{case_id}/`
- All API responses use fixture data from `jocky/demo/fixtures.py`

---

## WebSocket Events

```json
{"type": "AGENT_STATUS", "host_id": "HOST-01", "status": "COLLECTING", "artifact_count": 143}
{"type": "EVIDENCE_RECEIVED", "host_id": "HOST-01", "evidence_id": "E-00421", "artifact_type": "PROCESS"}
{"type": "FINDING_RAISED", "finding_id": "F-905C37", "severity": "CRITICAL", "confidence": "HIGH"}
```

---

## API Endpoints

```
POST /api/auth/login/                          → { token }
POST /api/compiler/compile/                    → { jir } or { error }
GET  /api/forge/builds/OP-FALCON-01/           → { builds: [{host_id, sha256, entry_point, build_id}] }
GET  /api/endpoints/                           → { endpoints: [{host_id, platform, status, artifact_count}] }
GET  /api/graph/OP-FALCON-01/HOST-01/          → { nodes: [...], edges: [...] }
GET  /api/timeline/OP-FALCON-01/HOST-01/       → { events: [...] }
GET  /api/findings/OP-FALCON-01/               → { findings: [...] }
POST /api/ai/explain/{finding_id}/             → { explanation, cited_ids, status }
GET  /api/kernel/OP-FALCON-01/HOST-01/         → { eprocess, ssdt_hooks, byovd_matches }
POST /api/blockchain/verify/                   → { on_chain_hash, current_hash, match, tamper_at }
POST /api/blockchain/tamper-demo/              → { tampered: true }
GET  /api/reports/OP-FALCON-01/pdf/            → PDF file download
GET  /api/reports/OP-FALCON-01/json/           → JSON file download
```

---

## Infrastructure

- Docker Compose — run everything with `docker compose up -d`
- Frontend served by nginx at port 443 with self-signed cert

---

## Three Must-Hit Visual Moments (SIH Demo)

1. **Step 4** — Endpoints page: three different SHA-256 hashes appear
2. **Step 15** — Blockchain page: flips from green (Match: YES) to red (TAMPER DETECTED)
3. **Step 16** — Findings page: AI explanation streams in, citation validation appears below
