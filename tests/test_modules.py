"""Tests for JOCKY framework modules (non-compiler)."""

import unittest
import json
import os
import tempfile

from jocky.common.evidence import (
    Evidence, Finding, ArtifactType, Severity, Confidence,
    TimelineEvent, EvidenceGraph, InvestigationCase,
)
from jocky.correlation.engine import CorrelationEngine
from jocky.blockchain.ledger import IntegrityLedger
from jocky.ai_assistant.assistant import ForensicAssistant
from jocky.report.generator import ReportGenerator, ReportConfig
from jocky.kernel.collector import KernelCollector
from jocky.forge.builder import ForgeBuilder
from jocky.spectre.agent import SpectreAgent
from jocky.beacon.beacon import BeaconManager
from jocky.console.dispatch import CommandConsole


def _make_evidence():
    return [
        Evidence(evidence_id="E-00101", artifact_type=ArtifactType.FILE, host="H1",
                 data={"path": r"C:\Temp\bad.exe", "signed": False, "pe_header": True}),
        Evidence(evidence_id="E-00102", artifact_type=ArtifactType.PROCESS, host="H1",
                 data={"pid": 100, "name": "bad.exe"}),
        Evidence(evidence_id="E-00103", artifact_type=ArtifactType.NETWORK, host="H1",
                 data={"pid": 100, "destination": "10.0.0.1", "port": 443}),
        Evidence(evidence_id="E-00104", artifact_type=ArtifactType.DRIVER, host="H1",
                 data={"name": "VulnDrv.sys", "cve": "CVE-2021-21551"}),
        Evidence(evidence_id="E-00105", artifact_type=ArtifactType.PERSISTENCE, host="H1",
                 data={"mechanism": "Run Key"}),
        Evidence(evidence_id="E-00106", artifact_type=ArtifactType.HIDDEN_PROCESS, host="H1",
                 data={"pid": 999, "name": "hidden.exe"}),
    ]


def _make_case():
    return InvestigationCase(
        case_id="TEST-01", investigator="Test", organization="Test Org",
        endpoints=["H1"], evidence=_make_evidence(),
    )


class TestEvidence(unittest.TestCase):
    def test_auto_id(self):
        e = Evidence(artifact_type=ArtifactType.PROCESS, data={"pid": 1})
        self.assertTrue(e.evidence_id.startswith("E-"))

    def test_hash_deterministic(self):
        e1 = Evidence(data={"key": "value"})
        e2 = Evidence(data={"key": "value"})
        self.assertEqual(e1.compute_hash(), e2.compute_hash())

    def test_to_dict(self):
        e = Evidence(evidence_id="E-X", artifact_type=ArtifactType.FILE, data={"a": 1})
        d = e.to_dict()
        self.assertEqual(d["evidence_id"], "E-X")
        self.assertEqual(d["artifact_type"], "FILE")


class TestCorrelation(unittest.TestCase):
    def test_multiple_signals_generate_finding(self):
        engine = CorrelationEngine()
        findings = engine.correlate(_make_evidence(), "TEST", "H1")
        self.assertTrue(len(findings) > 0)
        self.assertEqual(findings[0].severity, Severity.CRITICAL)

    def test_single_signal_no_finding(self):
        engine = CorrelationEngine()
        evidence = [Evidence(artifact_type=ArtifactType.PROCESS, data={"pid": 1})]
        findings = engine.correlate(evidence)
        self.assertEqual(len(findings), 0)


class TestBlockchain(unittest.TestCase):
    def test_anchor_and_verify(self):
        ledger = IntegrityLedger()
        e = Evidence(evidence_id="E-TEST", data={"key": "val"})
        ledger.anchor(e, "CASE-1")
        result = ledger.verify(e)
        self.assertTrue(result.verified)

    def test_tamper_detected(self):
        ledger = IntegrityLedger()
        e = Evidence(evidence_id="E-TEST", data={"key": "val"})
        ledger.anchor(e, "CASE-1")
        e.data["tampered"] = True
        result = ledger.verify(e)
        self.assertFalse(result.verified)

    def test_audit_trail(self):
        ledger = IntegrityLedger()
        for ev in _make_evidence()[:3]:
            ledger.anchor(ev, "CASE-1")
        trail = ledger.get_audit_trail("CASE-1")
        self.assertEqual(len(trail), 3)


class TestAIAssistant(unittest.TestCase):
    def test_valid_citations_accepted(self):
        case = _make_case()
        assistant = ForensicAssistant(case)
        finding = Finding(evidence_ids=["E-00101", "E-00102"], rules_fired=["TEST"])
        response = assistant.explain_finding(finding)
        self.assertTrue(response.accepted)

    def test_invalid_citation_rejected(self):
        case = _make_case()
        assistant = ForensicAssistant(case)
        response = assistant.validate_external_response("See evidence [E-99999]")
        self.assertFalse(response.accepted)


class TestReport(unittest.TestCase):
    def test_json_report(self):
        case = _make_case()
        case.findings = CorrelationEngine().correlate(case.evidence, "TEST", "H1")
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReportConfig(formats=["json"], output_dir=tmpdir)
            generator = ReportGenerator()
            outputs = generator.generate(case, config)
            self.assertIn("json", outputs)
            with open(outputs["json"]) as f:
                data = json.load(f)
            self.assertEqual(data["case_id"], "TEST-01")


class TestKernel(unittest.TestCase):
    def test_hidden_process_detection(self):
        collector = KernelCollector()
        result = collector.collect("H1", "HIDDEN_PROCESS_DELTA")
        self.assertTrue(result.success)
        self.assertTrue(len(result.evidence) > 0)

    def test_hook_state(self):
        result = KernelCollector().collect("H1", "HOOK_STATE")
        self.assertTrue(result.success)

    def test_driver_intel(self):
        result = KernelCollector().collect("H1", "DRIVER_INTELLIGENCE")
        self.assertTrue(result.success)
        self.assertTrue(result.data["byovd_count"] > 0)


class TestForge(unittest.TestCase):
    def test_polymorphic_builds_unique(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = ForgeBuilder(output_dir=tmpdir)
            source = 'case "T"\ntarget hostgroup ENTERPRISE_EAST\ncollect processes'
            builds = builder.deploy(source, "t.jky", ["H1", "H2"])
            self.assertEqual(len(builds), 2)
            self.assertNotEqual(builds[0].sha256, builds[1].sha256)


class TestSpectre(unittest.TestCase):
    def test_process_hollow(self):
        agent = SpectreAgent()
        result = agent.deploy("PROCESS_HOLLOW", "H1")
        self.assertTrue(result.success)
        self.assertFalse(result.details["file_written_to_disk"])

    def test_reflective_dll(self):
        result = SpectreAgent().deploy("REFLECTIVE_DLL", "H1", "explorer.exe")
        self.assertTrue(result.success)
        self.assertEqual(result.api_surface["LoadLibrary"], 0)

    def test_direct_syscall(self):
        result = SpectreAgent().deploy("DIRECT_SYSCALL", "H1")
        self.assertTrue(result.success)
        self.assertEqual(result.details["win32_api_calls"], 0)

    def test_unknown_strategy(self):
        result = SpectreAgent().deploy("UNKNOWN", "H1")
        self.assertFalse(result.success)


class TestBeacon(unittest.TestCase):
    def test_establish_channel(self):
        manager = BeaconManager()
        channel = manager.establish("H1")
        self.assertEqual(channel.status, "ACTIVE")
        self.assertTrue(channel.mtls_active)

    def test_network_footprint(self):
        manager = BeaconManager()
        channel = manager.establish("H1")
        footprint = manager.get_network_footprint(channel)
        self.assertEqual(footprint.jocky_domains_visible, 0)
        self.assertEqual(footprint.total_connections, 1)


class TestConsole(unittest.TestCase):
    def test_dispatch(self):
        console = CommandConsole()
        result = console.dispatch("CASE-1", ["HOST-01", "HOST-02"])
        self.assertEqual(len(result.endpoints), 2)
        self.assertTrue(result.total_evidence > 0)

    def test_cross_host_query(self):
        console = CommandConsole()
        matches = console.cross_host_query("abc123", ["HOST-01", "HOST-02"])
        self.assertEqual(len(matches), 2)


if __name__ == "__main__":
    unittest.main()
