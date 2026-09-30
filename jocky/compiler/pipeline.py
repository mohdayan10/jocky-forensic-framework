"""JOCKY Compiler Pipeline — Orchestrates Lexer → Parser → Semantic → JIR → Policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .lexer import Lexer, Token
from .lexer.tokens import TokenType
from .parser import Parser
from .parser.ast_nodes import Program
from .semantic import SemanticAnalyzer
from .jir import JIREmitter
from .jir.emitter import JIRProgram
from .policy import PolicyValidator
from .policy.validator import InvestigatorCert, PolicyResult


@dataclass
class CompileResult:
    """Result of the full compilation pipeline."""
    success: bool
    jir: Optional[JIRProgram] = None
    jir_text: str = ""
    jir_json: str = ""
    ast: Optional[Program] = None
    policy: Optional[PolicyResult] = None
    errors: list = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class CompilerPipeline:
    """Full JOCKY compilation pipeline."""

    def __init__(self, cert: Optional[InvestigatorCert] = None, verbose: bool = False):
        self.cert = cert
        self.verbose = verbose

    def compile(self, source: str, filename: str = "<stdin>") -> CompileResult:
        """Run the full pipeline: Lex → Parse → Semantic → JIR → Policy."""
        result = CompileResult(success=False)

        try:
            # Stage 1: Lexer
            lexer = Lexer(source, filename)
            if self.verbose:
                tokens = lexer.tokenize_verbose()
            else:
                tokens = lexer.tokenize()

            # Stage 2: Parser
            parser = Parser(tokens)
            if self.verbose:
                ast = parser.parse_verbose()
            else:
                ast = parser.parse()
            result.ast = ast

            # Stage 3: Semantic Analysis
            analyzer = SemanticAnalyzer()
            if self.verbose:
                valid = analyzer.analyze_verbose(ast)
            else:
                valid = analyzer.analyze(ast)

            if not valid:
                result.errors.extend(analyzer.errors)
                return result

            if analyzer.warnings and self.verbose:
                for w in analyzer.warnings:
                    print(f"           ⚠ {w}")

            # Stage 4: JIR Emission
            emitter = JIREmitter()
            if self.verbose:
                jir = emitter.emit_verbose(ast)
            else:
                jir = emitter.emit(ast)

            # Attach pipeline metadata
            token_count = len([t for t in tokens if t.type != TokenType.EOF and t.type != TokenType.NEWLINE])
            jir.token_count = token_count
            jir.cert_id = self.cert.cert_id if self.cert else ""
            jir.kernel_authorized = self.cert.kernel_ops_authorized if self.cert else False
            jir.case_expiry = (
                self.cert.case_expiry.strftime("%Y-%m-%d")
                if self.cert and self.cert.case_expiry else ""
            )

            result.jir = jir
            result.jir_text = emitter.format_text(jir)
            result.jir_json = emitter.to_json(jir)

            # Stage 5: Policy Validation
            validator = PolicyValidator(self.cert)
            if self.verbose:
                policy = validator.validate_verbose(jir)
            else:
                policy = validator.validate(jir)

            result.policy = policy

            if not policy.passed:
                result.errors.extend(policy.errors)
                return result

            result.success = True
            return result

        except Exception as e:
            result.errors.append(str(e))
            return result
