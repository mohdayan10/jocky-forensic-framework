"""JOCKY Blockchain Integrity Ledger — Evidence hash anchoring and verification.

In production, this integrates with Hyperledger Fabric. This implementation
provides a local simulation with the same interface and verification semantics.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from ..common.evidence import Evidence


@dataclass
class LedgerRecord:
    """A single record on the integrity ledger."""
    evidence_id: str
    case_id: str
    sha256: str
    timestamp: str
    block_number: int = 0
    tx_id: str = ""
    anchor_node: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "case_id": self.case_id,
            "sha256": self.sha256,
            "timestamp": self.timestamp,
            "block_number": self.block_number,
            "tx_id": self.tx_id,
            "anchor_node": self.anchor_node,
        }


@dataclass
class VerificationResult:
    """Result of verifying evidence against the ledger."""
    evidence_id: str
    on_chain_hash: str
    current_hash: str
    match: bool
    verified: bool
    tamper_detected_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "on_chain_hash": self.on_chain_hash,
            "current_hash": self.current_hash,
            "match": self.match,
            "integrity_verified": self.verified,
            "tamper_detected_at": self.tamper_detected_at,
        }


class IntegrityLedger:
    """Simulated Hyperledger Fabric integrity ledger.

    In production, this would use the Fabric SDK to:
    - Submit evidence hashes to the chaincode
    - Query the ledger for verification
    - Validate across multiple peer nodes

    This simulation provides the same API and verification semantics.
    """

    def __init__(self):
        self.records: Dict[str, LedgerRecord] = {}  # evidence_id → record
        self.block_count = 0
        self.nodes = ["peer0.ntro.gov.in", "peer0.agency.gov.in", "peer0.auditor.org"]

    def anchor(self, evidence: Evidence, case_id: str) -> LedgerRecord:
        """Anchor an evidence hash to the ledger (simulates chaincode invoke)."""
        self.block_count += 1
        tx_id = hashlib.sha256(
            f"{evidence.evidence_id}:{evidence.sha256}:{time.time()}".encode()
        ).hexdigest()[:16]

        record = LedgerRecord(
            evidence_id=evidence.evidence_id,
            case_id=case_id,
            sha256=evidence.sha256,
            timestamp=datetime.now(timezone.utc).isoformat(),
            block_number=self.block_count,
            tx_id=tx_id,
            anchor_node=self.nodes[self.block_count % len(self.nodes)],
        )

        self.records[evidence.evidence_id] = record
        return record

    def anchor_batch(self, evidence_list: List[Evidence], case_id: str) -> List[LedgerRecord]:
        """Anchor multiple evidence artifacts in one batch."""
        records = []
        for e in evidence_list:
            records.append(self.anchor(e, case_id))
        return records

    def verify(self, evidence: Evidence) -> VerificationResult:
        """Verify evidence integrity against the ledger."""
        record = self.records.get(evidence.evidence_id)

        if record is None:
            return VerificationResult(
                evidence_id=evidence.evidence_id,
                on_chain_hash="NOT FOUND",
                current_hash=evidence.sha256,
                match=False,
                verified=False,
            )

        current_hash = evidence.compute_hash()
        match = record.sha256 == current_hash

        return VerificationResult(
            evidence_id=evidence.evidence_id,
            on_chain_hash=record.sha256,
            current_hash=current_hash,
            match=match,
            verified=match,
            tamper_detected_at=None if match else datetime.now(timezone.utc).isoformat(),
        )

    def verify_verbose(self, evidence: Evidence) -> VerificationResult:
        """Verify with [BLOCKCHAIN] status output for demo."""
        print("[BLOCKCHAIN] Querying Hyperledger Fabric ledger...")
        result = self.verify(evidence)

        print(f"[BLOCKCHAIN] Evidence ID:    {result.evidence_id}")
        print(f"[BLOCKCHAIN] On-chain hash:  {result.on_chain_hash[:16]}...{result.on_chain_hash[-4:]}")
        print(f"[BLOCKCHAIN] Current hash:   {result.current_hash[:16]}...{result.current_hash[-4:]}")
        print(f"[BLOCKCHAIN] Match:          {'YES' if result.match else 'NO'}")

        if result.verified:
            print("[BLOCKCHAIN] INTEGRITY VERIFIED — artifact unchanged since collection")
        else:
            print("[BLOCKCHAIN] INTEGRITY FAILURE — artifact does not match ledger record")
            if result.tamper_detected_at:
                print(f"[BLOCKCHAIN] Tamper detected at: {result.tamper_detected_at}")

        return result

    def verify_all(self, evidence_list: List[Evidence]) -> Dict[str, VerificationResult]:
        """Verify all evidence artifacts in a case."""
        results = {}
        for e in evidence_list:
            results[e.evidence_id] = self.verify(e)
        return results

    def get_audit_trail(self, case_id: str) -> List[Dict[str, Any]]:
        """Get the full audit trail for a case."""
        trail = []
        for record in self.records.values():
            if record.case_id == case_id:
                trail.append(record.to_dict())
        return sorted(trail, key=lambda r: r["block_number"])
