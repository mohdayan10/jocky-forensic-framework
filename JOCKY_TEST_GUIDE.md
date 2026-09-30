# JOCKY — Complete Test Guide
### Run this before every demo / presentation

---

## 0. Setup Check — Run First

```bash
# From your repo root (wherever setup.py lives)
cd /path/to/jocky

# Verify Python version
python3 --version          # must be 3.10+

# Install dependencies
pip install -e .           # installs jocky package + all deps from setup.py

# Confirm anthropic key is set — AI step won't work without it
echo $ANTHROPIC_API_KEY    # must print a key, not blank

# If blank:
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## 1. Unit Tests — Run These First, Always

```bash
python3 -m pytest tests/test_modules.py -v
```

**Every test must pass before you touch the demo.**
If anything fails here, the demo will fail at the same point.

Expected output — what each test proves:

| Test class | What it's checking | If it fails |
|---|---|---|
| `TestEvidence` | `E-00001` sequential IDs, SHA-256 auto-hash | `evidence.py` counter broken |
| `TestCorrelation` | 3+ signals → finding raised, 1 signal → no finding | `engine.py` signal threshold wrong |
| `TestBlockchain` | anchor + verify match; tampered byte → mismatch | `ledger.py` hash comparison broken |
| `TestAIAssistant` | valid `E-XXXXX` accepted; `E-99999` rejected | citation regex broken |
| `TestReport` | JSON contains case_id, evidence_count, findings | `generator.py` field missing |
| `TestKernel` | hidden process count = EPROCESS - API; CVE match on VulnDrv.sys | `collector.py` delta wrong |
| `TestForge` | 3 builds → 3 different SHA-256 hashes | seed/urandom not varying |
| `TestSpectre` | all 3 strategies return evidence; unknown raises error | `agent.py` strategy switch |
| `TestBeacon` | channel established; JOCKY domains = 0 in footprint | `beacon.py` footprint field |
| `TestConsole` | dispatch to 3 hosts; cross-host hash query returns 3 matches | `dispatch.py` loop |

**Run a single failing test in isolation:**
```bash
python3 -m pytest tests/test_modules.py::TestBlockchain -v
python3 -m pytest tests/test_modules.py::TestAIAssistant -v   # requires ANTHROPIC_API_KEY
```

---

## 2. Compiler Pipeline — Isolated Test

Tests the core language: Lexer → Parser → Semantic → JIR → Policy.

```bash
# Create a minimal test program
cat > /tmp/test_minimal.jky << 'EOF'
case "TEST-01"
target hostgroup ENTERPRISE_EAST

collect processes
collect file_metadata WHERE path IN ["Temp"] AND modified_within "72h"

correlate processes WITH files

detect unsigned_executable_in_temp

timeline
generate report FORMAT [json, pdf]
EOF

# Compile it
python3 -m jocky compile /tmp/test_minimal.jky --verbose --emit-jir
```

**What you expect to see:**
```
[LEXER]    Tokenizing...    OK  (N tokens)
[PARSER]   Building AST...  OK  (N statements)
[SEMANTIC] Type check...    OK
[JIR]      Emitting...      OK  (N operations)
[POLICY]   Validation...    OK
```
Followed by the JIR block. If `--emit-jir` is silent or crashes, check `pipeline.py`'s `emit_jir` flag handling.

**Test policy rejection — file_metadata with no filter:**
```bash
cat > /tmp/test_bad.jky << 'EOF'
case "TEST-02"
target hostgroup ENTERPRISE_EAST

collect file_metadata

generate report FORMAT [json, pdf]
EOF

python3 -m jocky compile /tmp/test_bad.jky --verbose
```
**Must print a `PolicyViolation` error, not compile successfully.**
If it compiles clean, `policy/validator.py` check 3 is broken.

**Test kernel op rejection without authorization:**
```bash
cat > /tmp/test_kernel.jky << 'EOF'
case "TEST-03"
target hostgroup ENTERPRISE_EAST

collect hidden_processes
collect kernel_callbacks

generate report FORMAT [json, pdf]
EOF

python3 -m jocky compile /tmp/test_kernel.jky --verbose
```
Whether this passes or fails depends on your `demo_cert()` — if it sets `kernel_authorized=True` by default, it will pass. If your demo cert is restricted, it rejects. Know which behavior your cert produces before the presentation.

---

## 3. Forge Builds — Isolated Test

```bash
python3 -m jocky build /tmp/test_minimal.jky
```

Or directly:
```bash
python3 - << 'EOF'
import secrets, hashlib, os
from jocky.forge.builder import ForgeBuilder

# Simulate what Forge does for 3 hosts
builder = ForgeBuilder()
builds = []
for host in ["HOST-01", "HOST-02", "HOST-03"]:
    result = builder.build(jir=None, case_id="TEST-01", host_id=host)
    builds.append(result)
    print(f"{host}  SHA-256: {result['sha256'][:16]}...  BuildID: {result['build_id']}")

# Verify no hash collisions
hashes = [b['sha256'] for b in builds]
assert len(set(hashes)) == 3, f"COLLISION DETECTED: {hashes}"
print("\nAll 3 builds unique — OK")
EOF
```

**If `builder.build(jir=None, ...)` crashes:** your `builder.py` requires a real JIR object. Replace `jir=None` with a compiled JIR from the pipeline. The test above assumes Forge can run standalone — check your actual implementation.

---

## 4. Blockchain — Isolated Test

```bash
python3 - << 'EOF'
from jocky.blockchain.ledger import BlockchainLedger
from jocky.common.evidence import Evidence

ledger = BlockchainLedger()
case_id = "TEST-BC-01"

# Create evidence and anchor it
ev = Evidence(
    artifact_type="PROCESS",
    host_id="HOST-01",
    case_id=case_id,
    payload={"pid": 1234, "name": "test.exe"}
)
print(f"Evidence ID: {ev.evidence_id}")
print(f"SHA-256:     {ev.sha256[:32]}...")

anchor_result = ledger.anchor(ev, case_id)
print(f"Anchored:    block {anchor_result.block_number}, tx {anchor_result.transaction_id}")

# Verify unmodified — must match
verify_result = ledger.verify(ev, case_id)
print(f"\nUnmodified verify: match={verify_result.match}")
assert verify_result.match, "FAIL: clean evidence failed verification"

# Tamper and verify — must NOT match
original_payload = ev.payload.copy()
ev.payload["pid"] = 9999          # tamper
ev.sha256 = "tampered_hash_value" # simulate recomputed hash after tamper
verify_tampered = ledger.verify(ev, case_id)
print(f"Tampered verify:   match={verify_tampered.match}  tamper_detected={not verify_tampered.match}")
assert not verify_tampered.match, "FAIL: tampered evidence passed verification"

print("\nBlockchain tests passed")
EOF
```

**Watch for:** if `Evidence.__init__` auto-computes SHA-256 from payload, then mutating `ev.payload` without recomputing `ev.sha256` may not trigger a tamper. Check how your `ledger.verify()` computes the current hash — does it recompute from `ev.payload`, or does it use `ev.sha256`? The tamper demo in step 15 needs to produce a genuine hash mismatch, not just a field change.

---

## 5. AI Assistant — Isolated Test

**Requires `ANTHROPIC_API_KEY` set.**

```bash
python3 - << 'EOF'
from jocky.ai_assistant.assistant import AIAssistant
from jocky.common.evidence import Finding, Evidence, Severity, Confidence, InvestigationCase

# Build a minimal case with known evidence IDs
case = InvestigationCase(case_id="TEST-AI-01")

ev1 = Evidence(artifact_type="PROCESS", host_id="HOST-01", case_id="TEST-AI-01",
               payload={"pid": 4892, "name": "powershell.exe", "descriptor": "PowerShell spawned by cmd.exe"})
ev2 = Evidence(artifact_type="NETWORK", host_id="HOST-01", case_id="TEST-AI-01",
               payload={"remote_addr": "185.220.101.42", "port": 443, "descriptor": "Outbound TLS connection"})

case.evidence.extend([ev1, ev2])

finding = Finding(
    case_id="TEST-AI-01",
    host_id="HOST-01",
    severity=Severity.HIGH,
    confidence=Confidence.MEDIUM,
    rules_fired=["RAPID_OUTBOUND"],
    evidence_ids=[ev1.evidence_id, ev2.evidence_id]
)
case.findings.append(finding)

assistant = AIAssistant()

# Test 1: valid explanation
print("=== Valid citation test ===")
try:
    explanation = assistant.explain_finding(finding, case)
    print(f"Response received ({len(explanation)} chars)")
    print(f"Finding ID in response: {finding.finding_id}")
    # Check no E-XXXXX IDs outside the valid set appear
    import re
    cited = set(re.findall(r'E-\d{5}', explanation))
    valid = {ev1.evidence_id, ev2.evidence_id}
    invalid = cited - valid
    if invalid:
        print(f"FAIL: invalid citations: {invalid}")
    else:
        print(f"All citations valid: {cited}")
except Exception as e:
    print(f"FAIL: {e}")

# Test 2: citation rejection — inject a bad ID
print("\n=== Invalid citation rejection test ===")
bad_text = f"The process {ev1.evidence_id} connected to the network E-99999 maliciously."
try:
    assistant.validate_external_response(bad_text, case, finding)
    print("FAIL: should have rejected E-99999")
except Exception as e:
    print(f"Correctly rejected: {e}")
EOF
```

---

## 6. Full Demo — The Real Thing

```bash
python3 -m jocky.demo
# or, depending on your entry point:
python3 demo.py
```

**Walk through each step and verify:**

### Steps 1–2 (Language + Compiler)
- Line numbers on the source display are correct (1–26)
- Token count is ~89, statement count ~19 — if wildly different, lexer or parser changed
- All 5 policy checks print `OK` with the demo cert data
- JIR block shows all 8 collect ops with their flags

### Step 3 (LLVM hashes)
- Two hashes are printed — they **must differ**
- Run the demo twice — both runs should produce different pairs of hashes
- If the same two hashes appear on every run, `os.urandom()` is not being called or the seed is hardcoded

### Step 4 (Forge)
- Three build IDs: `FORGE-BUILD-{6 hex}` — all different
- Three SHA-256 hashes — all different
- Three entry points (hex) — should differ
- Three import hashes — should differ
- `[FORGE] All 3 builds unique` must print
- Run twice — all 9 values change between runs

### Step 5–7 (Spectre — simulated)
- Label reads `[SIMULATED AGENT]` not `[LIVE PIPELINE]`
- PID for svchost.exe changes between runs if your fixture randomizes it
- Evidence counts (187, 34, 12, 89) are static fixture values — that's correct

### Step 8–10 (Kernel — simulated)
- `[SIMULATED AGENT]` label present
- Hidden process count: EPROCESS=94, API=93, delta=1 — static fixture, correct
- CVE-2021-21551 match on VulnDrv.sys — static fixture, correct

### Step 11 (Beacon — simulated)
- `[SIMULATED AGENT]` label present
- Channel ID (`83a22bc7dbad` or similar) — check if this changes per run or is static
  - If static: acceptable, but note it for evaluators
  - If random: better

### Step 12 (Multi-endpoint dispatch)
- `[LIVE PIPELINE]` label on the dispatch lines
- `[SIMULATED AGENT]` label on the collection results (187/143/156 artifact counts)
- Cross-host query returns MATCH on all 3 hosts — static fixture result

### Step 13 (Evidence Graph + Timeline)
- `[LIVE PIPELINE]` label — graph is built by pipeline consuming fixture data
- Evidence IDs (`E-00421`, `E-00422`, etc.) — these must match the IDs used in step 14
- Timeline events have correct timestamps and link to correct evidence IDs

### Step 14 (Correlation Engine)
- `[LIVE PIPELINE]` label
- Finding ID format: `F-{6 hex chars}` — **changes every run**
- Finding ID must match what step 16 references — confirm the ID flows through
- 6 signals, all 6 rules fire, severity=CRITICAL, confidence=HIGH
- Evidence list: 8 IDs, all in the `E-00xxx` range from step 13

### Step 15 (Blockchain)
- `[LIVE PIPELINE]` label
- Unmodified: both hashes identical, `Match: YES`
- Tampered: hashes differ, `Match: NO`, tamper timestamp is today's date/time
- Tamper timestamp **must change between runs** — confirms `datetime.utcnow()` is live

### Step 16 (AI Assistant)
- `[LIVE PIPELINE]` label
- Finding ID in the query matches step 14's output
- AI response text **changes between runs** — confirms real API call
- All cited `E-XXXXX` IDs appear in the VALID list
- `E-00999` or similar rejected — `Response rejected` message appears
- **If the AI step hangs:** your `ANTHROPIC_API_KEY` is missing or expired
- **If the AI step crashes with 429:** rate limit — wait 60 seconds and retry

### Step 17 (Report)
- `[REPORT]` lines print without error
- JSON path and PDF path are printed
- Check the files actually exist:
  ```bash
  ls -la /tmp/jocky_reports/
  cat /tmp/jocky_reports/OP-FALCON-01_report.json | python3 -m json.tool | head -40
  ```
- JSON must have: `case_id`, `evidence_count: 486`, `findings` array, `blockchain_verified`
- PDF file must be non-zero bytes and openable

---

## 7. Web Console — API Endpoints

```bash
# Start the Django dev server
python3 manage.py runserver 8000

# In a second terminal, test each endpoint:

# Health check
curl http://localhost:8000/api/health/
# Expected: {"status": "ok"} or similar

# Case details
curl http://localhost:8000/api/auth/cases/OP-FALCON-01/
# Expected: JSON with case metadata

# Compile endpoint
curl -X POST http://localhost:8000/api/compiler/compile/ \
  -H "Content-Type: application/json" \
  -d '{"source": "case \"TEST-01\"\ntarget hostgroup ENTERPRISE_EAST\ncollect processes\ntimeline\ngenerate report FORMAT [json, pdf]", "case_id": "TEST-01"}'
# Expected: {"success": true, "jir": {...}, "token_count": N, "statement_count": N}

# Evidence graph
curl http://localhost:8000/api/graph/OP-FALCON-01/HOST-01/
# Expected: {"nodes": [...], "edges": [...]}

# Timeline
curl http://localhost:8000/api/timeline/OP-FALCON-01/HOST-01/
# Expected: array of timeline events with timestamps

# Findings
curl http://localhost:8000/api/findings/OP-FALCON-01/
# Expected: array of findings with severity, evidence_ids, rules_fired

# Blockchain verify (clean)
curl "http://localhost:8000/api/blockchain/verify/E-00421/"
# Expected: {"match": true}

# Blockchain verify (tampered)
curl "http://localhost:8000/api/blockchain/verify/E-00421/?tamper=true"
# Expected: {"match": false, "tamper_detected_at": "..."}

# Cross-host query
curl "http://localhost:8000/api/query/?hash=7b4c3f2a"
# Expected: matches on HOST-01, HOST-02, HOST-03
```

---

## 8. Known Failure Points and Fixes

### Demo crashes at Step 16 (AI)
```
anthropic.AuthenticationError
```
**Fix:** `export ANTHROPIC_API_KEY="sk-ant-..."` then rerun.

### Demo crashes at Step 16 with citation rejection on valid IDs
The AI response cited an evidence ID that doesn't exist in `case.evidence`.
**Fix:** Check that `build_demo_evidence()` in `demo.py` creates Evidence objects for every
ID that the correlation engine will reference. The IDs used in `build_demo_graph()`,
`build_demo_timeline()`, and the fixture finding must all be in the same pool.

### Step 4 Forge: all 3 hashes identical
`os.urandom(128)` call is outside the per-host loop, so all 3 builds use the same random bytes.
**Fix:** Move the `os.urandom()` call inside the loop.

### Step 15 Blockchain: tamper timestamp doesn't change between runs
The tamper timestamp is hardcoded as a string rather than `datetime.utcnow().isoformat()`.
**Fix:** Check `ledger.py` — the tamper timestamp should be generated at verification time.

### Step 3: same two hashes on every run
The seed passed to `hashlib.sha256()` is a constant string, not `os.urandom()`.
**Fix:** Confirm `demo.py` step 3 calls `os.urandom(8)` for each seed, not a fixed string.

### PDF report is 0 bytes or won't open
`pdf_writer.py` is stdlib-only — it generates valid PDF 1.4 but some viewers are strict.
**Test:** `python3 -c "open('/tmp/jocky_reports/OP-FALCON-01_report.pdf','rb').read(8)"` — must start with `%PDF-1.4`.
If the file is empty, check `generator.py`'s PDF path and that `/tmp/jocky_reports/` exists:
```bash
mkdir -p /tmp/jocky_reports
```

### Web console: `ModuleNotFoundError` on `manage.py runserver`
Django can't find the `jocky` package.
**Fix:** `pip install -e .` from the repo root, then retry.

### Compiler rejects valid `collect processes` (no filter)
`semantic/analyzer.py` is enforcing filter requirement on all collect types, not just `file_metadata`.
**Fix:** The filter requirement in `analyzer.py` should only fire when `collect_type == "file_metadata"`.
Same check applies in `policy/validator.py` via `JIRCollectOp.requires_filter`.

---

## 9. Pre-Presentation Checklist

Run through this the night before and the morning of.

```
[ ] python3 --version                      → 3.10+
[ ] pip install -e . completes clean
[ ] echo $ANTHROPIC_API_KEY                → non-blank
[ ] python3 -m pytest tests/ -v            → all green
[ ] python3 -m jocky compile op_falcon.jky → compiles, JIR prints
[ ] python3 -m jocky compile bad.jky       → rejects unfiltered file_metadata
[ ] python3 -m jocky.demo (full run)       → all 17 steps complete
[ ] Step 3 hashes differ from previous run → confirmed random
[ ] Step 4 build IDs differ from previous run → confirmed random
[ ] Step 14 finding ID differs from previous run → confirmed random
[ ] Step 15 tamper timestamp is today's date/time → confirmed live
[ ] Step 16 AI text differs from previous run → confirmed real API call
[ ] Step 16 citation rejection fires on invalid ID → confirmed
[ ] /tmp/jocky_reports/ has .json and .pdf → confirmed
[ ] PDF opens and is readable → confirmed
[ ] python3 manage.py runserver 8000 → no import errors
[ ] curl /api/health/ → 200 response
[ ] curl /api/compiler/compile/ → returns JIR
```

If every box is checked, the demo is solid.
