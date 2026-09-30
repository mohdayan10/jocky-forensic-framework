"""JOCKY Forge Builder — Generates per-host polymorphic builds."""

from __future__ import annotations

import hashlib
import secrets
import json
import os
from dataclasses import dataclass, field
from typing import List, Dict

from ..compiler.pipeline import CompilerPipeline
from ..blockchain.ledger import IntegrityLedger
from ..common.evidence import Evidence, ArtifactType
from ..demo_labels import live


@dataclass
class ForgeBuild:
    """A single polymorphic build for one target host."""
    host: str
    sha256: str
    entry_point: str
    import_hash: str
    build_id: str
    case_id: str
    mutation_seed: str
    output_path: str


class ForgeBuilder:
    """Generates structurally distinct builds for each target host.

    Each build gets:
    - Unique mutation seed → different binary content
    - Different SHA-256 hash
    - Different simulated entry point
    - Different import hash
    - Unique build certificate bound to case + host
    """

    def __init__(self, output_dir: str = "./forge_builds"):
        self.output_dir = output_dir
        self.ledger = IntegrityLedger()

    def deploy(self, source: str, filename: str, targets: List[str]) -> List[ForgeBuild]:
        """Compile once, then generate per-host polymorphic builds."""
        # Compile the source
        pipeline = CompilerPipeline(verbose=True)
        result = pipeline.compile(source, filename)

        if not result.success:
            print(f"\n[FORGE] Compilation failed. Cannot proceed with deployment.")
            return []

        os.makedirs(self.output_dir, exist_ok=True)

        builds = []
        hosts_str = "  ".join(targets)
        live(f"Dispatching Forge build → {hosts_str}")
        live("")

        for host in targets:
            build = self._generate_build(result.jir_json, host, result.jir.case_id)
            builds.append(build)
            self._print_build(build)

        # Verify no hash collisions
        hashes = [b.sha256 for b in builds]
        if len(hashes) == len(set(hashes)):
            live(f"All {len(builds)} builds unique — zero shared hash surface ✓")
            live("Deployment certs embedded. Blockchain anchored.")
        else:
            live("WARNING: Hash collision detected — mutation entropy insufficient.")

        return builds

    def _generate_build(self, jir_json: str, host: str, case_id: str) -> ForgeBuild:
        """Generate a single polymorphic build for one host."""
        # Unique mutation seed per host
        mutation_seed = secrets.token_hex(8)
        build_id = f"FORGE-BUILD-{secrets.token_hex(3)}"

        # Simulated binary content (in production: LLVM IR with mutation passes)
        build_payload = f"JOCKY_AGENT_v1\nHOST:{host}\nSEED:{mutation_seed}\n{jir_json}"
        build_bytes = build_payload.encode() + os.urandom(128)

        # Compute hashes
        sha256 = hashlib.sha256(build_bytes).hexdigest()
        import_hash = hashlib.md5(f"imports_{mutation_seed}".encode()).hexdigest()

        # Simulated entry point (varies per build)
        entry_bytes = secrets.token_bytes(2)
        entry_point = f"0x{int.from_bytes(entry_bytes, 'big'):04X}"

        # Write build artifact in binary mode
        output_path = os.path.join(self.output_dir, f"agent_{host.lower()}.bin")
        with open(output_path, "wb") as f:
            f.write(build_bytes)

        # Anchor build hash to blockchain ledger
        build_evidence = Evidence(
            evidence_id=build_id,
            artifact_type=ArtifactType.FILE,
            host=host,
            data={"type": "FORGE_BUILD", "case_id": case_id, "host": host},
            sha256=sha256,
        )
        self.ledger.anchor(build_evidence, case_id)

        return ForgeBuild(
            host=host,
            sha256=sha256,
            entry_point=entry_point,
            import_hash=import_hash,
            build_id=build_id,
            case_id=case_id,
            mutation_seed=mutation_seed,
            output_path=output_path,
        )

    def _print_build(self, build: ForgeBuild):
        """Print build info in demo format."""
        live(f"{build.host}  BuildID: {build.build_id}")
        live(f"         SHA-256: {build.sha256}")
        live(f"         Entry:   {build.entry_point}")
        live(f"         ImpHash: {build.import_hash[:16]}")
        live("")
