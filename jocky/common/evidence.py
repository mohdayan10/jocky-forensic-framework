"""JOCKY Evidence Model — Core data structures for forensic artifacts and findings."""

from __future__ import annotations

import hashlib
import json
import secrets
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum, auto
from typing import List, Dict, Any, Optional


class _EvidenceCounter:
    """Thread-safe sequential counter for evidence IDs."""
    def __init__(self, start: int = 1):
        self._value = start
        self._lock = threading.Lock()

    def next(self) -> str:
        with self._lock:
            eid = f"E-{self._value:05d}"
            self._value += 1
            return eid


_evidence_counter = _EvidenceCounter()


class Severity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Confidence(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ArtifactType(Enum):
    PROCESS = "PROCESS"
    FILE = "FILE"
    NETWORK = "NETWORK"
    REGISTRY = "REGISTRY"
    DRIVER = "DRIVER"
    KERNEL_CALLBACK = "KERNEL_CALLBACK"
    HOOK_STATE = "HOOK_STATE"
    HIDDEN_PROCESS = "HIDDEN_PROCESS"
    PERSISTENCE = "PERSISTENCE"
    USER_SESSION = "USER_SESSION"


@dataclass
class Evidence:
    """A single forensic evidence artifact collected during an investigation."""
    evidence_id: str = ""
    artifact_type: ArtifactType = ArtifactType.PROCESS
    host: str = ""
    timestamp: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    sha256: str = ""
    blockchain_verified: bool = False

    def __post_init__(self):
        if not self.evidence_id:
            self.evidence_id = _evidence_counter.next()
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if not self.sha256:
            self.sha256 = self.compute_hash()

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of the evidence data."""
        content = json.dumps(self.data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["artifact_type"] = self.artifact_type.value
        return d


@dataclass
class Finding:
    """A forensic finding — generated from correlated evidence signals."""
    finding_id: str = ""
    case_id: str = ""
    host: str = ""
    severity: Severity = Severity.MEDIUM
    confidence: Confidence = Confidence.MEDIUM
    evidence_ids: List[str] = field(default_factory=list)
    rules_fired: List[str] = field(default_factory=list)
    explanation: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.finding_id:
            self.finding_id = f"F-{secrets.token_hex(3).upper()}"
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["severity"] = self.severity.value
        d["confidence"] = self.confidence.value
        return d


@dataclass
class TimelineEvent:
    """A single event in the investigation timeline."""
    timestamp: str
    description: str
    host: str = ""
    evidence_id: str = ""
    event_type: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceGraph:
    """Graph of relationships between evidence artifacts."""
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)

    def add_node(self, evidence_id: str, label: str, node_type: str, **attrs):
        self.nodes.append({
            "id": evidence_id,
            "label": label,
            "type": node_type,
            **attrs,
        })

    def add_edge(self, source: str, target: str, relationship: str, **attrs):
        self.edges.append({
            "source": source,
            "target": target,
            "relationship": relationship,
            **attrs,
        })

    def to_dict(self) -> Dict[str, Any]:
        return {"nodes": self.nodes, "edges": self.edges}


@dataclass
class InvestigationCase:
    """A complete investigation case with all collected evidence and findings."""
    case_id: str = ""
    investigator: str = ""
    organization: str = ""
    endpoints: List[str] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    timeline: List[TimelineEvent] = field(default_factory=list)
    graph: Optional[EvidenceGraph] = None
    created_at: str = ""
    status: str = "ACTIVE"

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if self.graph is None:
            self.graph = EvidenceGraph()

    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        """Look up evidence by ID."""
        for e in self.evidence:
            if e.evidence_id == evidence_id:
                return e
        return None

    def validate_evidence_ids(self, ids: List[str]) -> List[str]:
        """Return any IDs that don't exist in this case."""
        valid_ids = {e.evidence_id for e in self.evidence}
        return [eid for eid in ids if eid not in valid_ids]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "investigator": self.investigator,
            "organization": self.organization,
            "endpoints": self.endpoints,
            "evidence_count": len(self.evidence),
            "evidence": [e.to_dict() for e in self.evidence],
            "findings": [f.to_dict() for f in self.findings],
            "timeline": [t.to_dict() for t in self.timeline],
            "graph": self.graph.to_dict() if self.graph else None,
            "created_at": self.created_at,
            "status": self.status,
        }
