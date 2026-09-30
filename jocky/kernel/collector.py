"""JOCKY Kernel Layer — Forensic kernel-level evidence collection.

This module provides detection capabilities for:
- Hidden process detection (EPROCESS walk vs API delta)
- Hook state enumeration (SSDT, inline, IRP)
- BYOVD driver intelligence (CVE-matched vulnerable driver detection)

NOTE: This is a simulation for demonstration. Production implementation
requires a signed kernel driver for real EPROCESS traversal and SSDT reads.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from ..common.evidence import Evidence, ArtifactType


# ── Known vulnerable driver database (subset for demo) ──

VULN_DRIVER_DB = {
    "VulnDrv.sys": {
        "cve": "CVE-2021-21551",
        "description": "Dell dbutil_2_3.sys — arbitrary kernel read/write via IOCTL",
        "exploit_type": "Arbitrary kernel read/write via IOCTL",
        "blocklist": True,
    },
    "dbutil_2_3.sys": {
        "cve": "CVE-2021-21551",
        "description": "Dell dbutil driver",
        "exploit_type": "Arbitrary kernel read/write via IOCTL",
        "blocklist": True,
    },
    "RTCore64.sys": {
        "cve": "CVE-2019-16098",
        "description": "MSI Afterburner RTCore64 — arbitrary read/write",
        "exploit_type": "Arbitrary physical memory read/write",
        "blocklist": True,
    },
    "gdrv.sys": {
        "cve": "CVE-2018-19320",
        "description": "GIGABYTE driver — arbitrary read/write",
        "exploit_type": "Arbitrary physical memory read/write",
        "blocklist": True,
    },
}


@dataclass
class KernelProcessInfo:
    """Process information from kernel-level enumeration."""
    pid: int
    name: str
    eprocess_addr: str
    parent_pid: int
    parent_name: str
    image_path: str
    visible_to_api: bool = True


@dataclass
class HookInfo:
    """Information about a detected hook."""
    hook_type: str  # SSDT, INLINE, IRP
    function_name: str
    expected_module: str
    expected_offset: str
    found_module: str
    found_offset: str
    replacement_type: str


@dataclass
class DriverInfo:
    """Information about a loaded driver."""
    name: str
    sha256: str
    signed: bool
    signer: str
    load_time: str
    loaded_by: str
    loaded_by_pid: int
    cve: Optional[str] = None
    exploit_type: Optional[str] = None
    on_blocklist: bool = False


@dataclass
class KernelCollectionResult:
    """Result of a kernel-level collection operation."""
    operation: str
    host: str
    success: bool
    evidence: List[Evidence] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)


class KernelCollector:
    """Performs kernel-level forensic evidence collection.

    Operations:
    - HIDDEN_PROCESS_DELTA: Compare EPROCESS walk vs API enumeration
    - HOOK_STATE: Enumerate SSDT, inline, and IRP hooks
    - DRIVER_INTELLIGENCE: Enumerate drivers and match against CVE database
    """

    def collect(self, host: str, operation: str, sim_data: Optional[Dict] = None) -> KernelCollectionResult:
        """Run a kernel collection operation."""
        sim = sim_data or {}

        if operation == "HIDDEN_PROCESS_DELTA":
            return self._collect_hidden_processes(host, sim)
        elif operation == "HOOK_STATE":
            return self._collect_hook_state(host, sim)
        elif operation == "DRIVER_INTELLIGENCE":
            return self._collect_driver_intel(host, sim)
        else:
            return KernelCollectionResult(
                operation=operation, host=host, success=False,
                data={"error": f"Unknown operation: {operation}"},
            )

    def collect_verbose(self, host: str, operation: str, sim_data: Optional[Dict] = None) -> KernelCollectionResult:
        """Collect with demo-formatted console output."""
        result = self.collect(host, operation, sim_data)

        if operation == "HIDDEN_PROCESS_DELTA":
            self._print_hidden_process_result(result)
        elif operation == "HOOK_STATE":
            self._print_hook_state_result(result)
        elif operation == "DRIVER_INTELLIGENCE":
            self._print_driver_intel_result(result)

        return result

    # ── Hidden process detection ──

    def _collect_hidden_processes(self, host: str, sim: Dict) -> KernelCollectionResult:
        """Detect DKOM-hidden processes via EPROCESS walk vs API delta.

        Simulation: uses provided process lists. Production: kernel driver
        traverses the EPROCESS doubly-linked list and compares with
        NtQuerySystemInformation results.
        """
        kernel_count = sim.get("kernel_process_count", 94)
        api_count = sim.get("api_process_count", 93)
        hidden = sim.get("hidden_processes", [
            {
                "pid": 4821,
                "name": "svc_hidden.exe",
                "eprocess": "0xFFFF8A01C3B40080",
                "parent_pid": 1204,
                "parent_name": "explorer.exe",
                "image_path": r"C:\Users\jdoe\AppData\Local\Temp\svc_hidden.exe",
            }
        ])

        evidence_list = []
        for proc in hidden:
            ev = Evidence(
                artifact_type=ArtifactType.HIDDEN_PROCESS,
                host=host,
                data={
                    "pid": proc["pid"],
                    "name": proc["name"],
                    "eprocess_addr": proc["eprocess"],
                    "parent_pid": proc["parent_pid"],
                    "parent_name": proc["parent_name"],
                    "image_path": proc["image_path"],
                    "status": "INVISIBLE TO TASK MANAGER AND NtQuerySystemInformation",
                    "detection_method": "EPROCESS_WALK_VS_API_DELTA",
                },
            )
            evidence_list.append(ev)

        return KernelCollectionResult(
            operation="HIDDEN_PROCESS_DELTA",
            host=host,
            success=True,
            evidence=evidence_list,
            data={
                "kernel_process_count": kernel_count,
                "api_process_count": api_count,
                "delta": kernel_count - api_count,
                "hidden_processes": hidden,
            },
        )

    # ── Hook state enumeration ──

    def _collect_hook_state(self, host: str, sim: Dict) -> KernelCollectionResult:
        """Enumerate SSDT, inline, and IRP hooks."""
        ssdt_hooks = sim.get("ssdt_hooks", [
            {
                "index": "0x0F",
                "function": "NtOpenProcess",
                "expected_module": "ntoskrnl.exe",
                "expected_offset": "0x4A2C10",
                "found_module": "SecurityProduct.sys",
                "found_offset": "0x1B440",
                "type": "FUNCTION POINTER REPLACEMENT",
            },
            {
                "index": "0x23",
                "function": "NtQuerySystemInformation",
                "expected_module": "ntoskrnl.exe",
                "expected_offset": "0x3F1800",
                "found_module": "SecurityProduct.sys",
                "found_offset": "0x1C120",
                "type": "FUNCTION POINTER REPLACEMENT",
            },
        ])

        inline_hooks = sim.get("inline_hooks", [
            {"function": "ntdll.dll!NtOpenProcess", "target": "SecurityProduct.sys"},
            {"function": "ntdll.dll!NtWriteVirtualMemory", "target": "SecurityProduct.sys"},
            {"function": "ntdll.dll!NtQuerySystemInformation", "target": "SecurityProduct.sys"},
        ])

        irp_hooks = sim.get("irp_hooks", [])

        evidence_list = []
        for hook in ssdt_hooks + inline_hooks:
            ev = Evidence(
                artifact_type=ArtifactType.HOOK_STATE,
                host=host,
                data=hook,
            )
            evidence_list.append(ev)

        return KernelCollectionResult(
            operation="HOOK_STATE",
            host=host,
            success=True,
            evidence=evidence_list,
            data={
                "ssdt_hook_count": len(ssdt_hooks),
                "inline_hook_count": len(inline_hooks),
                "irp_hook_count": len(irp_hooks),
                "ssdt_hooks": ssdt_hooks,
                "inline_hooks": inline_hooks,
                "irp_hooks": irp_hooks,
            },
        )

    # ── BYOVD driver intelligence ──

    def _collect_driver_intel(self, host: str, sim: Dict) -> KernelCollectionResult:
        """Enumerate loaded drivers and match against CVE database."""
        total_drivers = sim.get("total_drivers", 47)
        loaded_drivers = sim.get("drivers", [
            {
                "name": "VulnDrv.sys",
                "sha256": "d4e1f2a3b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2",
                "signed": True,
                "signer": "Valid WHQL signature (legacy)",
                "load_time": "2026-09-30 09:31:08 UTC",
                "loaded_by": "powershell.exe",
                "loaded_by_pid": 4892,
            }
        ])

        evidence_list = []
        byovd_indicators = []

        for drv in loaded_drivers:
            drv_name = drv["name"]
            vuln_info = VULN_DRIVER_DB.get(drv_name)

            drv_data = dict(drv)
            if vuln_info:
                drv_data["cve"] = vuln_info["cve"]
                drv_data["exploit_type"] = vuln_info["exploit_type"]
                drv_data["on_blocklist"] = vuln_info["blocklist"]
                byovd_indicators.append(drv_data)

            ev = Evidence(
                artifact_type=ArtifactType.DRIVER,
                host=host,
                data=drv_data,
            )
            evidence_list.append(ev)

        return KernelCollectionResult(
            operation="DRIVER_INTELLIGENCE",
            host=host,
            success=True,
            evidence=evidence_list,
            data={
                "total_drivers": total_drivers,
                "byovd_indicators": byovd_indicators,
                "byovd_count": len(byovd_indicators),
            },
        )

    # ── Demo output formatting ──

    def _print_hidden_process_result(self, result: KernelCollectionResult):
        d = result.data
        print(f"[KERNEL] EPROCESS walk: {d['kernel_process_count']} processes found")
        print(f"[KERNEL] API enumeration: {d['api_process_count']} processes found")
        print(f"[KERNEL] Delta: {d['delta']} process hidden from API")

        for proc in d["hidden_processes"]:
            print(f"\nHIDDEN PROCESS DETECTED:")
            print(f"  PID:          {proc['pid']}")
            print(f"  Name:         {proc['name']}")
            print(f"  EPROCESS:     {proc['eprocess']}")
            print(f"  Parent PID:   {proc['parent_pid']} ({proc['parent_name']})")
            print(f"  Image path:   {proc['image_path']}")
            print(f"  Status:       INVISIBLE TO TASK MANAGER AND NtQuerySystemInformation")

    def _print_hook_state_result(self, result: KernelCollectionResult):
        d = result.data
        print(f"[KERNEL] SSDT baseline comparison complete")
        print(f"\nHOOK STATE REPORT — {result.host}:")
        print(f"  SSDT hooks detected:         {d['ssdt_hook_count']}")
        print(f"  Inline hooks detected:       {d['inline_hook_count']}")
        print(f"  IRP hooks detected:          {d['irp_hook_count']}")

        if d["ssdt_hooks"]:
            print(f"\nSSDT HOOKS:")
            for hook in d["ssdt_hooks"]:
                print(f"  Index {hook['index']} ({hook['function']})")
                print(f"    Expected:  {hook['expected_module']} + {hook['expected_offset']}")
                print(f"    Found:     {hook['found_module']} + {hook['found_offset']}")
                print(f"    Type:      {hook['type']}")

        if d["inline_hooks"]:
            print(f"\nINLINE HOOKS:")
            for hook in d["inline_hooks"]:
                print(f"  {hook['function']}     → JMP to {hook['target']}")

    def _print_driver_intel_result(self, result: KernelCollectionResult):
        d = result.data
        print(f"[KERNEL] Driver enumeration complete: {d['total_drivers']} drivers loaded")

        for drv in d["byovd_indicators"]:
            print(f"\nBYOVD INDICATOR DETECTED:")
            print(f"  Driver:         {drv['name']}")
            print(f"  SHA-256:        {drv['sha256'][:16]}...")
            print(f"  CVE:            {drv['cve']}")
            print(f"  Exploit Type:   {drv['exploit_type']}")
            print(f"  Signing:        {drv['signer']}")
            print(f"  Load Time:      {drv['load_time']}")
            print(f"  Loaded By:      {drv['loaded_by']} (PID {drv['loaded_by_pid']})")
            print(f"  Blocklist:      {'Present on Microsoft vulnerable driver blocklist' if drv.get('on_blocklist') else 'Not on blocklist'}")
            print(f"\nFORENSIC ACTION: CRITICAL finding raised.")
