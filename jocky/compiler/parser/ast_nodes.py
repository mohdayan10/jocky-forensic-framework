"""AST node definitions for the JOCKY language."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ASTNode:
    """Base class for all AST nodes."""
    line: int = 0
    column: int = 0


# ── Investigation root ──

@dataclass
class Program(ASTNode):
    """Root node: a complete JOCKY investigation program."""
    case: CaseDecl | None = None
    target: TargetDecl | None = None
    statements: List[ASTNode] = field(default_factory=list)


@dataclass
class CaseDecl(ASTNode):
    """case \"OP-FALCON-01\""""
    case_id: str = ""


@dataclass
class TargetDecl(ASTNode):
    """target hostgroup ENTERPRISE_EAST"""
    target_type: str = ""   # "hostgroup", "host", etc.
    target_name: str = ""


# ── Collection ──

@dataclass
class CollectStmt(ASTNode):
    """collect <artifact_type> [WHERE <filters>]"""
    artifact_type: str = ""
    filters: List[FilterExpr] = field(default_factory=list)


@dataclass
class FilterExpr(ASTNode):
    """A single filter condition: field OP value"""
    field: str = ""
    operator: str = ""   # "IN", "==", "modified_within", etc.
    value: object = None  # string, list, duration


# ── Correlation ──

@dataclass
class CorrelateStmt(ASTNode):
    """correlate <source> WITH <target> [WITHIN <duration>]"""
    source: str = ""
    target: str = ""
    within: str | None = None  # e.g., "45s"


# ── Detection ──

@dataclass
class DetectStmt(ASTNode):
    """detect <rule_name>"""
    rule_name: str = ""


# ── Output ──

@dataclass
class TimelineStmt(ASTNode):
    """timeline"""
    pass


@dataclass
class EvidenceGraphStmt(ASTNode):
    """evidence_graph"""
    pass


@dataclass
class GenerateReportStmt(ASTNode):
    """generate report FORMAT [json, pdf]"""
    formats: List[str] = field(default_factory=list)
