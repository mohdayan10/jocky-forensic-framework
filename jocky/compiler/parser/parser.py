"""JOCKY Parser — Recursive descent parser that builds an AST from tokens."""

from __future__ import annotations

from typing import List, Optional

from ..lexer.tokens import Token, TokenType
from .ast_nodes import (
    Program, CaseDecl, TargetDecl,
    CollectStmt, FilterExpr,
    CorrelateStmt, DetectStmt,
    TimelineStmt, EvidenceGraphStmt, GenerateReportStmt,
)


class ParseError(Exception):
    def __init__(self, message: str, token: Token):
        self.token = token
        super().__init__(f"[PARSER] Error at L{token.line}:{token.column}: {message}")


class Parser:
    """Recursive descent parser for the JOCKY language."""

    # Valid collection artifact types
    COLLECT_TYPES = {
        "processes", "network", "persistence", "drivers",
        "file_metadata", "kernel_callbacks", "hook_state",
        "hidden_processes", "users",
    }

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def _current(self) -> Token:
        return self.tokens[self.pos]

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _peek_type(self) -> TokenType:
        return self.tokens[self.pos].type

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _expect(self, token_type: TokenType, context: str = "") -> Token:
        tok = self._current()
        if tok.type != token_type:
            ctx = f" (in {context})" if context else ""
            raise ParseError(
                f"Expected {token_type.name}, got {tok.type.name}{ctx}", tok
            )
        return self._advance()

    def _skip_newlines(self):
        while self.pos < len(self.tokens) and self._peek_type() == TokenType.NEWLINE:
            self._advance()

    def _at_end(self) -> bool:
        return self._peek_type() == TokenType.EOF

    # ── Top-level ──

    def parse(self) -> Program:
        """Parse a complete JOCKY program."""
        program = Program()
        self._skip_newlines()

        while not self._at_end():
            stmt = self._parse_statement()
            if stmt is not None:
                if isinstance(stmt, CaseDecl):
                    if program.case is not None:
                        raise ParseError("Duplicate case declaration", self._current())
                    program.case = stmt
                elif isinstance(stmt, TargetDecl):
                    if program.target is not None:
                        raise ParseError("Duplicate target declaration", self._current())
                    program.target = stmt
                else:
                    program.statements.append(stmt)
            self._skip_newlines()

        return program

    def parse_verbose(self) -> Program:
        """Parse with [PARSER] status output for demo."""
        print("[PARSER]   Building AST...", end="")
        program = self.parse()
        stmt_count = len(program.statements)
        print(f"                      OK  ({stmt_count} statements)")
        return program

    # ── Statement dispatch ──

    def _parse_statement(self):
        tok = self._peek()

        if tok.type == TokenType.CASE:
            return self._parse_case()
        elif tok.type == TokenType.TARGET:
            return self._parse_target()
        elif tok.type == TokenType.COLLECT:
            return self._parse_collect()
        elif tok.type == TokenType.CORRELATE:
            return self._parse_correlate()
        elif tok.type == TokenType.DETECT:
            return self._parse_detect()
        elif tok.type == TokenType.TIMELINE:
            self._advance()
            return TimelineStmt(line=tok.line, column=tok.column)
        elif tok.type == TokenType.EVIDENCE_GRAPH:
            self._advance()
            return EvidenceGraphStmt(line=tok.line, column=tok.column)
        elif tok.type == TokenType.GENERATE:
            return self._parse_generate()
        elif tok.type == TokenType.NEWLINE:
            self._advance()
            return None
        else:
            raise ParseError(f"Unexpected token: {tok.type.name} ({tok.value!r})", tok)

    # ── case "OP-FALCON-01" ──

    def _parse_case(self) -> CaseDecl:
        tok = self._advance()  # consume 'case'
        name_tok = self._expect(TokenType.STRING, "case declaration")
        return CaseDecl(case_id=name_tok.value, line=tok.line, column=tok.column)

    # ── target hostgroup ENTERPRISE_EAST ──

    def _parse_target(self) -> TargetDecl:
        tok = self._advance()  # consume 'target'
        type_tok = self._advance()  # e.g., 'hostgroup'
        name_tok = self._advance()  # e.g., 'ENTERPRISE_EAST'
        return TargetDecl(
            target_type=type_tok.value,
            target_name=name_tok.value,
            line=tok.line,
            column=tok.column,
        )

    # ── collect <type> [WHERE <filters>] ──

    def _parse_collect(self) -> CollectStmt:
        tok = self._advance()  # consume 'collect'
        type_tok = self._advance()
        artifact_type = type_tok.value

        if artifact_type not in self.COLLECT_TYPES:
            raise ParseError(
                f"Unknown collection type: {artifact_type!r}. "
                f"Valid types: {', '.join(sorted(self.COLLECT_TYPES))}",
                type_tok,
            )

        filters = []
        # Check for WHERE clause
        if not self._at_end() and self._peek_type() == TokenType.WHERE:
            self._advance()  # consume WHERE
            filters = self._parse_filters()

        return CollectStmt(
            artifact_type=artifact_type,
            filters=filters,
            line=tok.line,
            column=tok.column,
        )

    def _parse_filters(self) -> List[FilterExpr]:
        """Parse filter expressions: field OP value [AND field OP value ...]"""
        filters = []
        filters.append(self._parse_single_filter())

        while not self._at_end():
            self._skip_newlines()
            if self._at_end() or self._peek_type() != TokenType.AND:
                break
            self._advance()  # consume AND
            filters.append(self._parse_single_filter())

        return filters

    def _parse_single_filter(self) -> FilterExpr:
        """Parse: path IN [...] or modified_within \"72h\" etc."""
        field_tok = self._advance()
        field_name = field_tok.value

        # path IN ["Temp", "AppData"]
        if self._peek_type() == TokenType.IN:
            self._advance()  # consume IN
            values = self._parse_string_list()
            return FilterExpr(
                field=field_name, operator="IN", value=values,
                line=field_tok.line, column=field_tok.column,
            )

        # modified_within "72h"
        if field_name == "modified_within":
            val_tok = self._advance()
            return FilterExpr(
                field=field_name, operator="modified_within",
                value=val_tok.value,
                line=field_tok.line, column=field_tok.column,
            )

        # field == value
        if self._peek_type() == TokenType.EQUALS:
            self._advance()
            val_tok = self._advance()
            return FilterExpr(
                field=field_name, operator="==", value=val_tok.value,
                line=field_tok.line, column=field_tok.column,
            )

        raise ParseError(f"Expected filter operator after {field_name!r}", field_tok)

    def _parse_string_list(self) -> List[str]:
        """Parse: [\"a\", \"b\", \"c\"]"""
        self._expect(TokenType.LBRACKET, "string list")
        items = []
        while self._peek_type() != TokenType.RBRACKET:
            tok = self._advance()
            items.append(tok.value)
            if self._peek_type() == TokenType.COMMA:
                self._advance()
        self._expect(TokenType.RBRACKET, "string list")
        return items

    # ── correlate <src> WITH <tgt> [WITHIN <dur>] ──

    def _parse_correlate(self) -> CorrelateStmt:
        tok = self._advance()  # consume 'correlate'
        source_tok = self._advance()
        self._expect(TokenType.WITH, "correlate")
        target_tok = self._advance()

        within = None
        if not self._at_end() and self._peek_type() == TokenType.WITHIN:
            self._advance()  # consume WITHIN
            dur_tok = self._advance()  # number
            unit_tok = self._advance()  # seconds/minutes
            within = f"{dur_tok.value}{unit_tok.value[0]}"  # e.g., "45s"

        return CorrelateStmt(
            source=source_tok.value,
            target=target_tok.value,
            within=within,
            line=tok.line,
            column=tok.column,
        )

    # ── detect <rule_name> ──

    def _parse_detect(self) -> DetectStmt:
        tok = self._advance()  # consume 'detect'
        rule_tok = self._advance()
        return DetectStmt(
            rule_name=rule_tok.value,
            line=tok.line,
            column=tok.column,
        )

    # ── generate report FORMAT [json, pdf] ──

    def _parse_generate(self) -> GenerateReportStmt:
        tok = self._advance()  # consume 'generate'
        self._expect(TokenType.REPORT, "generate")
        self._expect(TokenType.FORMAT, "generate report")
        formats = self._parse_string_list()
        return GenerateReportStmt(
            formats=formats,
            line=tok.line,
            column=tok.column,
        )
