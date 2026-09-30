"""JOCKY Policy Validator — Enforces authorization before build."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime, timezone

from ..jir.emitter import JIRProgram


@dataclass
class InvestigatorCert:
    """Represents an investigator's authorization certificate."""
    cert_id: str
    investigator_name: str
    organization: str
    authorized_hostgroups: List[str] = field(default_factory=list)
    authorized_hosts: List[str] = field(default_factory=list)
    kernel_ops_authorized: bool = False
    case_expiry: Optional[datetime] = None

    @classmethod
    def demo_cert(cls) -> "InvestigatorCert":
        """Generate a demo certificate for presentation."""
        return cls(
            cert_id="CERT-DEMO-2024-001",
            investigator_name="SIH Team JOCKY",
            organization="NTRO Authorized",
            authorized_hostgroups=["ENTERPRISE_EAST", "ENTERPRISE_WEST", "DMZ"],
            authorized_hosts=["HOST-01", "HOST-02", "HOST-03"],
            kernel_ops_authorized=True,
            case_expiry=datetime(2026, 12, 31, tzinfo=timezone.utc),
        )


@dataclass
class PolicyResult:
    """Result of policy validation."""
    passed: bool
    checks: List[Dict[str, str]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class PolicyValidator:
    """Validates JIR against investigator authorization and policy rules.

    Checks:
    1. Investigator certificate is valid
    2. Target host/hostgroup is authorized
    3. All collection operations have filters (no blanket collection)
    4. Kernel operations require explicit authorization
    5. Case has not expired
    """

    def __init__(self, cert: Optional[InvestigatorCert] = None):
        self.cert = cert or InvestigatorCert.demo_cert()

    def validate(self, jir: JIRProgram) -> PolicyResult:
        """Run all policy checks against the JIR program."""
        result = PolicyResult(passed=True)

        # Check 1: Investigator cert validity
        self._check_cert(result)

        # Check 2: Host scope authorization
        self._check_host_scope(jir, result)

        # Check 3: Collection filters present
        self._check_collection_filters(jir, result)

        # Check 4: Kernel ops authorization
        self._check_kernel_ops(jir, result)

        # Check 5: Case expiry
        self._check_expiry(result)

        result.passed = len(result.errors) == 0
        return result

    def validate_verbose(self, jir: JIRProgram) -> PolicyResult:
        """Validate with [POLICY] status output for demo."""
        print("[POLICY]   Capability validation...", end="")
        result = self.validate(jir)

        if result.passed:
            print("             OK")
        else:
            print("             FAILED")

        for check in result.checks:
            status = check["status"]
            label = check["label"]
            detail = check.get("detail", "")
            symbol = "→"
            detail_str = f" — {detail}" if detail else ""
            print(f"           {symbol} {label}: {status}{detail_str}")

        if not result.passed:
            for err in result.errors:
                print(f"           ✗ BLOCKED: {err}")
            print("[POLICY]   Validation FAILED. Build aborted.")
        else:
            print("[POLICY]   Validation passed. Proceeding to build.")

        return result

    def _check_cert(self, result: PolicyResult):
        if self.cert and self.cert.cert_id:
            result.checks.append({
                "label": "Investigator cert",
                "status": "VALID",
                "detail": self.cert.cert_id,
            })
        else:
            result.errors.append("No valid investigator certificate")
            result.checks.append({
                "label": "Investigator cert",
                "status": "MISSING",
            })

    def _check_host_scope(self, jir: JIRProgram, result: PolicyResult):
        target = jir.target_name
        if jir.target_type == "HOSTGROUP":
            authorized = target in self.cert.authorized_hostgroups
        else:
            authorized = target in self.cert.authorized_hosts

        if authorized:
            result.checks.append({
                "label": "Host scope",
                "status": "AUTHORIZED",
                "detail": f"{jir.target_type} {target}",
            })
        else:
            result.errors.append(f"Target {target} not authorized for this investigator")
            result.checks.append({
                "label": "Host scope",
                "status": "UNAUTHORIZED",
                "detail": target,
            })

    def _check_collection_filters(self, jir: JIRProgram, result: PolicyResult):
        all_have_filters = True
        for op in jir.collect_ops:
            if op.requires_filter and not op.has_filter:
                all_have_filters = False
                result.errors.append(
                    f"MISSING_FILTER: collect {op.artifact_type} has no explicit "
                    f"WHERE clause — unscoped collection rejected"
                )

        status = "ALL PRESENT" if all_have_filters else "MISSING"
        result.checks.append({
            "label": "Collection filters",
            "status": status,
        })

    def _check_kernel_ops(self, jir: JIRProgram, result: PolicyResult):
        kernel_types = {"KERNEL_CALLBACKS", "HOOK_STATE", "HIDDEN_PROCESSES"}
        has_kernel = any(op.artifact_type in kernel_types for op in jir.collect_ops)

        if has_kernel:
            if self.cert.kernel_ops_authorized:
                result.checks.append({
                    "label": "Kernel ops",
                    "status": "AUTHORIZED",
                })
            else:
                result.errors.append("Kernel operations not authorized for this certificate")
                result.checks.append({
                    "label": "Kernel ops",
                    "status": "UNAUTHORIZED",
                })

    def _check_expiry(self, result: PolicyResult):
        if self.cert.case_expiry:
            now = datetime.now(timezone.utc)
            if now < self.cert.case_expiry:
                expiry_str = self.cert.case_expiry.strftime("%Y-%m-%d")
                result.checks.append({
                    "label": "Case expiry",
                    "status": f"{expiry_str} — VALID",
                })
            else:
                result.errors.append("Investigation case has expired")
                result.checks.append({
                    "label": "Case expiry",
                    "status": "EXPIRED",
                })
