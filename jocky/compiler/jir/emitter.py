"""JOCKY JIR Emitter — Converts AST to OS-agnostic intermediate representation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

from ..parser.ast_nodes import (
    Program, CollectStmt, CorrelateStmt, DetectStmt,
    TimelineStmt, EvidenceGraphStmt, GenerateReportStmt,
)


# ── JIR data structures ──

@dataclass
class JIRCorrelateOp:
    source: str
    target: str
    window: Optional[str] = None  # e.g. "45s"


@dataclass
class JIRDetectOp:
    rule: str
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JIRCollectOp:
    artifact_type: str
    flags: List[str] = field(default_factory=list)
    scope: Dict[str, Any] = field(default_factory=dict)
    filters: Dict[str, Any] = field(default_factory=dict)

    @property
    def requires_filter(self) -> bool:
        return self.artifact_type in {"FILE_METADATA"}

    @property
    def has_filter(self) -> bool:
        return bool(self.scope) or bool(self.filters)


@dataclass
class JIRProgram:
    """The complete JIR output for a JOCKY investigation."""
    case_id: str = ""
    target_type: str = ""
    target_name: str = ""
    collect_ops: List[JIRCollectOp] = field(default_factory=list)
    correlate_ops: List[JIRCorrelateOp] = field(default_factory=list)
    detect_ops: List[JIRDetectOp] = field(default_factory=list)
    emit_timeline: bool = False
    emit_evidence_graph: bool = False
    report_formats: List[str] = field(default_factory=list)
    token_count: int = 0
    statement_count: int = 0
    cert_id: str = ""
    kernel_authorized: bool = False
    case_expiry: str = ""

    @property
    def target_hostgroup(self) -> str:
        return self.target_name

    @property
    def has_kernel_ops(self) -> bool:
        kernel_types = {"KERNEL_CALLBACKS", "HOOK_STATE", "HIDDEN_PROCESSES"}
        return any(op.artifact_type in kernel_types for op in self.collect_ops)

    @property
    def ops(self) -> list:
        return self.collect_ops + self.correlate_ops + self.detect_ops


# ── Artifact type → JIR flags mapping ──

ARTIFACT_FLAGS = {
    "processes": {
        "flags": ["FULL_TREE", "MEMORY_FLAGS", "LOADED_MODULES"],
    },
    "network": {
        "flags": ["ACTIVE", "DNS", "ARP", "ROUTING"],
    },
    "persistence": {
        "flags": ["REGISTRY_RUN_KEYS", "SCHEDULED_TASKS", "SERVICES", "STARTUP_FOLDERS"],
    },
    "drivers": {
        "flags": ["LOADED_MODULES", "SIGNATURE_CHECK", "CVE_MATCH"],
    },
    "file_metadata": {
        "flags": ["HASH_SHA256", "SIGNATURE", "TIMESTAMPS", "PE_HEADER"],
    },
    "kernel_callbacks": {
        "flags": ["PROCESS", "IMAGE", "REGISTRY", "THREAD"],
    },
    "hook_state": {
        "flags": ["SSDT", "INLINE", "IRP"],
    },
    "hidden_processes": {
        "flags": ["EPROCESS_WALK_VS_API_DELTA"],
    },
    "users": {
        "flags": ["LOCAL_SESSIONS", "DOMAIN_SESSIONS", "LOGON_HISTORY"],
    },
}


class JIREmitter:
    """Emits JIR from a validated AST."""

    def emit(self, program: Program) -> JIRProgram:
        """Convert AST to JIR."""
        jir = JIRProgram()

        # Case and target
        if program.case:
            jir.case_id = program.case.case_id
        if program.target:
            jir.target_type = program.target.target_type.upper()
            jir.target_name = program.target.target_name

        # Statements
        for stmt in program.statements:
            if isinstance(stmt, CollectStmt):
                jir.collect_ops.append(self._emit_collect(stmt))
            elif isinstance(stmt, CorrelateStmt):
                jir.correlate_ops.append(self._emit_correlate(stmt))
            elif isinstance(stmt, DetectStmt):
                jir.detect_ops.append(self._emit_detect(stmt))
            elif isinstance(stmt, TimelineStmt):
                jir.emit_timeline = True
            elif isinstance(stmt, EvidenceGraphStmt):
                jir.emit_evidence_graph = True
            elif isinstance(stmt, GenerateReportStmt):
                jir.report_formats = stmt.formats

        # Populate metadata for downstream pipeline stages
        jir.statement_count = len(program.statements)

        return jir

    def emit_with_metadata(self, program: Program, token_count: int = 0,
                           cert_id: str = "", kernel_authorized: bool = False,
                           case_expiry: str = "") -> JIRProgram:
        """Emit JIR and attach pipeline metadata."""
        jir = self.emit(program)
        jir.token_count = token_count
        jir.cert_id = cert_id
        jir.kernel_authorized = kernel_authorized
        jir.case_expiry = case_expiry
        return jir

    def emit_verbose(self, program: Program) -> JIRProgram:
        """Emit with [JIR] status output for demo."""
        print("[JIR]      Emitting intermediate representation...", end="")
        jir = self.emit(program)
        ops = len(jir.collect_ops) + len(jir.correlate_ops) + len(jir.detect_ops)
        print(f"  OK  ({ops} operations)")
        return jir

    def _emit_collect(self, stmt: CollectStmt) -> JIRCollectOp:
        """Emit a COLLECT operation with expanded flags."""
        meta = ARTIFACT_FLAGS.get(stmt.artifact_type, {"flags": []})

        op = JIRCollectOp(
            artifact_type=stmt.artifact_type.upper(),
            flags=meta["flags"],
        )

        # Apply filters
        for f in stmt.filters:
            if f.operator == "IN":
                op.scope[f.field] = f.value
            elif f.operator == "modified_within":
                op.filters["modified_within"] = f.value
            elif f.operator == "==":
                op.filters[f.field] = f.value

        return op

    def _emit_correlate(self, stmt: CorrelateStmt) -> JIRCorrelateOp:
        return JIRCorrelateOp(
            source=stmt.source.upper(),
            target=stmt.target.upper(),
            window=stmt.within,
        )

    def _emit_detect(self, stmt: DetectStmt) -> JIRDetectOp:
        return JIRDetectOp(rule=stmt.rule_name.upper())

    # ── Output formatting ──

    def format_text(self, jir: JIRProgram) -> str:
        """Format JIR as human-readable text (for --emit-jir demo output)."""
        lines = []
        lines.append(f"CASE {jir.case_id}")
        lines.append(f"TARGET {jir.target_type} {jir.target_name}")
        lines.append("")

        # COLLECT block
        lines.append("COLLECT [")
        for op in jir.collect_ops:
            flags_str = " | ".join(op.flags)
            parts = [f"flags: {flags_str}"]
            if op.scope:
                parts.append(f"scope: {json.dumps(op.scope)}")
            if op.filters:
                for k, v in op.filters.items():
                    parts.append(f"filter: {k}:{v}")
            indent = " " * 4
            lines.append(f"{indent}{op.artifact_type:<20} {{ {', '.join(parts)} }}")
        lines.append("]")
        lines.append("")

        # CORRELATE block
        if jir.correlate_ops:
            lines.append("CORRELATE [")
            for op in jir.correlate_ops:
                window = f" WITHIN {op.window}" if op.window else ""
                lines.append(f"    {op.source} WITH {op.target}{window}")
            lines.append("]")
            lines.append("")

        # DETECT block
        if jir.detect_ops:
            lines.append("DETECT [")
            for op in jir.detect_ops:
                lines.append(f"    {op.rule}")
            lines.append("]")
            lines.append("")

        # Output directives
        if jir.emit_timeline:
            lines.append("EMIT TIMELINE")
        if jir.emit_evidence_graph:
            lines.append("EMIT EVIDENCE_GRAPH")
        if jir.report_formats:
            lines.append(f"GENERATE REPORT [{', '.join(f.upper() for f in jir.report_formats)}]")

        return "\n".join(lines)

    def to_json(self, jir: JIRProgram) -> str:
        """Serialize JIR to JSON."""
        return json.dumps(asdict(jir), indent=2)
