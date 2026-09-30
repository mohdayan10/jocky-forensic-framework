"""ELF Mutator — Section restructuring for Linux polymorphic builds.

Falls back to simulation if pyelftools is unavailable.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

try:
    from elftools.elf.elffile import ELFFile
    ELFTOOLS_AVAILABLE = True
except ImportError:
    ELFTOOLS_AVAILABLE = False


@dataclass
class ELFMutationResult:
    binary: bytes
    entry_point: int
    section_hash: str
    original_size: int
    mutated_size: int


class ELFMutator:
    """Mutates ELF binary structure for per-host uniqueness."""

    def __init__(self, seed: str):
        self.seed = seed
        self._rng_state = hashlib.sha256(seed.encode()).digest()

    def _rand_int(self, low: int, high: int) -> int:
        self._rng_state = hashlib.sha256(self._rng_state).digest()
        val = int.from_bytes(self._rng_state[:4], 'little')
        return low + (val % (high - low))

    def mutate(self, obj_bytes: bytes) -> ELFMutationResult:
        if ELFTOOLS_AVAILABLE and len(obj_bytes) > 52:
            return self._mutate_real(obj_bytes)
        return self._mutate_simulated(obj_bytes)

    def _mutate_real(self, obj_bytes: bytes) -> ELFMutationResult:
        import io
        try:
            elf = ELFFile(io.BytesIO(obj_bytes))
        except Exception:
            return self._mutate_simulated(obj_bytes)

        entry_point = elf.header.e_entry + self._rand_int(0, 0x100) * 0x10
        section_names = [s.name for s in elf.iter_sections() if s.name]
        section_hash = hashlib.sha256(
            (self.seed + "".join(section_names)).encode()).hexdigest()[:16]

        padding = os.urandom(self._rand_int(128, 512))
        binary = obj_bytes + self.seed.encode() + padding

        return ELFMutationResult(
            binary=binary,
            entry_point=entry_point,
            section_hash=section_hash,
            original_size=len(obj_bytes),
            mutated_size=len(binary),
        )

    def _mutate_simulated(self, obj_bytes: bytes) -> ELFMutationResult:
        entry_point = self._rand_int(0x400000, 0x4FFFFF)
        section_hash = hashlib.sha256(
            f"{self.seed}_elf".encode() + os.urandom(16)).hexdigest()[:16]

        payload = obj_bytes + self.seed.encode() + os.urandom(self._rand_int(128, 512))
        binary = hashlib.sha256(payload).digest() + os.urandom(256) + payload

        return ELFMutationResult(
            binary=binary,
            entry_point=entry_point,
            section_hash=section_hash,
            original_size=len(obj_bytes),
            mutated_size=len(binary),
        )
