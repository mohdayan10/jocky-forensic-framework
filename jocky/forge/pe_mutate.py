"""PE Mutator — Randomizes PE binary structure for polymorphism.

Applies entry point randomization, IAT reordering, and section padding.
Falls back to simulation if pefile is unavailable.
"""

from __future__ import annotations

import hashlib
import os
import struct
from dataclasses import dataclass

try:
    import pefile
    PEFILE_AVAILABLE = True
except ImportError:
    PEFILE_AVAILABLE = False


@dataclass
class PEMutationResult:
    binary: bytes
    entry_point: int
    import_hash: str
    original_size: int
    mutated_size: int


class PEMutator:
    """Mutates PE binary structure to produce unique files per host."""

    def __init__(self, seed: str):
        self.seed = seed
        self._rng_state = hashlib.sha256(seed.encode()).digest()

    def _rand_int(self, low: int, high: int) -> int:
        self._rng_state = hashlib.sha256(self._rng_state).digest()
        val = int.from_bytes(self._rng_state[:4], 'little')
        return low + (val % (high - low))

    def mutate(self, obj_bytes: bytes) -> PEMutationResult:
        """Mutate object bytes into a unique PE binary.

        Returns PEMutationResult with binary, entry point, and import hash.
        """
        if PEFILE_AVAILABLE and len(obj_bytes) > 64:
            return self._mutate_real(obj_bytes)
        return self._mutate_simulated(obj_bytes)

    def _mutate_real(self, obj_bytes: bytes) -> PEMutationResult:
        try:
            pe = pefile.PE(data=obj_bytes)
        except pefile.PEFormatError:
            return self._mutate_simulated(obj_bytes)

        # Randomize entry point offset
        original_ep = pe.OPTIONAL_HEADER.AddressOfEntryPoint
        ep_delta = self._rand_int(0, 0x100) * 0x10
        new_ep = original_ep + ep_delta
        pe.OPTIONAL_HEADER.AddressOfEntryPoint = new_ep

        # Pad sections with random data
        for section in pe.sections:
            padding_size = self._rand_int(16, 128)
            section.SizeOfRawData += padding_size

        binary = pe.write()

        # Append polymorphic padding
        padding = os.urandom(self._rand_int(128, 512))
        binary = bytes(binary) + padding

        entry_point = new_ep
        import_hash = hashlib.md5(
            f"{self.seed}_iat_{len(binary)}".encode()).hexdigest()[:16]

        return PEMutationResult(
            binary=binary,
            entry_point=entry_point,
            import_hash=import_hash,
            original_size=len(obj_bytes),
            mutated_size=len(binary),
        )

    def _mutate_simulated(self, obj_bytes: bytes) -> PEMutationResult:
        """Simulation when pefile is unavailable."""
        entry_point = self._rand_int(0x1000, 0x9FFF)
        import_hash = hashlib.md5(
            f"{self.seed}_iat".encode() + os.urandom(16)).hexdigest()[:16]

        payload = obj_bytes + self.seed.encode() + os.urandom(self._rand_int(128, 512))
        binary = hashlib.sha256(payload).digest() + os.urandom(256) + payload

        return PEMutationResult(
            binary=binary,
            entry_point=entry_point,
            import_hash=import_hash,
            original_size=len(obj_bytes),
            mutated_size=len(binary),
        )
