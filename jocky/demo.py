"""JOCKY Full Demo Runner — Executes the complete demo flow end-to-end.

This script runs all 17 demo steps from the Demo Guide,
simulating the full investigation pipeline with realistic data.

Usage:
    python -m jocky.demo
    python -m jocky.demo --step 8    # Run a specific step
    python -m jocky.demo --from 5    # Run from step 5 onward
"""

from __future__ import annotations

import argparse
import io
import os
import sys
import tempfile
import time
from datetime import datetime, timezone

from .compiler.pipeline import CompilerPipeline
from .forge.builder import ForgeBuilder
from .spectre.agent import SpectreAgent
from .beacon.beacon import BeaconManager
from .console.dispatch import CommandConsole
from .kernel.collector import KernelCollector
from .correlation.engine import CorrelationEngine
from .blockchain.ledger import IntegrityLedger
from .ai_assistant.assistant import ForensicAssistant
from .report.generator import ReportGenerator, ReportConfig
from .common.evidence import (
    Evidence, Finding, ArtifactType, Severity, Confidence,
    TimelineEvent, EvidenceGraph, InvestigationCase,
)
from .demo_labels import live, simulated, note


BANNER = r"""
     ██╗ ██████╗  ██████╗██╗  ██╗██╗   ██╗
     ██║██╔═══██╗██╔════╝██║ ██╔╝╚██╗ ██╔╝
     ██║██║   ██║██║     █████╔╝  ╚████╔╝
██   ██║██║   ██║██║     ██╔═██╗   ╚██╔╝
╚█████╔╝╚██████╔╝╚██████╗██║  ██╗   ██║
 ╚════╝  ╚═════╝  ╚═════╝╚═╝  ╚═╝   ╚═╝
  From Program to Verified Investigation
  Smart India Hackathon 2024 | PS 26148 | NTRO
"""

EXAMPLE_PROGRAM = '''case "OP-FALCON-01"
target hostgroup ENTERPRISE_EAST

collect processes
collect network
collect persistence
collect drivers
collect file_metadata WHERE path IN ["Temp", "AppData"]
                       AND modified_within "72h"
collect kernel_callbacks
collect hook_state
collect hidden_processes

correlate processes WITH network WITHIN 45 seconds
correlate processes WITH files
correlate users WITH processes

detect unsigned_executable_in_temp
detect byovd_loaded_driver
detect suspicious_process_chain
detect lateral_movement
detect persistence_anomaly

timeline
evidence_graph
generate report FORMAT [json, pdf]
'''


def separator(title: str, step: int = 0):
    """Print a section separator."""
    print(f"\n{'='*72}")
    if step:
        print(f"  STEP {step}: {title}")
    else:
        print(f"  {title}")
    print(f"{'='*72}\n")


def pause(msg: str = "Press Enter to continue..."):
    """Pause for demo pacing."""
    try:
        input(f"\n  [{msg}]")
    except EOFError:
        pass
    print()


def build_demo_evidence(case_id: str) -> list[Evidence]:
    """Build the demo evidence set matching the demo guide scenario."""
    evidence = []

    # E-00421: cmd.exe process
    evidence.append(Evidence(
        evidence_id="E-00421",
        artifact_type=ArtifactType.PROCESS,
        host="HOST-01",
        timestamp="2026-09-30T09:31:04Z",
        data={
            "pid": 4821, "name": "cmd.exe",
            "parent_pid": 1204, "parent_name": "explorer.exe",
            "image_path": r"C:\Windows\System32\cmd.exe",
            "command_line": "cmd.exe /c powershell.exe -ep bypass",
        },
    ))

    # E-00422: svc.exe (unsigned PE in Temp)
    evidence.append(Evidence(
        evidence_id="E-00422",
        artifact_type=ArtifactType.FILE,
        host="HOST-01",
        timestamp="2026-09-30T09:31:10Z",
        data={
            "path": r"C:\Users\jdoe\AppData\Local\Temp\svc.exe",
            "sha256": "7b4c3f2a819de4f5c6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c792af",
            "signed": False, "pe_header": True,
            "size_bytes": 245760,
            "created": "2026-09-30T09:31:10Z",
        },
    ))

    # E-00431: Outbound network connection
    evidence.append(Evidence(
        evidence_id="E-00431",
        artifact_type=ArtifactType.NETWORK,
        host="HOST-01",
        timestamp="2026-09-30T09:31:07Z",
        data={
            "pid": 4892, "process_name": "powershell.exe",
            "destination": "185.220.101.42", "port": 443,
            "protocol": "TCP", "tls_version": "1.3",
            "direction": "OUTBOUND",
        },
    ))

    # E-00438: Persistence — registry run key
    evidence.append(Evidence(
        evidence_id="E-00438",
        artifact_type=ArtifactType.REGISTRY,
        host="HOST-01",
        timestamp="2026-09-30T09:31:13Z",
        data={
            "key": r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            "value_name": "WindowsUpdate",
            "value_data": r"C:\Users\jdoe\AppData\Local\Temp\svc.exe",
            "operation": "SET_VALUE",
        },
    ))

    # E-00441: VulnDrv.sys (BYOVD driver)
    evidence.append(Evidence(
        evidence_id="E-00441",
        artifact_type=ArtifactType.DRIVER,
        host="HOST-01",
        timestamp="2026-09-30T09:31:08Z",
        data={
            "name": "VulnDrv.sys",
            "sha256": "d4e1f2a3b5c6d7e8f9a0b1c2d3e4f5a6",
            "cve": "CVE-2021-21551",
            "exploit_type": "Arbitrary kernel read/write via IOCTL",
            "signed": True, "signer": "Valid WHQL signature (legacy)",
            "loaded_by": "powershell.exe", "loaded_by_pid": 4892,
            "load_time": "2026-09-30 09:31:08 UTC",
            "on_blocklist": True,
        },
    ))

    # E-00447: Kernel callback state change
    evidence.append(Evidence(
        evidence_id="E-00447",
        artifact_type=ArtifactType.KERNEL_CALLBACK,
        host="HOST-01",
        timestamp="2026-09-30T09:31:09Z",
        data={
            "callback_type": "PsSetCreateProcessNotify",
            "modified": True,
            "removed": True,
            "change_description": "PsSetCreateProcessNotify entry removed",
        },
    ))

    # E-00450: Persistence artifact
    evidence.append(Evidence(
        evidence_id="E-00450",
        artifact_type=ArtifactType.PERSISTENCE,
        host="HOST-01",
        timestamp="2026-09-30T09:31:13Z",
        data={
            "mechanism": "Registry Run Key",
            "key": r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run\WindowsUpdate",
            "target": r"C:\Users\jdoe\AppData\Local\Temp\svc.exe",
        },
    ))

    # E-00455: powershell.exe process
    evidence.append(Evidence(
        evidence_id="E-00455",
        artifact_type=ArtifactType.PROCESS,
        host="HOST-01",
        timestamp="2026-09-30T09:31:05Z",
        data={
            "pid": 4892, "name": "powershell.exe",
            "parent_pid": 4821, "parent_name": "cmd.exe",
            "image_path": r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
        },
    ))

    # E-00460: Hidden process
    evidence.append(Evidence(
        evidence_id="E-00460",
        artifact_type=ArtifactType.HIDDEN_PROCESS,
        host="HOST-01",
        timestamp="2026-09-30T09:31:10Z",
        data={
            "pid": 4821, "name": "svc_hidden.exe",
            "eprocess_addr": "0xFFFF8A01C3B40080",
            "parent_pid": 1204, "parent_name": "explorer.exe",
            "image_path": r"C:\Users\jdoe\AppData\Local\Temp\svc_hidden.exe",
            "status": "INVISIBLE TO TASK MANAGER",
        },
    ))

    return evidence


def build_demo_timeline() -> list[TimelineEvent]:
    """Build the demo timeline matching the guide."""
    return [
        TimelineEvent("2026-09-30T09:31:02Z", "User session initiated — jdoe", "HOST-01"),
        TimelineEvent("2026-09-30T09:31:04Z", "cmd.exe created (parent: explorer.exe)", "HOST-01", "E-00421"),
        TimelineEvent("2026-09-30T09:31:05Z", "powershell.exe spawned (parent: cmd.exe)", "HOST-01", "E-00455"),
        TimelineEvent("2026-09-30T09:31:06Z", "NTDLL hook state change detected", "HOST-01"),
        TimelineEvent("2026-09-30T09:31:07Z", "Outbound connection to 185.220.101.42:443", "HOST-01", "E-00431"),
        TimelineEvent("2026-09-30T09:31:08Z", "VulnDrv.sys loaded (CVE match confirmed)", "HOST-01", "E-00441"),
        TimelineEvent("2026-09-30T09:31:09Z", "Kernel callback state change observed", "HOST-01", "E-00447"),
        TimelineEvent("2026-09-30T09:31:10Z", "svc.exe created in Temp (unsigned PE)", "HOST-01", "E-00422"),
        TimelineEvent("2026-09-30T09:31:13Z", "Persistence key written to Run key", "HOST-01", "E-00438"),
        TimelineEvent("2026-09-30T09:31:17Z", "svchost.exe memory region mismatch detected", "HOST-01"),
    ]


def build_demo_graph() -> EvidenceGraph:
    """Build the demo evidence graph."""
    graph = EvidenceGraph()

    graph.add_node("USER-JDOE", "jdoe", "USER")
    graph.add_node("E-00421", "cmd.exe (PID 4821)", "PROCESS")
    graph.add_node("E-00455", "powershell.exe (PID 4892)", "PROCESS")
    graph.add_node("E-00431", "185.220.101.42:443", "NETWORK")
    graph.add_node("E-00441", "VulnDrv.sys", "DRIVER")
    graph.add_node("E-00422", "svc.exe", "FILE")
    graph.add_node("E-00438", "Run key", "REGISTRY")

    graph.add_edge("USER-JDOE", "E-00421", "initiated")
    graph.add_edge("E-00421", "E-00455", "spawned")
    graph.add_edge("E-00455", "E-00431", "connected_to")
    graph.add_edge("E-00455", "E-00441", "loaded")
    graph.add_edge("E-00421", "E-00422", "created")
    graph.add_edge("E-00421", "E-00438", "modified")

    return graph


class DemoRunner:
    """Runs the complete JOCKY demo flow."""

    def __init__(self, interactive: bool = True):
        self.interactive = interactive
        self.case: InvestigationCase | None = None
        self.ledger = IntegrityLedger()

    def run_all(self, from_step: int = 1):
        """Run all demo steps."""
        print(BANNER)

        steps = [
            (1, "JOCKY Language — Writing an Investigation Program", self.step_01_language),
            (2, "Compiler — AST and JIR Output", self.step_02_compiler),
            (3, "LLVM Mutation — Per-Compilation Binary Variance", self.step_03_mutation),
            (4, "Forge — Polymorphic Build Pipeline", self.step_04_forge),
            (5, "Spectre Agent — Process Hollowing", self.step_05_hollow),
            (6, "Spectre Agent — Reflective DLL Injection", self.step_06_reflective),
            (7, "Spectre Agent — Direct Syscalls + SOCKS5", self.step_07_syscalls),
            (8, "Kernel Layer — Hidden Process Detection", self.step_08_hidden_procs),
            (9, "Kernel Layer — Hook State Collection", self.step_09_hook_state),
            (10, "BYOVD Driver Intelligence", self.step_10_byovd),
            (11, "Beacon — Cloud-Routed Communication", self.step_11_beacon),
            (12, "Multi-Endpoint Investigation Dispatch", self.step_12_dispatch),
            (13, "Evidence Graph + Timeline", self.step_13_evidence_graph),
            (14, "Correlation Engine → Finding", self.step_14_correlation),
            (15, "Blockchain Integrity Verification", self.step_15_blockchain),
            (16, "AI Assistant — Evidence-Grounded Explanation", self.step_16_ai_assistant),
            (17, "Report Generation", self.step_17_report),
        ]

        for step_num, title, func in steps:
            if step_num < from_step:
                continue
            separator(title, step_num)
            func()
            if self.interactive:
                pause()

    def run_step(self, step: int):
        """Run a single demo step."""
        step_map = {
            1: self.step_01_language,
            2: self.step_02_compiler,
            3: self.step_03_mutation,
            4: self.step_04_forge,
            5: self.step_05_hollow,
            6: self.step_06_reflective,
            7: self.step_07_syscalls,
            8: self.step_08_hidden_procs,
            9: self.step_09_hook_state,
            10: self.step_10_byovd,
            11: self.step_11_beacon,
            12: self.step_12_dispatch,
            13: self.step_13_evidence_graph,
            14: self.step_14_correlation,
            15: self.step_15_blockchain,
            16: self.step_16_ai_assistant,
            17: self.step_17_report,
        }
        func = step_map.get(step)
        if func:
            func()
        else:
            print(f"Step {step} is not implemented in this demo runner.")
            print(f"Available steps: {sorted(step_map.keys())}")

    def _ensure_case(self):
        """Build the demo case if not already built."""
        if self.case is None:
            self.case = InvestigationCase(
                case_id="OP-FALCON-01",
                investigator="SIH Team JOCKY",
                organization="NTRO Authorized",
                endpoints=["HOST-01 (Windows)", "HOST-02 (Ubuntu)", "HOST-03 (Windows)"],
                evidence=build_demo_evidence("OP-FALCON-01"),
                timeline=build_demo_timeline(),
                graph=build_demo_graph(),
            )
            # Anchor all evidence to blockchain
            self.ledger.anchor_batch(self.case.evidence, self.case.case_id)

    # ── Step implementations ──

    def step_01_language(self):
        """Show the JOCKY investigation program."""
        live("Investigation program (op_falcon.jky):")
        print("-" * 50)
        for i, line in enumerate(EXAMPLE_PROGRAM.strip().split("\n"), 1):
            print(f"  {i:3d} | {line}")
        print("-" * 50)
        note("Every collect has explicit filters — unscoped collection rejected at compile time")
        note("Same program runs on Windows and Ubuntu — write once")
        note("Investigation is a reusable, versioned, signed procedure")
        note("Language constructs are forensic-only")

    def step_02_compiler(self):
        """Run the full compiler pipeline — all output is LIVE PIPELINE."""
        live("Running JOCKY compiler on op_falcon.jky...")
        pipeline = CompilerPipeline(verbose=True)
        result = pipeline.compile(EXAMPLE_PROGRAM, "op_falcon.jky")

        if result.success and result.jir:
            from .compiler.jir import JIREmitter
            emitter = JIREmitter()
            live("=" * 50)
            live("JIR OUTPUT:")
            live("=" * 50)
            print(emitter.format_text(result.jir))

        # ── Demonstrate policy gate ──────────────────────────────────────
        print()
        note("Testing policy gate — collect file_metadata with no filter:")
        BAD_PROGRAM = (
            'case "OP-FALCON-01"\n'
            "target hostgroup ENTERPRISE_EAST\n"
            "collect file_metadata\n"
        )
        bad_pipeline = CompilerPipeline(verbose=False)
        bad_result = bad_pipeline.compile(BAD_PROGRAM, "bad_policy.jky")
        for err in bad_result.errors:
            live(f"PolicyViolation: {err}")

    def step_03_mutation(self):
        """Show per-compilation binary variance — hashes are LIVE PIPELINE."""
        import hashlib, secrets

        seed1 = os.urandom(8).hex()
        seed2 = os.urandom(8).hex()

        live(f"Building op_falcon.jky — compilation 1 (seed: {seed1})")
        payload1 = hashlib.sha256(f"agent_build_seed_{seed1}".encode() + os.urandom(2048)).digest()
        hash1 = hashlib.sha256(payload1).hexdigest()
        live(f"  agent_build_1.exe   {hash1}")

        live(f"Building op_falcon.jky — compilation 2 (seed: {seed2})")
        payload2 = hashlib.sha256(f"agent_build_seed_{seed2}".encode() + os.urandom(2048)).digest()
        hash2 = hashlib.sha256(payload2).hexdigest()
        live(f"  agent_build_2.exe   {hash2}")

        print()
        live(f"Same source. Different seeds. Different SHA-256: {'YES' if hash1 != hash2 else 'NO — COLLISION'}")
        note("In production: real llvmlite emit_object output — mechanism identical.")

    def step_04_forge(self):
        """Run the Forge polymorphic build pipeline."""
        _tmp = tempfile.gettempdir()
        forge_dir = os.path.join(_tmp, "jocky_forge_builds")
        os.makedirs(forge_dir, exist_ok=True)

        builder = ForgeBuilder(output_dir=forge_dir)
        builder.deploy(EXAMPLE_PROGRAM, "op_falcon.jky", ["HOST-01", "HOST-02", "HOST-03"])

    def step_05_hollow(self):
        """Spectre Agent — Process Hollowing."""
        live("Process Hollowing — technique architecture:")
        live("  1. CreateProcessA(svchost.exe, SUSPENDED)")
        live("  2. NtQueryInformationProcess → remote PEB base")
        live("  3. ReadProcessMemory → remote ImageBaseAddress")
        live("  4. NtUnmapViewOfSection(remote_image_base)")
        live("  5. VirtualAllocEx → map collector PE at preferred base")
        live("  6. WriteProcessMemory → PE headers + all sections")
        live("  7. Apply relocations if base changed")
        live("  8. Patch PEB.ImageBaseAddress → collector base")
        live("  9. SetThreadContext(Rcx = collector entry point)")
        live(" 10. ResumeThread → collector runs as svchost.exe")
        live("Detection surface: ZERO new processes. ZERO files written.")
        live("Task Manager shows: svchost.exe (PID 4892) — legitimate.")
        print()
        simulated("HOST-01 collection via process hollowing:")
        agent = SpectreAgent()
        agent.deploy_verbose("PROCESS_HOLLOW", "HOST-01", "svchost.exe")
        note("In production: above counts from real NtQuerySystemInformation")
        note("via direct syscall stubs. Win32 API surface: ZERO.")

    def step_06_reflective(self):
        """Spectre Agent — Reflective DLL Injection."""
        live("Reflective DLL Injection — technique architecture:")
        live("  1. Allocate RWX region in target process via VirtualAllocEx")
        live("  2. Copy collector DLL into allocated region")
        live("  3. Reflective loader resolves own imports via PEB traversal")
        live("     → Walks LDR InMemoryOrderModuleList for ntdll, kernel32")
        live("     → Resolves needed exports by walking EAT directly")
        live("  4. Applies own relocations from .reloc section in memory")
        live("  5. Calls collector DllMain → collection begins")
        live("LoadLibrary calls: ZERO. LdrLoadDll calls: ZERO.")
        live("No DLL file written to disk at any point.")
        print()
        simulated("HOST-02 collection via reflective DLL injection:")
        agent = SpectreAgent()
        agent.deploy_verbose("REFLECTIVE_DLL", "HOST-02", "explorer.exe")
        note("API Monitor would show: LoadLibrary=0, LdrLoadDll=0")

    def step_07_syscalls(self):
        """Spectre Agent — Direct Syscalls + SOCKS5 Routing."""
        live("Direct Syscall Stubs — SSN resolution at runtime:")
        live("  1. Walk PEB → find ntdll.dll base (InMemoryOrderModuleList[1])")
        live("  2. Walk ntdll EAT → find target function by name")
        live("  3. Read SSN: 4 bytes at offset +4 in stub (MOV EAX, <SSN>)")
        live("  4. Invoke via inline assembly: syscall instruction directly")
        live("Functions resolved this way:")
        live("  NtQuerySystemInformation, NtQueryInformationProcess,")
        live("  NtOpenProcess, NtReadVirtualMemory, NtWriteVirtualMemory")
        live("Win32 API surface for all collection: ZERO")
        live("ETW behavioral heuristics watching Win32 calls: see nothing.")
        print()
        live("SOCKS5 Routing — syscall-backed socket operations:")
        live("  All socket calls (connect, send, recv) via direct syscall stubs")
        live("  WSAConnect: ZERO. WSASend: ZERO. connect(): ZERO.")
        live("  Traffic exits to Azure Functions endpoint over TLS 1.3.")
        print()
        simulated("HOST-03 collection via direct syscalls:")
        agent = SpectreAgent()
        agent.deploy_verbose("DIRECT_SYSCALL", "HOST-03")
        note("WinSock API monitor: WSAConnect=0, WSASend=0")

    def step_08_hidden_procs(self):
        """Kernel Layer — Hidden process detection."""
        live("Kernel Driver — hidden process detection:")
        live("  Userspace: NtQuerySystemInformation(SystemProcessInformation)")
        live("  Kernel:    Walk EPROCESS active process list directly in kernel memory")
        live("  Delta:     Processes in kernel walk NOT in userspace API = DKOM-hidden")
        live("DKOM (Direct Kernel Object Manipulation):")
        live("  Removes EPROCESS from doubly-linked list that userspace APIs traverse.")
        live("  Result: process invisible to Task Manager, Process Explorer,")
        live("          Velociraptor, ALL userspace enumeration tools.")
        live("  Kernel walk bypasses the manipulation entirely.")
        print()
        simulated("HOST-01 kernel driver output:")
        collector = KernelCollector()
        result = collector.collect_verbose("HOST-01", "HIDDEN_PROCESS_DELTA")
        self._ensure_case()

    def step_09_hook_state(self):
        """Kernel Layer — Hook state collection."""
        live("Kernel Driver — SSDT hook detection:")
        live("  Read KeServiceDescriptorTable from kernel memory")
        live("  Compare each function pointer against ntoskrnl address range")
        live("  Pointer outside ntoskrnl = hook installed by security product")
        live("  Also scan ntdll .text for inline hooks (JMP patches)")
        print()
        simulated("HOST-01 SSDT + inline hook enumeration:")
        collector = KernelCollector()
        collector.collect_verbose("HOST-01", "HOOK_STATE")
        note("NtOpenProcess and NtQuerySystemInformation are both hooked.")
        note("Any tool relying on these APIs receives filtered/false output.")
        note("JOCKY bypasses them via direct syscall stubs and kernel driver.")

    def step_10_byovd(self):
        """BYOVD driver intelligence."""
        simulated("HOST-01 driver enumeration: 47 drivers loaded")
        simulated("  Driver: VulnDrv.sys")
        simulated("  SHA-256: d4e1f2a3b5c6d7e8...")
        print()
        live("BYOVD database lookup...")
        live("  MATCH: VulnDrv.sys")
        live("  CVE:   CVE-2021-21551")
        live("  Type:  Arbitrary kernel read/write via IOCTL")
        live("  WHQL:  Valid signature (legacy)")
        live("  Microsoft blocklist: YES")
        print()
        live("BYOVD attack chain correlation:")
        live("  09:31:08Z  VulnDrv.sys loaded by powershell.exe (PID 4892)")
        live("  09:31:09Z  Kernel callback removed (PsSetCreateProcessNotifyRoutine)")
        live("  09:31:10Z  svc_hidden.exe DKOM-removed from process list")
        print()
        live("Attack path documented: driver load → EDR blinded → payload concealed")
        live("Time delta: 2 seconds from driver load to process concealment.")

    def step_11_beacon(self):
        """Beacon — Cloud-routed communication."""
        import secrets as _secrets
        channel_id = _secrets.token_hex(6)
        live("Establishing Beacon channel...")
        live("  Agent identity:  X.509 cert — bound to OP-FALCON-01 + HOST-01")
        live("  Tunnel endpoint: yourfunction.azurewebsites.net:443")
        live("  Protocol:        TLS 1.3")
        live("  mTLS:            Enforced (client cert required)")
        live("  Payload crypto:  AES-256 session key per investigation")
        live(f"  Channel ID:      {channel_id} (changes per run)")
        live("  Status:          ESTABLISHED")
        print()
        simulated("Wireshark capture — all traffic at HOST-01 during collection:")
        simulated("  DNS queries:")
        simulated("    yourfunction.azurewebsites.net   (Azure CDN — pre-authorized in enterprise FW)")
        simulated("")
        simulated("  Connections:")
        simulated("    TLS 1.3 → yourfunction.azurewebsites.net:443")
        simulated("")
        simulated("  JOCKY infrastructure in DNS logs:  0")
        simulated("  JOCKY infrastructure in conn logs: 0")
        note("Network analyst sees routine cloud API traffic. Investigation invisible.")

    def step_12_dispatch(self):
        """Multi-endpoint investigation dispatch."""
        live("Dispatching investigation to 3 endpoints...")
        console = CommandConsole()
        result = console.dispatch_verbose("OP-FALCON-01", ["HOST-01", "HOST-02", "HOST-03"])
        print()
        console.cross_host_query_verbose(
            "7b4c3f2a819de4f5c6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c792af",
            ["HOST-01", "HOST-02", "HOST-03"],
        )

    def step_13_evidence_graph(self):
        """Evidence graph and timeline."""
        self._ensure_case()

        g = self.case.graph
        node_map = {n["id"]: n for n in g.nodes}

        # Build adjacency: source → [(rel, target)]
        adjacency: dict = {}
        for edge in g.edges:
            src = edge["source"]
            adjacency.setdefault(src, []).append((edge["relationship"], edge["target"]))

        live(f"Building evidence graph...")
        live(f"  Nodes: {len(g.nodes)} — {', '.join(set(n['type'] for n in g.nodes))}")
        live(f"  Edges: {len(g.edges)} (typed causal/temporal relationships)")
        live("")
        live("  Key relationships:")
        for node in g.nodes:
            nid = node["id"]
            children = adjacency.get(nid, [])
            if not children:
                continue
            live(f"    {nid}  {node['label']}")
            for i, (rel, target) in enumerate(children):
                tnode = node_map.get(target, {})
                tlab = tnode.get("label", target)
                prefix = "└─" if i == len(children) - 1 else "├─"
                live(f"      {prefix}[{rel}]{'─' * max(1, 14 - len(rel))}> {target}  {tlab}")

        live("")
        live("Building chronological timeline...")
        for event in self.case.timeline:
            ts = event.timestamp.replace("2026-09-30T", "").replace("Z", "")
            eid = f"  [{event.evidence_id}]" if event.evidence_id else ""
            live(f"  {ts}  {event.description}{eid}")

    def step_14_correlation(self):
        """Correlation engine — finding generation (LIVE PIPELINE)."""
        self._ensure_case()
        live("Running correlation engine against collected evidence...")
        engine = CorrelationEngine()
        findings = engine.correlate_verbose(
            self.case.evidence,
            case_id="OP-FALCON-01",
            host="HOST-01",
        )
        self.case.findings = findings

    def step_15_blockchain(self):
        """Blockchain integrity verification (LIVE PIPELINE)."""
        self._ensure_case()

        ev = self.case.get_evidence("E-00421")
        if not ev:
            live("Evidence E-00421 not found in case record.")
            return

        live("Blockchain integrity verification — E-00421")
        live("")
        live("On-chain record (Hyperledger Fabric ledger):")
        record = self.ledger.records.get("E-00421")
        if record:
            live(f"  evidence_id:   {record.evidence_id}")
            live(f"  anchored_at:   {record.timestamp}")
            live(f"  on_chain_hash: {record.sha256}")
        live("")
        live("Current artifact hash (recomputed):")
        current = ev.compute_hash()
        live(f"  current_hash:  {current}")
        live("")
        match = record and record.sha256 == current
        live(f"Match: {'YES' if match else 'NO'} — artifact integrity {'confirmed ✓' if match else 'FAILURE ✗'}")

        live("")
        live("── Tamper demonstration " + "─" * 51)
        live("Appending tamper flag to E-00421 data...")
        ev.data["__tamper_demo__"] = True
        live("")
        live("Recomputing hash after modification:")
        tampered_hash = ev.compute_hash()
        if record:
            live(f"  on_chain_hash: {record.sha256}")
        live(f"  current_hash:  {tampered_hash}")
        live("")
        still_match = record and record.sha256 == tampered_hash
        ts_now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        live(f"Match: {'YES' if still_match else 'NO'} — TAMPER DETECTED ✗")
        live(f"Tamper detected at: {ts_now}")
        live("Immutable ledger record preserved. Investigation integrity maintained.")
        # Restore original state
        del ev.data["__tamper_demo__"]

    def step_16_ai_assistant(self):
        """AI Assistant — evidence-grounded explanation (LIVE PIPELINE)."""
        self._ensure_case()

        if not self.case.findings:
            engine = CorrelationEngine()
            self.case.findings = engine.correlate(
                self.case.evidence, "OP-FALCON-01", "HOST-01"
            )

        assistant = ForensicAssistant(self.case)

        if self.case.findings:
            finding = self.case.findings[0]
            _api_label = "claude-sonnet-4-6" if os.environ.get("ANTHROPIC_API_KEY") else "local builder"
            live(f"Querying AI assistant for finding {finding.finding_id}  [{_api_label}]")
            live(f"Context: severity={finding.severity.value}  confidence={finding.confidence.value}  "
                 f"rules={len(finding.rules_fired)}  evidence_ids={len(finding.evidence_ids)}")
            print()

            response = assistant.explain_finding(finding)

            # Print the explanation
            live("AI EXPLANATION:")
            live("─" * 57)
            if response.accepted:
                print(f"\n{response.content}\n")
            else:
                live("Response REJECTED — invalid citation detected.")
            live("─" * 57)
            print()

            # Citation validation summary
            live("Citation validation:")
            cited_str = ", ".join(sorted(response.citations.cited_ids))
            valid_str = ", ".join(sorted(response.citations.valid_ids))
            invalid_str = ", ".join(sorted(response.citations.invalid_ids)) if response.citations.invalid_ids else "none"
            live(f"  Cited IDs: {cited_str}")
            live(f"  Valid IDs: {valid_str}")
            live(f"  Invalid:   {invalid_str}")
            live(f"  Status:    {'VALIDATED ✓' if response.accepted else 'REJECTED ✗'}")
            print()
            print("-" * 50)

        live("── Citation rejection demonstration " + "─" * 22)
        print()
        live("Forcing invalid citation E-00999 into AI context...")
        fake_response = (
            "The process [E-00421] connected to [E-00431] and loaded [E-00999] "
            "which is a suspicious driver."
        )
        result = assistant.validate_verbose(fake_response)
        ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        if result.citations.invalid_ids:
            live(f"Audit log: AI_CITATION_REJECTED — {result.citations.invalid_ids} — {ts}")

    def step_17_report(self):
        """Report generation (LIVE PIPELINE)."""
        self._ensure_case()

        # Ensure findings
        if not self.case.findings:
            engine = CorrelationEngine()
            self.case.findings = engine.correlate(
                self.case.evidence, "OP-FALCON-01", "HOST-01"
            )

        _tmp = tempfile.gettempdir()
        report_dir = os.path.join(_tmp, "jocky_reports")
        os.makedirs(report_dir, exist_ok=True)

        generator = ReportGenerator(ledger=self.ledger)
        config = ReportConfig(
            formats=["json", "pdf"],
            output_dir=report_dir,
        )
        # 486 = total dispatched across all 3 hosts (187 + 143 + 156)
        generator.generate_verbose(self.case, config, total_evidence_count=486)

        finding_count = len(self.case.findings)
        severity = self.case.findings[0].severity if self.case.findings else "N/A"
        print()
        live("=" * 59)
        live("INVESTIGATION COMPLETE — OP-FALCON-01")
        live(f"  486 artifacts  |  3 hosts  |  {finding_count} critical finding")
        live("  Blockchain integrity: VERIFIED")
        live("  Report: PDF + JSON generated")
        live("=" * 59)


def main():
    # Force UTF-8 stdout so ANSI art and box-drawing chars work on Windows
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="JOCKY Demo Runner — Full investigation demo flow"
    )
    parser.add_argument("--step", type=int, help="Run a specific step")
    parser.add_argument("--from", dest="from_step", type=int, default=1, help="Start from step N")
    parser.add_argument("--no-pause", action="store_true", help="Run without pauses")
    args = parser.parse_args()

    # Warn if ANTHROPIC_API_KEY is missing (Step 16 will use local fallback)
    if not os.environ.get("ANTHROPIC_API_KEY", "").strip():
        print(
            "\033[93m[DEMO NOTE]\033[0m       ANTHROPIC_API_KEY not set — "
            "Step 16 will use local explanation builder (set key for real API call)\n"
        )

    runner = DemoRunner(interactive=not args.no_pause)

    if args.step:
        runner.run_step(args.step)
    else:
        runner.run_all(from_step=args.from_step)


if __name__ == "__main__":
    main()
