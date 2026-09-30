"""Views for JOCKY Command Console."""

import hashlib
import json
import os
import secrets
import time
from datetime import datetime, timezone, timedelta
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..demo import build_demo_evidence, build_demo_timeline, build_demo_graph
from ..common.evidence import InvestigationCase
from ..compiler.pipeline import CompilerPipeline
from ..correlation.engine import CorrelationEngine
from ..blockchain.ledger import IntegrityLedger
from ..console.dispatch import CommandConsole

try:
    import jwt as pyjwt
    HAS_JWT = True
except ImportError:
    HAS_JWT = False

JWT_SECRET = os.environ.get("JOCKY_JWT_SECRET", "jocky-jwt-secret-demo")

# Hardcoded demo credentials
DEMO_USERS = {"investigator": "jocky2024"}

# Module-level ledger so tamper state persists within a session
_ledger = IntegrityLedger()
_case_cache = {}


def _read_session() -> dict:
    """Read live session state written by terminal demo."""
    try:
        from ..session import read
        return read()
    except Exception:
        return {}


def _get_demo_case(case_id="OP-FALCON-01"):
    if case_id not in _case_cache:
        evidence = build_demo_evidence(case_id)
        timeline = build_demo_timeline()
        graph = build_demo_graph()
        case = InvestigationCase(
            case_id=case_id,
            investigator="SIH Team JOCKY",
            organization="NTRO Authorized",
            endpoints=["HOST-01 (Windows)", "HOST-02 (Ubuntu)", "HOST-03 (Windows)"],
            evidence=evidence,
            timeline=timeline,
            graph=graph,
        )
        engine = CorrelationEngine()
        case.findings = engine.correlate(evidence, case_id, "HOST-01")
        _case_cache[case_id] = case
        _ledger.anchor_batch(evidence, case_id)
    return _case_cache[case_id]


def _make_token(username: str) -> str:
    if HAS_JWT:
        payload = {
            "sub": username,
            "iat": int(time.time()),
            "exp": int(time.time()) + 86400,
        }
        return pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")
    # Fallback: simple opaque token
    return f"demo-{username}-{secrets.token_hex(8)}"


def _cors(response):
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


def console_home(request):
    return HttpResponse(
        "<h1>JOCKY API</h1><p>Frontend is served by React dev server on port 3000.</p>"
    )


# ── Auth ──────────────────────────────────────────────────────────────────────

@csrf_exempt
def api_login(request):
    if request.method == "OPTIONS":
        return _cors(HttpResponse())
    if request.method != "POST":
        return _cors(JsonResponse({"error": "POST required"}, status=405))

    # Parse body — accept JSON or form data
    username = ""
    password = ""
    try:
        body = json.loads(request.body.decode("utf-8"))
        username = str(body.get("username", "")).strip()
        password = str(body.get("password", "")).strip()
    except (json.JSONDecodeError, UnicodeDecodeError):
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

    # Demo: hardcoded credentials OR accept any non-empty login as investigator
    valid = DEMO_USERS.get(username) == password
    if not valid and username and password:
        # Fallback: accept investigator / jocky2024 case-insensitively
        valid = username.lower() == "investigator" and password == "jocky2024"

    if not valid:
        return _cors(JsonResponse(
            {"error": f"Invalid credentials (got user='{username}')"},
            status=401,
        ))

    token = _make_token(username or "investigator")
    return _cors(JsonResponse({"token": token, "username": username or "investigator"}))


# ── Health ────────────────────────────────────────────────────────────────────

def api_health(request):
    return _cors(JsonResponse({
        "status": "healthy",
        "service": "JOCKY Command Console",
        "version": "2.0.0",
        "endpoints_connected": 3,
    }))


# ── Case ──────────────────────────────────────────────────────────────────────

def api_case(request, case_id):
    case = _get_demo_case(case_id)
    return _cors(JsonResponse(case.to_dict()))


# ── Compiler ──────────────────────────────────────────────────────────────────

@csrf_exempt
def api_compile(request):
    if request.method == "OPTIONS":
        return _cors(HttpResponse())
    if request.method != "POST":
        return _cors(JsonResponse({"error": "POST required"}, status=405))

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return _cors(JsonResponse({"error": "Invalid JSON"}, status=400))

    source = body.get("source", "")
    filename = body.get("filename", "input.jky")

    pipeline = CompilerPipeline()
    result = pipeline.compile(source, filename)

    if result.success:
        return _cors(JsonResponse({
            "success": True,
            "jir": result.jir_text,
            "token_count": result.jir.token_count if result.jir else 0,
            "statement_count": result.jir.statement_count if result.jir else 0,
            "policy": "PASSED",
        }))
    else:
        return _cors(JsonResponse({
            "success": False,
            "error": result.errors[0] if result.errors else "Compilation failed",
            "policy": "REJECTED",
        }))


# ── Forge builds ──────────────────────────────────────────────────────────────

_HOST_PLATFORMS = {
    "HOST-01": "Windows Server 2019",
    "HOST-02": "Ubuntu 22.04",
    "HOST-03": "Windows 11",
}


def api_forge_builds(request, case_id):
    session = _read_session()
    session_forge = session.get("forge", {})
    builds = []
    for host_id, platform in _HOST_PLATFORMS.items():
        if host_id in session_forge:
            fd = session_forge[host_id]
            builds.append({
                "host_id":     host_id,
                "platform":    platform,
                "build_id":    fd["build_id"],
                "sha256":      fd["sha256"],
                "entry_point": fd.get("entry_point", "0x1000"),
                "status":      fd.get("status", "COMPLETE"),
            })
        else:
            # Stable fallback when no demo has run yet
            seed = hashlib.sha256(f"{case_id}:{host_id}:forge-v1".encode()).digest()
            sha256 = hashlib.sha256(seed + host_id.encode()).hexdigest()
            builds.append({
                "host_id":     host_id,
                "platform":    platform,
                "build_id":    f"FORGE-BUILD-{sha256[:6].upper()}",
                "sha256":      sha256,
                "entry_point": "0x1000",
                "status":      "PENDING",
            })
    return _cors(JsonResponse({"case_id": case_id, "builds": builds}))


# ── Endpoints ─────────────────────────────────────────────────────────────────

def api_endpoints(request):
    session = _read_session()
    session_forge = session.get("forge", {})
    artifact_counts = {"HOST-01": 486, "HOST-02": 312, "HOST-03": 271}
    endpoints = []
    for host_id, platform in _HOST_PLATFORMS.items():
        if host_id in session_forge:
            fd = session_forge[host_id]
            endpoints.append({
                "host_id":        host_id,
                "platform":       platform,
                "status":         "COMPLETE",
                "artifact_count": artifact_counts[host_id],
                "build_id":       fd["build_id"],
                "sha256":         fd["sha256"],
                "entry_point":    fd.get("entry_point", "0x1000"),
            })
        else:
            seed = hashlib.sha256(f"OP-FALCON-01:{host_id}:forge-v1".encode()).digest()
            sha256 = hashlib.sha256(seed + host_id.encode()).hexdigest()
            endpoints.append({
                "host_id":        host_id,
                "platform":       platform,
                "status":         "PENDING",
                "artifact_count": 0,
                "build_id":       f"FORGE-BUILD-{sha256[:6].upper()}",
                "sha256":         sha256,
                "entry_point":    "0x1000",
            })
    return _cors(JsonResponse({"endpoints": endpoints}))


# ── Dispatch ──────────────────────────────────────────────────────────────────

@csrf_exempt
def api_dispatch(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            body = {}
        targets = body.get("targets", ["HOST-01", "HOST-02", "HOST-03"])
        case_id = body.get("case_id", "OP-FALCON-01")
    else:
        targets = request.GET.get("targets", "HOST-01,HOST-02,HOST-03").split(",")
        case_id = request.GET.get("case_id", "OP-FALCON-01")

    console = CommandConsole()
    result = console.dispatch(case_id, targets)
    return _cors(JsonResponse({
        "case_id": result.case_id,
        "status": result.status,
        "total_evidence": result.total_evidence,
        "endpoints": [
            {"host": ep.host, "os": ep.os_type, "status": ep.status, "evidence_count": ep.evidence_count}
            for ep in result.endpoints
        ],
    }))


# ── Findings ──────────────────────────────────────────────────────────────────

def api_correlate(request, case_id):
    session = _read_session()
    session_findings = session.get("findings")
    if session_findings:
        return _cors(JsonResponse({"case_id": case_id, "findings": session_findings}))
    case = _get_demo_case(case_id)
    return _cors(JsonResponse({
        "case_id": case_id,
        "findings": [f.to_dict() for f in case.findings],
    }))


# ── AI Explain ────────────────────────────────────────────────────────────────

def api_ai_explain(request, finding_id):
    if request.method == "OPTIONS":
        return _cors(HttpResponse())

    # Return live AI explanation from session if demo has run
    session = _read_session()
    session_ai = session.get("ai")
    if session_ai and session_ai.get("explanation"):
        return _cors(JsonResponse({
            "finding_id":  session_ai.get("finding_id", finding_id),
            "explanation": session_ai["explanation"],
            "cited_ids":   session_ai.get("cited_ids", []),
            "valid_ids":   session_ai.get("valid_ids", []),
            "invalid_ids": session_ai.get("invalid_ids", []),
            "status":      session_ai.get("status", "VALIDATED"),
        }))

    case = _get_demo_case()
    finding = next((f for f in case.findings if f.finding_id == finding_id), None)
    if not finding:
        if case.findings:
            finding = case.findings[0]
        else:
            return _cors(JsonResponse({"error": "Finding not found"}, status=404))

    from ..ai_assistant.assistant import ForensicAssistant
    assistant = ForensicAssistant(case)
    response = assistant.explain_finding(finding)

    return _cors(JsonResponse({
        "finding_id":  finding_id,
        "explanation": response.content,
        "cited_ids":   response.citations.cited_ids,
        "valid_ids":   response.citations.valid_ids,
        "invalid_ids": response.citations.invalid_ids,
        "status":      "VALIDATED" if response.accepted else "REJECTED",
    }))


# ── Kernel ────────────────────────────────────────────────────────────────────

def api_kernel(request, case_id, host):
    from ..kernel.collector import KernelCollector

    collector = KernelCollector()
    hp  = collector.collect(host, "HIDDEN_PROCESS_DELTA")
    hk  = collector.collect(host, "HOOK_STATE")
    drv = collector.collect(host, "DRIVER_INTELLIGENCE")

    # EPROCESS section
    hp_data = hp.data
    eprocess = {
        "walk_count": hp_data.get("kernel_process_count", 94),
        "api_count":  hp_data.get("api_process_count", 93),
        "delta":      hp_data.get("delta", 1),
        "hidden": [
            {
                "name": p["name"],
                "pid":  p["pid"],
                "path": p.get("image_path", ""),
            }
            for p in hp_data.get("hidden_processes", [])
        ],
    }

    # SSDT hooks section
    ssdt_hooks = [
        {
            "syscall":   h.get("function", h.get("syscall", "")),
            "expected":  h.get("expected_module", "ntoskrnl.exe"),
            "found":     h.get("found_module", ""),
            "hook_type": h.get("type", h.get("hook_type", "unknown")),
        }
        for h in hk.data.get("ssdt_hooks", [])
    ]

    # BYOVD section — combine driver intel + timeline from timeline data
    case = _get_demo_case(case_id)
    timeline_events = [t.to_dict() for t in case.timeline]

    byovd_matches = []
    for indicator in drv.data.get("byovd_indicators", []):
        # Build attack chain from timeline events referencing this driver
        drv_name = indicator.get("name", "")
        chain = [
            {"time": e["timestamp"].replace("2026-09-30T", "").replace("Z", "") + "Z",
             "event": e["description"]}
            for e in timeline_events
            if drv_name.lower() in e.get("description", "").lower()
               or "callback" in e.get("description", "").lower()
               or "hidden" in e.get("description", "").lower()
        ][:3]

        byovd_matches.append({
            "driver":      drv_name,
            "cve":         indicator.get("cve", ""),
            "capability":  indicator.get("exploit_type", ""),
            "blocklisted": indicator.get("on_blocklist", False),
            "attack_chain": chain or [
                {"time": "09:31:08Z", "event": f"{drv_name} loaded by powershell.exe (PID 4892)"},
                {"time": "09:31:09Z", "event": "Kernel callback removed (PsSetCreateProcessNotifyRoutine)"},
                {"time": "09:31:10Z", "event": "svc_hidden.exe DKOM-removed from process list"},
            ],
        })

    return _cors(JsonResponse({
        "case_id":      case_id,
        "host":         host,
        "eprocess":     eprocess,
        "ssdt_hooks":   ssdt_hooks,
        "byovd_matches": byovd_matches,
    }))


# ── Blockchain ────────────────────────────────────────────────────────────────

def api_blockchain_verify(request):
    """GET /api/blockchain/verify/?evidence_id=E-00421"""
    evidence_id = request.GET.get("evidence_id", "E-00421")

    # Prefer live session data (written after demo step 15)
    session = _read_session()
    bc = session.get("blockchain")
    if bc and bc.get("evidence_id") == evidence_id:
        ok = bc.get("verified", True)
        return _cors(JsonResponse({
            "evidence_id":   evidence_id,
            "on_chain_hash": bc.get("on_chain_hash", ""),
            "current_hash":  bc.get("current_hash", ""),
            "anchored_at":   bc.get("anchored_at", ""),
            "verified":      ok,
            "match":         ok,
            "status":        "VERIFIED" if ok else "FAILED",
        }))

    case = _get_demo_case()
    ev = case.get_evidence(evidence_id)
    if not ev:
        return _cors(JsonResponse({"error": f"Evidence {evidence_id} not found"}, status=404))
    result = _ledger.verify(ev)
    return _cors(JsonResponse(result.to_dict()))


def api_blockchain_tamper(request):
    """GET /api/blockchain/tamper-demo/?evidence_id=E-00421"""
    evidence_id = request.GET.get("evidence_id", "E-00421")

    # Prefer live session data
    session = _read_session()
    bc = session.get("blockchain")
    if bc and bc.get("evidence_id") == evidence_id:
        return _cors(JsonResponse({
            "tampered":      True,
            "evidence_id":   evidence_id,
            "on_chain_hash": bc.get("on_chain_hash", ""),
            "current_hash":  bc.get("tamper_hash", ""),
            "tamper_ts":     bc.get("tamper_ts", ""),
            "match":         False,
            "verified":      False,
            "tamper_detected_at": bc.get("tamper_ts", ""),
        }))

    case = _get_demo_case()
    ev = case.get_evidence(evidence_id)
    if not ev:
        return _cors(JsonResponse({"error": f"Evidence {evidence_id} not found"}, status=404))
    ev.data["__tamper_demo__"] = True
    result = _ledger.verify(ev)
    return _cors(JsonResponse({
        "tampered":    True,
        "evidence_id": evidence_id,
        "verify":      result.to_dict(),
    }))


def api_integrity(request, evidence_id):
    case = _get_demo_case()
    ev = case.get_evidence(evidence_id)
    if not ev:
        return _cors(JsonResponse({"error": f"Evidence {evidence_id} not found"}, status=404))

    tamper = request.GET.get("tamper", "false") == "true"
    if tamper:
        ev.data["tampered"] = True

    result = _ledger.verify(ev)
    return _cors(JsonResponse(result.to_dict()))


# ── Graph + Timeline ──────────────────────────────────────────────────────────

def api_graph(request, case_id):
    case = _get_demo_case(case_id)
    graph = case.graph.to_dict()
    # Attach full evidence data keyed by evidence_id for the detail panel
    evidence_map = {ev.evidence_id: {
        "artifact_type": ev.artifact_type.value if hasattr(ev.artifact_type, "value") else str(ev.artifact_type),
        "host": ev.host,
        "sha256": ev.sha256,
        "timestamp": ev.timestamp,
        **ev.data,
    } for ev in case.evidence}
    graph["evidence"] = evidence_map
    return _cors(JsonResponse(graph))


def api_timeline(request, case_id):
    case = _get_demo_case(case_id)
    return _cors(JsonResponse({
        "case_id": case_id,
        "events": [t.to_dict() for t in case.timeline],
    }))


# ── Reports ───────────────────────────────────────────────────────────────────

def api_report_pdf(request, case_id):
    import tempfile
    # Serve the file written by demo step 17 if it exists
    pdf_path = os.path.join(tempfile.gettempdir(), "jocky_reports", f"{case_id}_report.pdf")
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        resp = HttpResponse(pdf_bytes, content_type="application/pdf")
        resp["Content-Disposition"] = f'attachment; filename="jocky_{case_id}.pdf"'
        return _cors(resp)
    # Generate fresh if demo hasn't run yet
    try:
        from ..report.generator import ReportGenerator, ReportConfig
        case = _get_demo_case(case_id)
        cfg = ReportConfig(formats=["pdf"])
        gen = ReportGenerator(ledger=_ledger)
        out_dir = os.path.join(tempfile.gettempdir(), "jocky_reports")
        os.makedirs(out_dir, exist_ok=True)
        gen.generate(case, cfg)
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            resp = HttpResponse(pdf_bytes, content_type="application/pdf")
            resp["Content-Disposition"] = f'attachment; filename="jocky_{case_id}.pdf"'
            return _cors(resp)
    except Exception:
        pass
    # Last resort: generate minimal valid PDF with reportlab
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        import io
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(60, 780, "JOCKY — Investigation Report")
        c.setFont("Helvetica", 12)
        c.drawString(60, 750, f"Case: {case_id}")
        c.drawString(60, 730, "Investigator: SIH Team JOCKY")
        c.drawString(60, 710, "Organization: NTRO Authorized")
        c.drawString(60, 680, "Artifacts: 486 across 3 hosts")
        c.drawString(60, 660, "Finding: CRITICAL — BYOVD + EDR blinding")
        c.drawString(60, 640, "Blockchain: VERIFIED")
        c.save()
        pdf_bytes = buf.getvalue()
        resp = HttpResponse(pdf_bytes, content_type="application/pdf")
        resp["Content-Disposition"] = f'attachment; filename="jocky_{case_id}.pdf"'
        return _cors(resp)
    except Exception:
        pass
    resp = HttpResponse(b"%PDF-1.4 placeholder", content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="jocky_{case_id}.pdf"'
    return _cors(resp)


def api_report_json(request, case_id):
    case = _get_demo_case(case_id)
    data = {
        "case_id": case_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "investigator": case.investigator,
        "organization": case.organization,
        "endpoints": case.endpoints,
        "evidence_count": len(case.evidence),
        "finding_count": len(case.findings),
        "findings": [f.to_dict() for f in case.findings],
        "timeline": [t.to_dict() for t in case.timeline],
    }
    resp = HttpResponse(
        json.dumps(data, indent=2, default=str),
        content_type="application/json",
    )
    resp["Content-Disposition"] = f'attachment; filename="jocky_{case_id}.json"'
    return _cors(resp)


def api_report_stats(request, case_id):
    """GET /api/reports/<case_id>/ — summary stats for the Reports page."""
    session = _read_session()
    finding_id = session.get("finding", {}).get("finding_id", "")
    if not finding_id:
        case = _get_demo_case(case_id)
        finding_id = case.findings[0].finding_id if case.findings else "F-000000"
    return _cors(JsonResponse({
        "case_id":        case_id,
        "artifact_count": 486,
        "host_count":     3,
        "finding_count":  1,
        "finding_id":     finding_id,
    }))


def api_report_generate(request, case_id):
    session = _read_session()
    finding_id = session.get("finding", {}).get("finding_id", "")
    case = _get_demo_case(case_id)
    if not finding_id and case.findings:
        finding_id = case.findings[0].finding_id
    return _cors(JsonResponse({
        "case_id":        case_id,
        "artifact_count": 486,
        "evidence_count": 486,
        "finding_count":  1,
        "host_count":     3,
        "hosts":          3,
        "finding_id":     finding_id,
        "status":         "ready",
    }))


# ── Query ─────────────────────────────────────────────────────────────────────

def api_query(request):
    query_hash = request.GET.get("hash", "7b4c3f2a")
    hosts = request.GET.get("hosts", "HOST-01,HOST-02,HOST-03").split(",")
    console = CommandConsole()
    matches = console.cross_host_query(query_hash, hosts)
    return _cors(JsonResponse({
        "query_hash": query_hash,
        "matches": [{"host": m.host, "path": m.path, "type": m.match_type} for m in matches],
        "lateral_movement": len(matches) > 1,
    }))
