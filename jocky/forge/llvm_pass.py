"""LLVM Mutation Pass — CFG mutation for polymorphic binary generation.

Four mutation passes applied per-seed:
  1. Dead basic block insertion (random block names + arithmetic)
  2. Symbol name mutation (sha256(name+seed)[:12])
  3. Instruction sequence substitution
  4. Section seed embedding for PE/ELF stage

Falls back to hashlib-based simulation if llvmlite is unavailable.
"""

from __future__ import annotations

import hashlib
import os
import secrets
from dataclasses import dataclass, field

try:
    from llvmlite import ir, binding
    LLVMLITE_AVAILABLE = True
except ImportError:
    LLVMLITE_AVAILABLE = False


@dataclass
class MutationStats:
    dead_blocks_inserted: int = 0
    symbols_mutated: int = 0
    instructions_substituted: int = 0
    section_seed: str = ""


class LLVMMutationPass:
    """Applies four mutation passes to produce structurally unique object code."""

    def __init__(self, seed: str):
        self.seed = seed
        self.stats = MutationStats()
        self._rng = hashlib.sha256(seed.encode())

    def _next_rand(self, n: int = 8) -> bytes:
        self._rng.update(os.urandom(4))
        return self._rng.digest()[:n]

    def _mutate_symbol(self, name: str) -> str:
        h = hashlib.sha256(f"{name}{self.seed}".encode()).hexdigest()[:12]
        self.stats.symbols_mutated += 1
        return f"_{h}"

    def apply(self, jir) -> dict:
        """Apply all four mutation passes to a JIR program.

        Returns a dict with module IR (if llvmlite available) or simulated
        mutation metadata.
        """
        if LLVMLITE_AVAILABLE:
            return self._apply_llvmlite(jir)
        return self._apply_simulated(jir)

    def _apply_llvmlite(self, jir) -> dict:
        module = ir.Module(name="jocky_agent")
        module.triple = "x86_64-pc-windows-msvc"

        func_type = ir.FunctionType(ir.IntType(32), [])
        main_func = ir.Function(module, func_type,
                                name=self._mutate_symbol("collector_main"))

        entry = main_func.append_basic_block(name="entry")
        builder = ir.IRBuilder(entry)

        # Pass 1: Dead basic block insertion
        num_dead = int.from_bytes(self._next_rand(2), 'little') % 8 + 2
        for i in range(num_dead):
            block_name = f"dead_{self._next_rand(4).hex()}"
            dead_block = main_func.append_basic_block(name=block_name)
            dead_builder = ir.IRBuilder(dead_block)
            a = dead_builder.add(
                ir.Constant(ir.IntType(32), int.from_bytes(self._next_rand(4), 'little')),
                ir.Constant(ir.IntType(32), int.from_bytes(self._next_rand(4), 'little')))
            dead_builder.ret(a)
            self.stats.dead_blocks_inserted += 1

        # Pass 3: Instruction substitution (vary arithmetic patterns)
        val = ir.Constant(ir.IntType(32), int.from_bytes(self._next_rand(4), 'little'))
        sub_choice = int.from_bytes(self._next_rand(1), 'little') % 3
        if sub_choice == 0:
            result = builder.add(val, ir.Constant(ir.IntType(32), 1))
        elif sub_choice == 1:
            result = builder.sub(val, ir.Constant(ir.IntType(32), -1))
        else:
            result = builder.xor(val, ir.Constant(ir.IntType(32), 0))
        self.stats.instructions_substituted += 1

        builder.ret(ir.Constant(ir.IntType(32), 0))

        # Pass 4: Section seed embedding
        self.stats.section_seed = self.seed
        seed_data = ir.GlobalVariable(module, ir.ArrayType(ir.IntType(8), 16),
                                      name=self._mutate_symbol("section_seed"))
        seed_bytes = bytes.fromhex(self.seed.ljust(32, '0')[:32])
        seed_data.initializer = ir.Constant(
            ir.ArrayType(ir.IntType(8), 16),
            [ir.Constant(ir.IntType(8), b) for b in seed_bytes[:16]])
        seed_data.global_constant = True

        return {"module": module, "stats": self.stats, "ir_text": str(module)}

    def _apply_simulated(self, jir) -> dict:
        """Hashlib-based simulation when llvmlite is not installed."""
        ops = jir.ops if hasattr(jir, 'ops') else []
        mutated_symbols = {}
        for i, op in enumerate(ops):
            original = f"op_{i}_{type(op).__name__}"
            mutated_symbols[original] = self._mutate_symbol(original)

        dead_blocks = int.from_bytes(self._next_rand(2), 'little') % 8 + 2
        self.stats.dead_blocks_inserted = dead_blocks
        self.stats.instructions_substituted = len(ops) + dead_blocks
        self.stats.section_seed = self.seed

        ir_text = f"; JOCKY IR Module (simulated — llvmlite not available)\n"
        ir_text += f"; seed: {self.seed}\n"
        ir_text += f"; dead_blocks: {dead_blocks}\n"
        ir_text += f"; mutated_symbols: {len(mutated_symbols)}\n"
        for orig, mut in mutated_symbols.items():
            ir_text += f"; {orig} -> {mut}\n"

        return {"module": None, "stats": self.stats, "ir_text": ir_text}

    def emit_object(self, module=None) -> bytes:
        """Emit native object bytes from LLVM module.

        Returns real object code if llvmlite is available,
        otherwise returns simulated unique bytes.
        """
        if LLVMLITE_AVAILABLE and module is not None:
            binding.initialize()
            binding.initialize_native_target()
            binding.initialize_native_asmprinter()

            llvm_ir = str(module)
            mod = binding.parse_assembly(llvm_ir)
            mod.verify()

            target = binding.Target.from_default_triple()
            machine = target.create_target_machine()
            return machine.emit_object(mod)

        payload = f"jocky_object_{self.seed}".encode()
        payload += os.urandom(2048)
        return hashlib.sha256(payload).digest() + os.urandom(256)
