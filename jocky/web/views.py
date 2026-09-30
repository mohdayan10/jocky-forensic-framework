"""Views for JOCKY Command Console."""

import json
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string

from ..demo import build_demo_evidence, build_demo_timeline, build_demo_graph
from ..common.evidence import InvestigationCase
from ..compiler.pipeline import CompilerPipeline
from ..correlation.engine import CorrelationEngine
from ..blockchain.ledger import IntegrityLedger
from ..console.dispatch import CommandConsole


def _get_demo_case(case_id="OP-FALCON-01"):
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
    return case


def console_home(request):
    html = render_to_string("console.html")
    return HttpResponse(html)


def api_health(request):
    return JsonResponse({
        "status": "healthy",
        "service": "JOCKY Command Console",
        "version": "0.1.0",
        "endpoints_connected": 3,
    })


def api_case(request, case_id):
    case = _get_demo_case(case_id)
    return JsonResponse(case.to_dict())


def api_compile(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    body = json.loads(request.body)
    source = body.get("source", "")
    case_id = body.get("case_id", "")
    filename = body.get("filename", "input.jky")

    pipeline = CompilerPipeline()
    result = pipeline.compile(source, filename)

    if result.success:
        return JsonResponse({
            "success": True,
            "jir": result.jir_text,
            "token_count": result.jir.token_count if result.jir else 0,
            "statement_count": result.jir.statement_count if result.jir else 0,
        })
    else:
        return JsonResponse({
            "success": False,
            "error": result.errors,
        })


def api_dispatch(request):
    if request.method == "POST":
        body = json.loads(request.body)
        targets = body.get("targets", ["HOST-01", "HOST-02", "HOST-03"])
        case_id = body.get("case_id", "OP-FALCON-01")
    else:
        targets = request.GET.get("targets", "HOST-01,HOST-02,HOST-03").split(",")
        case_id = request.GET.get("case_id", "OP-FALCON-01")

    console = CommandConsole()
    result = console.dispatch(case_id, targets)

    return JsonResponse({
        "case_id": result.case_id,
        "status": result.status,
        "total_evidence": result.total_evidence,
        "endpoints": [
            {
                "host": ep.host,
                "os": ep.os_type,
                "status": ep.status,
                "evidence_count": ep.evidence_count,
            }
            for ep in result.endpoints
        ],
    })


def api_correlate(request, case_id):
    case = _get_demo_case(case_id)
    return JsonResponse({
        "case_id": case_id,
        "findings": [f.to_dict() for f in case.findings],
    })


def api_integrity(request, evidence_id):
    case = _get_demo_case()
    ledger = IntegrityLedger()
    ledger.anchor_batch(case.evidence, case.case_id)

    ev = case.get_evidence(evidence_id)
    if not ev:
        return JsonResponse({"error": f"Evidence {evidence_id} not found"}, status=404)

    tamper = request.GET.get("tamper", "false") == "true"
    if tamper:
        ev.data["tampered"] = True

    result = ledger.verify(ev)
    return JsonResponse(result.to_dict())


def api_graph(request, case_id):
    case = _get_demo_case(case_id)
    return JsonResponse(case.graph.to_dict())


def api_timeline(request, case_id):
    case = _get_demo_case(case_id)
    return JsonResponse({
        "case_id": case_id,
        "events": [t.to_dict() for t in case.timeline],
    })


def api_query(request):
    query_hash = request.GET.get("hash", "7b4c3f2a")
    hosts = request.GET.get("hosts", "HOST-01,HOST-02,HOST-03").split(",")

    console = CommandConsole()
    matches = console.cross_host_query(query_hash, hosts)

    return JsonResponse({
        "query_hash": query_hash,
        "matches": [{"host": m.host, "path": m.path, "type": m.match_type} for m in matches],
        "lateral_movement": len(matches) > 1,
    })
