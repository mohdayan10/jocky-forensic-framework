"""JOCKY Correlation Engine — Detects multi-signal patterns across evidence artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Callable, Optional, Any
from datetime import datetime, timezone

from ..common.evidence import (
    Evidence, Finding, ArtifactType,
    Severity, Confidence, TimelineEvent,
)


@dataclass
class CorrelationSignal:
    """A single matched signal from a detection rule."""
    rule_name: str
    description: str
    evidence_ids: List[str] = field(default_factory=list)
    matched: bool = False


@dataclass
class DetectionRule:
    """A detection rule that evaluates evidence for suspicious indicators."""
    name: str
    display_name: str
    description: str
    min_severity: Severity = Severity.MEDIUM
    evaluate: Callable[[List[Evidence]], Optional[CorrelationSignal]] = None


class CorrelationEngine:
    """Correlates evidence artifacts to generate findings.

    Key principles:
    - Single-artifact signals are indicators, not findings
    - Engine requires multi-signal correlation to raise a finding
    - Severity (impact) and Confidence (evidential strength) are separate
    - Every finding links directly to evidence IDs
    """

    def __init__(self):
        self.rules: List[DetectionRule] = []
        self._register_builtin_rules()

    def _register_builtin_rules(self):
        """Register the built-in detection rules."""
        self.rules = [
            DetectionRule(
                name="UNSIGNED_TEMP_EXE",
                display_name="Unsigned executable in Temp",
                description="Detects unsigned PE files created in temporary directories",
                min_severity=Severity.MEDIUM,
                evaluate=self._rule_unsigned_temp_exe,
            ),
            DetectionRule(
                name="RAPID_OUTBOUND",
                display_name="Rapid outbound connection",
                description="Detects outbound network connections within seconds of process creation",
                min_severity=Severity.MEDIUM,
                evaluate=self._rule_rapid_outbound,
            ),
            DetectionRule(
                name="BYOVD_DRIVER",
                display_name="CVE-matched vulnerable driver",
                description="Detects loaded drivers matching known CVE-vulnerable driver database",
                min_severity=Severity.HIGH,
                evaluate=self._rule_byovd_driver,
            ),
            DetectionRule(
                name="PERSISTENCE_WRITE",
                display_name="Persistence artifact written",
                description="Detects registry run key or scheduled task creation",
                min_severity=Severity.MEDIUM,
                evaluate=self._rule_persistence_write,
            ),
            DetectionRule(
                name="HIDDEN_PROCESS_DELTA",
                display_name="Hidden process detected",
                description="Detects processes visible via kernel walk but hidden from API",
                min_severity=Severity.CRITICAL,
                evaluate=self._rule_hidden_process,
            ),
            DetectionRule(
                name="KERNEL_CALLBACK_MOD",
                display_name="Kernel callback state change",
                description="Detects modification of kernel notification callbacks",
                min_severity=Severity.HIGH,
                evaluate=self._rule_callback_mod,
            ),
        ]

    def correlate(self, evidence: List[Evidence], case_id: str = "", host: str = "") -> List[Finding]:
        """Run all detection rules against evidence and generate findings."""
        signals: List[CorrelationSignal] = []

        for rule in self.rules:
            if rule.evaluate:
                signal = rule.evaluate(evidence)
                if signal and signal.matched:
                    signals.append(signal)

        if not signals:
            return []

        return self._generate_findings(signals, case_id, host)

    def correlate_verbose(self, evidence: List[Evidence], case_id: str = "", host: str = "") -> List[Finding]:
        """Correlate with console output matching the demo format."""
        signals: List[CorrelationSignal] = []

        for rule in self.rules:
            if rule.evaluate:
                signal = rule.evaluate(evidence)
                if signal and signal.matched:
                    signals.append(signal)
                    evidence_str = ", ".join(signal.evidence_ids)
                    print(f"[CORRELATE] {rule.display_name + ':':<40} MATCH  ({evidence_str})")
                else:
                    print(f"[CORRELATE] {rule.display_name + ':':<40} —")

        if not signals:
            print("\n[ENGINE] No correlated signals. No findings raised.")
            return []

        findings = self._generate_findings(signals, case_id, host)
        print(f"\n[ENGINE] {len(signals)} signals across {len(self.rules)} rules → FINDING RAISED")

        for finding in findings:
            self._print_finding(finding)

        return findings

    def _generate_findings(self, signals: List[CorrelationSignal], case_id: str, host: str) -> List[Finding]:
        """Generate findings from correlated signals.

        Requires at least 2 signals to raise a finding.
        More signals → higher confidence.
        """
        if len(signals) < 2:
            return []

        # Collect all evidence IDs and rules
        all_evidence_ids = []
        all_rules = []
        for sig in signals:
            all_evidence_ids.extend(sig.evidence_ids)
            all_rules.append(sig.rule_name)

        # Deduplicate evidence IDs while preserving order
        seen = set()
        unique_evidence = []
        for eid in all_evidence_ids:
            if eid not in seen:
                seen.add(eid)
                unique_evidence.append(eid)

        # Determine severity from the highest-severity rule
        max_severity = Severity.LOW
        severity_order = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
        for rule in self.rules:
            if rule.name in all_rules:
                if severity_order.index(rule.min_severity) > severity_order.index(max_severity):
                    max_severity = rule.min_severity

        # Confidence based on signal count
        if len(signals) >= 5:
            confidence = Confidence.HIGH
        elif len(signals) >= 3:
            confidence = Confidence.MEDIUM
        else:
            confidence = Confidence.LOW

        # Build explanation
        explanations = [sig.description for sig in signals]
        explanation = " ".join(explanations)
        explanation += f" {len(signals)} correlated indicators across {len(unique_evidence)} evidence artifacts."

        finding = Finding(
            case_id=case_id,
            host=host,
            severity=max_severity,
            confidence=confidence,
            evidence_ids=unique_evidence,
            rules_fired=all_rules,
            explanation=explanation,
        )

        return [finding]

    def _print_finding(self, finding: Finding):
        """Print a finding in demo format."""
        print(f"\nFinding ID:    {finding.finding_id}")
        print(f"Case:          {finding.case_id}")
        print(f"Host:          {finding.host}")
        print(f"Severity:      {finding.severity.value}")
        print(f"Confidence:    {finding.confidence.value}")
        print(f"Evidence:      {len(finding.evidence_ids)} artifacts {finding.evidence_ids}")
        print(f"Rules fired:   {', '.join(finding.rules_fired)}")
        print(f"\nExplanation:")
        print(f"  {finding.explanation}")

    # ── Detection rule implementations ──

    def _rule_unsigned_temp_exe(self, evidence: List[Evidence]) -> Optional[CorrelationSignal]:
        """Detect unsigned executables in temporary directories."""
        signal = CorrelationSignal(
            rule_name="UNSIGNED_TEMP_EXE",
            description="Unsigned executable created in Temp directory.",
        )
        for e in evidence:
            if e.artifact_type == ArtifactType.FILE:
                path = e.data.get("path", "").lower()
                signed = e.data.get("signed", True)
                is_pe = e.data.get("pe_header", False) or path.endswith((".exe", ".dll"))
                if not signed and is_pe and ("temp" in path or "appdata" in path):
                    signal.evidence_ids.append(e.evidence_id)
                    signal.matched = True
        return signal

    def _rule_rapid_outbound(self, evidence: List[Evidence]) -> Optional[CorrelationSignal]:
        """Detect process creation followed by outbound connection within 30s."""
        signal = CorrelationSignal(
            rule_name="RAPID_OUTBOUND",
            description="Outbound connection established within 30 seconds of process creation.",
        )
        processes = [e for e in evidence if e.artifact_type == ArtifactType.PROCESS]
        networks = [e for e in evidence if e.artifact_type == ArtifactType.NETWORK]

        for proc in processes:
            for net in networks:
                proc_pid = proc.data.get("pid")
                net_pid = net.data.get("pid")
                if proc_pid and net_pid and proc_pid == net_pid:
                    signal.evidence_ids.extend([proc.evidence_id, net.evidence_id])
                    signal.matched = True
                    return signal
        return signal

    def _rule_byovd_driver(self, evidence: List[Evidence]) -> Optional[CorrelationSignal]:
        """Detect CVE-matched vulnerable drivers."""
        signal = CorrelationSignal(
            rule_name="BYOVD_DRIVER",
            description="CVE-matched vulnerable driver loaded.",
        )
        for e in evidence:
            if e.artifact_type == ArtifactType.DRIVER:
                cve = e.data.get("cve")
                if cve:
                    signal.evidence_ids.append(e.evidence_id)
                    signal.matched = True
        return signal

    def _rule_persistence_write(self, evidence: List[Evidence]) -> Optional[CorrelationSignal]:
        """Detect persistence artifact creation."""
        signal = CorrelationSignal(
            rule_name="PERSISTENCE_WRITE",
            description="Persistence artifact written.",
        )
        for e in evidence:
            if e.artifact_type == ArtifactType.PERSISTENCE:
                signal.evidence_ids.append(e.evidence_id)
                signal.matched = True
            elif e.artifact_type == ArtifactType.REGISTRY:
                key = e.data.get("key", "").lower()
                if "run" in key or "startup" in key:
                    signal.evidence_ids.append(e.evidence_id)
                    signal.matched = True
        return signal

    def _rule_hidden_process(self, evidence: List[Evidence]) -> Optional[CorrelationSignal]:
        """Detect DKOM-hidden processes."""
        signal = CorrelationSignal(
            rule_name="HIDDEN_PROCESS_DELTA",
            description="Process hidden from API enumeration but visible via kernel walk.",
        )
        for e in evidence:
            if e.artifact_type == ArtifactType.HIDDEN_PROCESS:
                signal.evidence_ids.append(e.evidence_id)
                signal.matched = True
        return signal

    def _rule_callback_mod(self, evidence: List[Evidence]) -> Optional[CorrelationSignal]:
        """Detect kernel callback state modifications."""
        signal = CorrelationSignal(
            rule_name="KERNEL_CALLBACK_MOD",
            description="Kernel callback state change detected.",
        )
        for e in evidence:
            if e.artifact_type == ArtifactType.KERNEL_CALLBACK:
                if e.data.get("modified") or e.data.get("removed"):
                    signal.evidence_ids.append(e.evidence_id)
                    signal.matched = True
        return signal
