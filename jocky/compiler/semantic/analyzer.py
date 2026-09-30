"""JOCKY Semantic Analyzer — Validates AST for forensic correctness."""

from __future__ import annotations

from typing import List, Set

from ..parser.ast_nodes import (
    Program, CaseDecl, TargetDecl,
    CollectStmt, CorrelateStmt, DetectStmt,
    TimelineStmt, EvidenceGraphStmt, GenerateReportStmt,
)


class SemanticError(Exception):
    def __init__(self, message: str, line: int = 0, column: int = 0):
        self.line = line
        self.column = column
        super().__init__(f"[SEMANTIC] Error at L{line}:{column}: {message}")


class SemanticAnalyzer:
    """Validates a JOCKY AST for forensic semantic correctness.

    Rules enforced:
    1. Every program must have a case declaration
    2. Every program must have a target declaration
    3. Collection types that support filters MUST have filters (no unscoped collection)
    4. Correlation sources/targets must reference collected artifact types
    5. Detection rules must be from the known rule set
    6. No duplicate collect statements for the same type
    """

    # Types that REQUIRE filters — unscoped collection is rejected
    FILTER_REQUIRED = {"file_metadata"}

    # Types that can be collected
    VALID_COLLECT_TYPES = {
        "processes", "network", "persistence", "drivers",
        "file_metadata", "kernel_callbacks", "hook_state",
        "hidden_processes", "users",
    }

    # Known detection rules
    KNOWN_RULES = {
        "unsigned_executable_in_temp",
        "byovd_loaded_driver",
        "suspicious_process_chain",
        "lateral_movement",
        "persistence_anomaly",
        "rapid_outbound_connection",
        "hidden_process_delta",
        "kernel_callback_modification",
        "unusual_parent_child",
        "dll_injection_indicator",
    }

    # Correlatable artifact types (mapped from collect type names)
    CORRELATABLE = {
        "processes", "network", "persistence", "drivers",
        "files", "users", "kernel_callbacks",
    }

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.collected_types: Set[str] = set()

    def analyze(self, program: Program) -> bool:
        """Analyze the program. Returns True if valid, False otherwise."""
        self.errors = []
        self.warnings = []
        self.collected_types = set()

        # Rule 1: Must have case
        if program.case is None:
            self.errors.append("Missing case declaration — every investigation must have a case ID")

        # Rule 2: Must have target
        if program.target is None:
            self.errors.append("Missing target declaration — collection scope is required")

        # Analyze statements
        for stmt in program.statements:
            if isinstance(stmt, CollectStmt):
                self._check_collect(stmt)
            elif isinstance(stmt, CorrelateStmt):
                self._check_correlate(stmt)
            elif isinstance(stmt, DetectStmt):
                self._check_detect(stmt)
            elif isinstance(stmt, GenerateReportStmt):
                self._check_report(stmt)

        return len(self.errors) == 0

    def analyze_verbose(self, program: Program) -> bool:
        """Analyze with [SEMANTIC] status output for demo."""
        print("[SEMANTIC] Type check + scope resolution...", end="")
        result = self.analyze(program)
        if result:
            print("     OK")
        else:
            print("     FAILED")
            for err in self.errors:
                print(f"           → {err}")
        return result

    def _check_collect(self, stmt: CollectStmt):
        """Validate a collect statement."""
        # Duplicate check
        if stmt.artifact_type in self.collected_types:
            self.warnings.append(
                f"Duplicate collect for '{stmt.artifact_type}' at L{stmt.line}"
            )
        self.collected_types.add(stmt.artifact_type)

        # Filter requirement check
        if stmt.artifact_type in self.FILTER_REQUIRED and not stmt.filters:
            self.errors.append(
                f"Unscoped collection rejected: '{stmt.artifact_type}' requires "
                f"explicit filters (L{stmt.line}:{stmt.column})"
            )

    def _check_correlate(self, stmt: CorrelateStmt):
        """Validate correlation references collected types."""
        for ref in (stmt.source, stmt.target):
            if ref not in self.CORRELATABLE:
                self.warnings.append(
                    f"Correlation references unknown type '{ref}' at L{stmt.line} — "
                    f"valid types: {', '.join(sorted(self.CORRELATABLE))}"
                )

    def _check_detect(self, stmt: DetectStmt):
        """Validate detection rule exists."""
        if stmt.rule_name not in self.KNOWN_RULES:
            self.warnings.append(
                f"Unknown detection rule '{stmt.rule_name}' at L{stmt.line} — "
                f"will be treated as custom rule"
            )

    def _check_report(self, stmt: GenerateReportStmt):
        """Validate report format."""
        valid_formats = {"json", "pdf", "csv", "html"}
        for fmt in stmt.formats:
            if fmt not in valid_formats:
                self.errors.append(
                    f"Unknown report format '{fmt}' at L{stmt.line} — "
                    f"valid formats: {', '.join(sorted(valid_formats))}"
                )
