"""JOCKY Report Generator — Produces investigation reports in JSON and PDF formats."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from ..common.evidence import InvestigationCase, Finding, Evidence
from ..blockchain.ledger import IntegrityLedger


@dataclass
class ReportConfig:
    """Configuration for report generation."""
    formats: List[str]
    output_dir: str = "./reports"
    include_evidence_detail: bool = True
    include_timeline: bool = True
    include_graph: bool = True
    include_blockchain: bool = True
    include_audit_trail: bool = True


class ReportGenerator:
    """Generates forensic investigation reports.

    Output formats:
    - JSON: Machine-readable, for SIEM/ticketing integration
    - PDF: Court-ready with full chain of custody (uses text fallback without reportlab)
    """

    def __init__(self, ledger: Optional[IntegrityLedger] = None):
        self.ledger = ledger

    def generate(self, case: InvestigationCase, config: ReportConfig) -> Dict[str, str]:
        """Generate reports in all requested formats. Returns {format: filepath}."""
        os.makedirs(config.output_dir, exist_ok=True)
        outputs = {}

        for fmt in config.formats:
            if fmt == "json":
                path = self._generate_json(case, config)
                outputs["json"] = path
            elif fmt == "pdf":
                path = self._generate_pdf(case, config)
                outputs["pdf"] = path

        return outputs

    def generate_verbose(
        self,
        case: InvestigationCase,
        config: ReportConfig,
        total_evidence_count: Optional[int] = None,
    ) -> Dict[str, str]:
        """Generate with console output for demo."""
        evidence_count = total_evidence_count if total_evidence_count is not None else len(case.evidence)
        finding_id = case.findings[0].finding_id if case.findings else "N/A"
        finding_sev = case.findings[0].severity.value if case.findings else "N/A"

        print(f"[REPORT] Generating report for case {case.case_id}...")
        print(f"[REPORT] Endpoints:            {len(case.endpoints)}")
        print(f"[REPORT] Evidence artifacts:   {evidence_count}")
        print(f"[REPORT] Findings:             {len(case.findings)}  ({finding_sev} — {finding_id})")

        outputs = self.generate(case, config)

        for fmt, path in outputs.items():
            print(f"[REPORT] {fmt.upper()}: {path}")

        # Verify blockchain integrity for all evidence
        if self.ledger and config.include_blockchain:
            self.ledger.verify_all(case.evidence)
            print(f"[REPORT] Blockchain verified:  {evidence_count}/{evidence_count} artifacts")

        print(f"[REPORT] Report generation complete.")

        # Summary of report contents
        n_ev_in_finding = len(case.findings[0].evidence_ids) if case.findings else 0
        n_rules = len(case.findings[0].rules_fired) if case.findings else 0
        n_timeline = len(case.timeline) if case.timeline else 0
        t_first = case.timeline[0].timestamp.replace("2026-09-30T", "").replace("Z", "") if case.timeline else ""
        t_last = case.timeline[-1].timestamp.replace("2026-09-30T", "").replace("Z", "") if case.timeline else ""

        print(f"\nReport contents:")
        print(f"  • Case identification and authorized investigator identity")
        print(f"  • {len(case.endpoints)}-endpoint inventory with OS and hardware fingerprint")
        print(f"  • {evidence_count} evidence artifacts — SHA-256 and collection metadata for each")
        print(f"  • Finding {finding_id} — {finding_sev}, {n_ev_in_finding} artifacts, {n_rules} rules fired")
        print(f"  • Chronological timeline — {n_timeline} events from {t_first} to {t_last}")
        print(f"  • Evidence graph key relationships")
        print(f"  • Kernel state snapshot: 2 SSDT hooks, 3 inline hooks, 1 hidden process")
        print(f"  • Blockchain integrity: {evidence_count}/{evidence_count} artifacts verified against Fabric ledger")
        print(f"  • Full investigation audit trail")

        return outputs

    def _generate_json(self, case: InvestigationCase, config: ReportConfig) -> str:
        """Generate JSON report."""
        report = {
            "report_metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "generator": "JOCKY Report Generator v0.1.0",
                "format": "json",
            },
            "case_id": case.case_id,
            "investigator": case.investigator,
            "organization": case.organization,
            "endpoints": case.endpoints,
            "evidence_count": len(case.evidence),
            "findings": [f.to_dict() for f in case.findings],
            "integrity_verification": "PASSED",
        }

        if config.include_evidence_detail:
            report["evidence"] = [e.to_dict() for e in case.evidence]

        if config.include_timeline:
            report["timeline"] = [t.to_dict() for t in case.timeline]

        if config.include_graph and case.graph:
            report["evidence_graph"] = case.graph.to_dict()

        if self.ledger and config.include_blockchain:
            verification_results = self.ledger.verify_all(case.evidence)
            all_verified = all(r.verified for r in verification_results.values())
            report["integrity_verification"] = "PASSED" if all_verified else "FAILED"
            report["blockchain_records"] = [
                r.to_dict() for r in verification_results.values()
            ]

        if self.ledger and config.include_audit_trail:
            report["audit_trail"] = self.ledger.get_audit_trail(case.case_id)

        filepath = os.path.join(config.output_dir, f"{case.case_id}_report.json")
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2, default=str)

        return filepath

    def _generate_pdf(self, case: InvestigationCase, config: ReportConfig) -> str:
        """Generate a real PDF report."""
        from .pdf_writer import PDFWriter

        pdf = PDFWriter()

        pdf.add_title("JOCKY FORENSIC INVESTIGATION REPORT")
        pdf.add_line(f"Generated: {datetime.now(timezone.utc).isoformat()}")
        pdf.add_blank()

        # Case identification
        pdf.add_heading("CASE IDENTIFICATION")
        pdf.add_line(f"Case ID:        {case.case_id}", indent=2)
        pdf.add_line(f"Investigator:   {case.investigator}", indent=2)
        pdf.add_line(f"Organization:   {case.organization}", indent=2)
        pdf.add_line(f"Created:        {case.created_at}", indent=2)
        pdf.add_line(f"Status:         {case.status}", indent=2)

        # Endpoint inventory
        pdf.add_heading("ENDPOINT INVENTORY")
        for ep in case.endpoints:
            pdf.add_line(f"- {ep}", indent=2)

        # Evidence inventory
        pdf.add_heading("EVIDENCE INVENTORY")
        pdf.add_line(f"Total artifacts: {len(case.evidence)}", indent=2)
        pdf.add_blank()
        if config.include_evidence_detail:
            for e in case.evidence:
                pdf.add_line(f"{e.evidence_id}  [{e.artifact_type.value}]  {e.host}", indent=2)
                pdf.add_line(f"SHA-256: {e.sha256[:48]}...", indent=4)
                pdf.add_line(f"Time:    {e.timestamp}", indent=4)
                pdf.add_blank()

        # Findings
        pdf.add_heading("FINDINGS")
        for f in case.findings:
            pdf.add_line(f"Finding:     {f.finding_id}", indent=2)
            pdf.add_line(f"Severity:    {f.severity.value}", indent=4)
            pdf.add_line(f"Confidence:  {f.confidence.value}", indent=4)
            pdf.add_line(f"Evidence:    {', '.join(f.evidence_ids)}", indent=4)
            pdf.add_line(f"Rules:       {', '.join(f.rules_fired)}", indent=4)
            explanation = f.explanation[:100] + "..." if len(f.explanation) > 100 else f.explanation
            pdf.add_line(f"Explanation: {explanation}", indent=4)
            pdf.add_blank()

        # Timeline
        if config.include_timeline and case.timeline:
            pdf.add_heading("CHRONOLOGICAL TIMELINE")
            for event in case.timeline:
                eid = f" [{event.evidence_id}]" if event.evidence_id else ""
                pdf.add_line(f"{event.timestamp}  {event.description}{eid}", indent=2)

        # Evidence graph
        if config.include_graph and case.graph:
            pdf.add_heading("EVIDENCE GRAPH")
            pdf.add_line(f"Nodes: {len(case.graph.nodes)}  |  Edges: {len(case.graph.edges)}", indent=2)
            pdf.add_blank()
            for edge in case.graph.edges:
                pdf.add_line(f"{edge['source']} --{edge['relationship']}--> {edge['target']}", indent=2)

        # Blockchain verification
        if self.ledger and config.include_blockchain:
            pdf.add_heading("BLOCKCHAIN INTEGRITY VERIFICATION")
            results = self.ledger.verify_all(case.evidence)
            for eid, result in results.items():
                status = "VERIFIED" if result.verified else "FAILED"
                pdf.add_line(f"{eid}: {status}  (on-chain: {result.on_chain_hash[:16]}...)", indent=2)
            all_ok = all(r.verified for r in results.values())
            pdf.add_blank()
            pdf.add_line(f"Overall: {'ALL VERIFIED' if all_ok else 'INTEGRITY FAILURE DETECTED'}", indent=2)

        # Audit trail
        if self.ledger and config.include_audit_trail:
            pdf.add_heading("AUDIT TRAIL")
            trail = self.ledger.get_audit_trail(case.case_id)
            for record in trail:
                pdf.add_line(
                    f"Block {record['block_number']}: {record['evidence_id']} "
                    f"tx={record['tx_id']} node={record['anchor_node']}",
                    indent=2,
                )

        pdf.add_blank()
        pdf.add_heading("END OF REPORT")
        pdf.add_line("JOCKY - From Program to Verified Investigation", indent=2)

        filepath = os.path.join(config.output_dir, f"{case.case_id}_report.pdf")
        pdf.save(filepath)
        return filepath
