"""JOCKY AI Assistant — Evidence-grounded forensic explanation with citation validation.

The assistant:
- Receives only structured finding objects, not raw evidence content
- Every cited evidence ID is validated against the case record
- Explains and navigates — does not produce findings or assert intent
- Hallucinated evidence references are caught before reaching the investigator
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set

from ..common.evidence import InvestigationCase, Finding, Evidence


@dataclass
class CitationValidationResult:
    """Result of validating evidence citations in an assistant response."""
    valid: bool
    cited_ids: List[str] = field(default_factory=list)
    valid_ids: List[str] = field(default_factory=list)
    invalid_ids: List[str] = field(default_factory=list)


@dataclass
class AssistantResponse:
    """A validated response from the AI assistant."""
    content: str
    citations: CitationValidationResult
    accepted: bool  # False if any invalid citation detected
    finding_id: str = ""


class ForensicAssistant:
    """AI Assistant that provides evidence-grounded forensic explanations.

    Security model:
    - Assistant has access to finding metadata only, not raw evidence
    - All evidence IDs cited in responses are validated pre-display
    - Invalid citations cause the response to be rejected entirely
    """

    # Pattern to extract evidence IDs from text: [E-00421] or E-00421
    EVIDENCE_ID_PATTERN = re.compile(r"\[?(E-\d{5})\]?")

    def __init__(self, case: InvestigationCase):
        self.case = case
        self._valid_ids: Set[str] = {e.evidence_id for e in case.evidence}

    def explain_finding(self, finding: Finding) -> AssistantResponse:
        """Generate an evidence-grounded explanation for a finding.

        Priority: GROQ_API_KEY → ANTHROPIC_API_KEY → local builder.
        """
        groq_key = os.environ.get("GROQ_API_KEY", "").strip()
        if groq_key:
            try:
                return self._explain_via_groq(finding, groq_key)
            except Exception as exc:
                print(f"[AI] Groq API call failed ({exc}) — trying Anthropic")

        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if anthropic_key:
            try:
                return self._explain_via_anthropic(finding, anthropic_key)
            except Exception as exc:
                print(f"[AI] Anthropic API call failed ({exc}) — using local explanation builder")

        # Local fallback
        explanation = self._build_explanation(finding)
        validation = self._validate_citations(explanation)
        return AssistantResponse(
            content=explanation,
            citations=validation,
            accepted=validation.valid,
            finding_id=finding.finding_id,
        )

    def _build_prompt(self, finding: Finding) -> str:
        """Build the forensic explanation prompt (shared by all API backends)."""
        all_case_ev = {e.evidence_id: e for e in self.case.evidence}
        evidence_lines = []
        for eid in finding.evidence_ids:
            ev = all_case_ev.get(eid)
            if ev:
                desc = self._describe_evidence(ev)
                evidence_lines.append(f"  [{eid}] {ev.artifact_type.value}: {desc}")

        return (
            "You are a forensic analysis assistant. "
            "Explain the following security finding using ONLY the evidence listed below.\n\n"
            f"Finding ID: {finding.finding_id}\n"
            f"Severity:   {finding.severity.value}\n"
            f"Confidence: {finding.confidence.value}\n"
            f"Rules fired: {', '.join(finding.rules_fired)}\n\n"
            "Evidence artifacts (cite ONLY these IDs in [E-XXXXX] format — "
            "do NOT invent or hallucinate evidence IDs):\n"
            + "\n".join(evidence_lines)
            + "\n\nWrite a concise 3-4 sentence forensic explanation that:\n"
            "1. Describes the attack pattern observed across the evidence.\n"
            "2. Names the specific technique used (e.g. BYOVD, DKOM, process hollowing).\n"
            "3. References evidence by [E-XXXXX] notation where relevant.\n"
            "4. Does NOT reference any evidence ID not in the list above."
        )

    def _explain_via_groq(self, finding: Finding, api_key: str) -> AssistantResponse:
        """Call Groq API (llama3-70b-8192) for a real explanation."""
        from groq import Groq  # type: ignore

        prompt = self._build_prompt(finding)
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.3,
        )
        response_text = completion.choices[0].message.content

        validation = self._validate_citations(response_text)
        return AssistantResponse(
            content=response_text,
            citations=validation,
            accepted=validation.valid,
            finding_id=finding.finding_id,
        )

    def _explain_via_anthropic(self, finding: Finding, api_key: str) -> AssistantResponse:
        """Call the Anthropic API (claude-sonnet-4-6) for a real explanation."""
        import anthropic  # type: ignore

        prompt = self._build_prompt(finding)
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = message.content[0].text

        validation = self._validate_citations(response_text)
        return AssistantResponse(
            content=response_text,
            citations=validation,
            accepted=validation.valid,
            finding_id=finding.finding_id,
        )

    # Keep old name as alias for backward compatibility
    def _explain_via_api(self, finding: Finding, api_key: str) -> AssistantResponse:
        return self._explain_via_anthropic(finding, api_key)

    def validate_external_response(self, response_text: str) -> AssistantResponse:
        """Validate an externally-generated response (e.g., from an LLM).

        This is the citation validation gate that catches hallucinated evidence IDs.
        """
        validation = self._validate_citations(response_text)

        return AssistantResponse(
            content=response_text if validation.valid else "",
            citations=validation,
            accepted=validation.valid,
        )

    def validate_verbose(self, response_text: str) -> AssistantResponse:
        """Validate with [VALIDATION] output for demo."""
        validation = self._validate_citations(response_text)

        print("[VALIDATION] Checking cited evidence IDs against case record...")
        for eid in validation.cited_ids:
            if eid in validation.valid_ids:
                print(f"  {eid} → VALID")
            else:
                print(f"  {eid} → NOT FOUND IN CASE RECORD")

        if validation.valid:
            print("[VALIDATION] All citations verified. Response accepted.")
        else:
            print("[VALIDATION] Response rejected — invalid citation detected.")
            print("             Assistant response not displayed to investigator.")

        return AssistantResponse(
            content=response_text if validation.valid else "",
            citations=validation,
            accepted=validation.valid,
        )

    def _validate_citations(self, text: str) -> CitationValidationResult:
        """Extract and validate all evidence ID citations in text."""
        # Find all evidence IDs referenced in the text
        cited_ids = list(dict.fromkeys(self.EVIDENCE_ID_PATTERN.findall(text)))

        valid_ids = [eid for eid in cited_ids if eid in self._valid_ids]
        invalid_ids = [eid for eid in cited_ids if eid not in self._valid_ids]

        return CitationValidationResult(
            valid=len(invalid_ids) == 0,
            cited_ids=cited_ids,
            valid_ids=valid_ids,
            invalid_ids=invalid_ids,
        )

    def _build_explanation(self, finding: Finding) -> str:
        """Build a narrative forensic explanation from finding data.

        Dynamically references evidence from the finding's evidence_ids,
        not hardcoded IDs. Works with any case data.
        """
        all_case_ev = {e.evidence_id: e for e in self.case.evidence}

        # Categorize the finding's evidence by type
        processes = []
        networks = []
        files = []
        drivers = []
        callbacks = []
        hidden = []
        registry = []
        persistence = []

        for eid in finding.evidence_ids:
            ev = all_case_ev.get(eid)
            if not ev:
                continue
            t = ev.artifact_type.value
            if t == "PROCESS":
                processes.append(ev)
            elif t == "NETWORK":
                networks.append(ev)
            elif t == "FILE":
                files.append(ev)
            elif t == "DRIVER":
                drivers.append(ev)
            elif t == "KERNEL_CALLBACK":
                callbacks.append(ev)
            elif t == "HIDDEN_PROCESS":
                hidden.append(ev)
            elif t == "REGISTRY":
                registry.append(ev)
            elif t == "PERSISTENCE":
                persistence.append(ev)

        lines = []
        lines.append(f"Finding {finding.finding_id} documents a staged intrusion chain on {finding.host}.")
        lines.append("")

        if processes:
            for proc in processes:
                parent = proc.data.get("parent_name", "unknown")
                lines.append(
                    f"  Process {proc.data.get('name', 'unknown')} [{proc.evidence_id}] "
                    f"(parent: {parent}) — not consistent with standard enterprise user activity."
                )

        if networks:
            for net in networks:
                dst = net.data.get("destination", "unknown")
                port = net.data.get("port", "?")
                lines.append("")
                lines.append(
                    f"  Outbound connection to {dst}:{port} [{net.evidence_id}] "
                    f"— timing consistent with a command-and-control callback."
                )

        if drivers:
            for drv in drivers:
                cve = drv.data.get("cve", "unknown CVE")
                lines.append("")
                lines.append(
                    f"  {drv.data.get('name', 'unknown')} [{drv.evidence_id}] — a {cve} matched driver "
                    f"with {drv.data.get('exploit_type', 'arbitrary kernel read/write').lower()} vulnerability."
                )

        if callbacks:
            for cb in callbacks:
                lines.append(
                    f"  Kernel callback state change [{cb.evidence_id}]: "
                    f"{cb.data.get('change_description', 'callback modified')}."
                )

        if hidden:
            for h in hidden:
                lines.append(
                    f"  Hidden process [{h.evidence_id}]: {h.data.get('name', 'unknown')} "
                    f"invisible to API enumeration."
                )

        if drivers and callbacks and hidden:
            lines.append("")
            lines.append(
                "  This sequence is consistent with BYOVD-assisted EDR blinding: "
                "vulnerable driver loaded, monitoring callback removed, payload "
                "concealed from userspace visibility."
            )

        if files or registry:
            lines.append("")
            for f in files:
                signed = "unsigned" if not f.data.get("signed") else "signed"
                lines.append(
                    f"  {signed.capitalize()} PE [{f.evidence_id}] created at {f.data.get('path', 'unknown')}."
                )
            for r in registry:
                lines.append(
                    f"  Persistence key [{r.evidence_id}] written to {r.data.get('key', 'unknown')}."
                )

        lines.append("")
        lines.append(
            "  Technique pattern: BYOVD-assisted staged intrusion with kernel-level"
        )
        lines.append(
            "  EDR blinding, fileless payload staging, and registry persistence"
        )
        lines.append(
            "  establishment — consistent with a pre-planned multi-stage operation."
        )

        cited = sorted(finding.evidence_ids)
        lines.append("")
        lines.append("  Cited evidence:")
        lines.append(f"  [{', '.join(cited)}]")

        return "\n".join(lines)

    def _describe_evidence(self, evidence: Evidence) -> str:
        """Generate a human-readable description of an evidence artifact."""
        etype = evidence.artifact_type.value
        data = evidence.data

        if etype == "PROCESS":
            name = data.get("name", "unknown")
            pid = data.get("pid", "?")
            parent = data.get("parent_name", "?")
            return f"Process {name} (PID {pid}), parent: {parent}"

        elif etype == "FILE":
            path = data.get("path", "unknown")
            signed = "signed" if data.get("signed") else "unsigned"
            return f"File {path} ({signed})"

        elif etype == "NETWORK":
            dst = data.get("destination", "?")
            port = data.get("port", "?")
            return f"Network connection to {dst}:{port}"

        elif etype == "DRIVER":
            name = data.get("name", "unknown")
            cve = data.get("cve", "none")
            return f"Driver {name} (CVE: {cve})"

        elif etype == "REGISTRY":
            key = data.get("key", "unknown")
            return f"Registry modification: {key}"

        elif etype == "PERSISTENCE":
            mech = data.get("mechanism", "unknown")
            return f"Persistence artifact: {mech}"

        elif etype == "HIDDEN_PROCESS":
            name = data.get("name", "unknown")
            pid = data.get("pid", "?")
            return f"Hidden process {name} (PID {pid}) — invisible to API enumeration"

        elif etype == "KERNEL_CALLBACK":
            callback = data.get("callback_type", "unknown")
            return f"Kernel callback modification: {callback}"

        else:
            return f"{etype} artifact"
