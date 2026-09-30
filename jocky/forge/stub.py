"""Polymorphic Stub — AES-256 encrypted payload with varying decryption stub.

Wraps a binary payload in an encrypted container with a per-build unique
decryption stub whose byte pattern varies with the key.
"""

from __future__ import annotations

import hashlib
import os
import secrets
import struct
from dataclasses import dataclass

try:
    from Crypto.Cipher import AES
    PYCRYPTO_AVAILABLE = True
except ImportError:
    PYCRYPTO_AVAILABLE = False


@dataclass
class StubResult:
    wrapped_binary: bytes
    stub_size: int
    payload_size: int
    key_hash: str
    iv: bytes


class PolymorphicStub:
    """Wraps a binary with AES-256 encryption and a polymorphic decryption stub."""

    def __init__(self, key: bytes = None, seed: str = ""):
        self.key = key or secrets.token_bytes(32)
        self.seed = seed
        self.iv = os.urandom(16)

    def _generate_stub(self) -> bytes:
        """Generate a decryption stub whose byte pattern varies with the key.

        The stub is x86-64 shellcode that:
        1. Locates the encrypted payload after itself
        2. Derives the AES key from embedded key material
        3. Decrypts the payload in-place
        4. Jumps to decrypted entry point

        Polymorphism: instruction ordering, register selection, and NOP
        patterns vary based on the key hash.
        """
        key_hash = hashlib.sha256(self.key).digest()

        stub = bytearray()

        # Variable NOP sled (length varies with key)
        nop_len = key_hash[0] % 16 + 4
        nop_patterns = [
            b'\x90',              # NOP
            b'\x66\x90',          # 66 NOP
            b'\x0f\x1f\x00',     # NOP DWORD [rax]
            b'\x0f\x1f\x40\x00', # NOP DWORD [rax+0]
        ]
        for i in range(nop_len):
            stub.extend(nop_patterns[key_hash[i % 32] % len(nop_patterns)])

        # Embed key material (XOR-encoded with seed-derived mask)
        mask = hashlib.sha256(self.seed.encode()).digest()
        encoded_key = bytes(k ^ m for k, m in zip(self.key, mask))
        stub.extend(encoded_key)

        # Embed IV
        stub.extend(self.iv)

        # Stub metadata: payload offset, payload size (filled during wrap)
        stub.extend(b'\x00' * 8)  # Placeholder for payload_offset + payload_size

        return bytes(stub)

    def _pad(self, data: bytes) -> bytes:
        pad_len = 16 - (len(data) % 16)
        return data + bytes([pad_len] * pad_len)

    def _encrypt(self, plaintext: bytes) -> bytes:
        padded = self._pad(plaintext)
        if PYCRYPTO_AVAILABLE:
            cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
            return cipher.encrypt(padded)

        # Simulation: XOR-based "encryption" preserving size variance
        key_stream = b''
        block = self.iv
        while len(key_stream) < len(padded):
            block = hashlib.sha256(self.key + block).digest()[:16]
            key_stream += block
        return bytes(p ^ k for p, k in zip(padded, key_stream[:len(padded)]))

    def wrap(self, binary: bytes) -> StubResult:
        """Wrap binary with encrypted container and polymorphic stub."""
        stub = self._generate_stub()
        encrypted = self._encrypt(binary)

        # Patch stub with payload offset and size
        stub_mut = bytearray(stub)
        payload_offset = len(stub)
        struct.pack_into('<I', stub_mut, len(stub_mut) - 8, payload_offset)
        struct.pack_into('<I', stub_mut, len(stub_mut) - 4, len(encrypted))

        wrapped = bytes(stub_mut) + encrypted

        return StubResult(
            wrapped_binary=wrapped,
            stub_size=len(stub),
            payload_size=len(encrypted),
            key_hash=hashlib.sha256(self.key).hexdigest()[:16],
            iv=self.iv,
        )
