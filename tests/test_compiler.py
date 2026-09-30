"""Tests for the JOCKY compiler pipeline."""

import unittest

from jocky.compiler.lexer import Lexer, TokenType
from jocky.compiler.parser import Parser
from jocky.compiler.parser.ast_nodes import (
    CollectStmt, CorrelateStmt, DetectStmt,
    TimelineStmt, EvidenceGraphStmt, GenerateReportStmt,
)
from jocky.compiler.semantic import SemanticAnalyzer
from jocky.compiler.jir import JIREmitter
from jocky.compiler.policy import PolicyValidator
from jocky.compiler.policy.validator import InvestigatorCert
from jocky.compiler.pipeline import CompilerPipeline


VALID_PROGRAM = '''\
case "OP-FALCON-01"
target hostgroup ENTERPRISE_EAST

collect processes
collect network
collect persistence
collect drivers
collect file_metadata WHERE path IN ["Temp", "AppData"]
                       AND modified_within "72h"
collect kernel_callbacks
collect hook_state
collect hidden_processes

correlate processes WITH network WITHIN 45 seconds
correlate processes WITH files

detect unsigned_executable_in_temp
detect byovd_loaded_driver

timeline
evidence_graph
generate report FORMAT [json, pdf]
'''


class TestLexer(unittest.TestCase):
    def test_tokenize_valid_program(self):
        lexer = Lexer(VALID_PROGRAM, "test.jky")
        tokens = lexer.tokenize()
        types = [t.type for t in tokens]
        self.assertIn(TokenType.CASE, types)
        self.assertIn(TokenType.COLLECT, types)
        self.assertIn(TokenType.CORRELATE, types)
        self.assertIn(TokenType.DETECT, types)
        self.assertEqual(tokens[-1].type, TokenType.EOF)

    def test_string_literal(self):
        lexer = Lexer('case "HELLO-WORLD"')
        tokens = lexer.tokenize()
        self.assertEqual(tokens[0].type, TokenType.CASE)
        self.assertEqual(tokens[1].type, TokenType.STRING)
        self.assertEqual(tokens[1].value, "HELLO-WORLD")

    def test_duration(self):
        lexer = Lexer('72h')
        tokens = lexer.tokenize()
        self.assertEqual(tokens[0].type, TokenType.DURATION)
        self.assertEqual(tokens[0].value, "72h")

    def test_unexpected_character(self):
        lexer = Lexer('collect @invalid')
        with self.assertRaises(Exception):
            lexer.tokenize()


class TestParser(unittest.TestCase):
    def _parse(self, source):
        tokens = Lexer(source).tokenize()
        return Parser(tokens).parse()

    def test_parse_full_program(self):
        program = self._parse(VALID_PROGRAM)
        self.assertIsNotNone(program.case)
        self.assertEqual(program.case.case_id, "OP-FALCON-01")
        self.assertIsNotNone(program.target)
        self.assertEqual(program.target.target_type, "hostgroup")
        self.assertTrue(len(program.statements) > 0)

    def test_collect_with_filters(self):
        program = self._parse(VALID_PROGRAM)
        file_collects = [s for s in program.statements
                         if isinstance(s, CollectStmt) and s.artifact_type == "file_metadata"]
        self.assertEqual(len(file_collects), 1)
        self.assertEqual(len(file_collects[0].filters), 2)

    def test_correlate_with_window(self):
        program = self._parse(VALID_PROGRAM)
        correlates = [s for s in program.statements if isinstance(s, CorrelateStmt)]
        self.assertTrue(any(c.within == "45s" for c in correlates))

    def test_duplicate_case_rejected(self):
        with self.assertRaises(Exception):
            self._parse('case "A"\ncase "B"\ncollect processes')

    def test_unknown_collect_type(self):
        with self.assertRaises(Exception):
            self._parse('case "A"\ntarget hostgroup X\ncollect bananas')


class TestSemantic(unittest.TestCase):
    def _analyze(self, source):
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        analyzer = SemanticAnalyzer()
        valid = analyzer.analyze(ast)
        return valid, analyzer

    def test_valid_program(self):
        valid, _ = self._analyze(VALID_PROGRAM)
        self.assertTrue(valid)

    def test_missing_case(self):
        valid, analyzer = self._analyze('target hostgroup X\ncollect processes')
        self.assertFalse(valid)
        self.assertTrue(any("case" in e.lower() for e in analyzer.errors))

    def test_unscoped_file_metadata(self):
        source = 'case "A"\ntarget hostgroup X\ncollect file_metadata'
        valid, analyzer = self._analyze(source)
        self.assertFalse(valid)
        self.assertTrue(any("unscoped" in e.lower() for e in analyzer.errors))


class TestJIR(unittest.TestCase):
    def test_emit(self):
        tokens = Lexer(VALID_PROGRAM).tokenize()
        ast = Parser(tokens).parse()
        jir = JIREmitter().emit(ast)
        self.assertEqual(jir.case_id, "OP_FALCON_01")
        self.assertTrue(len(jir.collect_ops) > 0)
        self.assertTrue(jir.emit_timeline)
        self.assertTrue(jir.emit_evidence_graph)
        self.assertIn("json", jir.report_formats)

    def test_format_text(self):
        tokens = Lexer(VALID_PROGRAM).tokenize()
        ast = Parser(tokens).parse()
        emitter = JIREmitter()
        jir = emitter.emit(ast)
        text = emitter.format_text(jir)
        self.assertIn("CASE OP_FALCON_01", text)
        self.assertIn("COLLECT [", text)


class TestPolicy(unittest.TestCase):
    def test_valid_cert_passes(self):
        tokens = Lexer(VALID_PROGRAM).tokenize()
        ast = Parser(tokens).parse()
        jir = JIREmitter().emit(ast)
        result = PolicyValidator().validate(jir)
        self.assertTrue(result.passed)

    def test_unauthorized_host_fails(self):
        source = 'case "A"\ntarget hostgroup UNAUTHORIZED_GROUP\ncollect processes'
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        jir = JIREmitter().emit(ast)
        result = PolicyValidator().validate(jir)
        self.assertFalse(result.passed)

    def test_kernel_ops_without_auth(self):
        cert = InvestigatorCert(
            cert_id="TEST", investigator_name="Test",
            organization="Test", authorized_hostgroups=["ENTERPRISE_EAST"],
            kernel_ops_authorized=False,
        )
        source = 'case "A"\ntarget hostgroup ENTERPRISE_EAST\ncollect kernel_callbacks'
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        jir = JIREmitter().emit(ast)
        result = PolicyValidator(cert).validate(jir)
        self.assertFalse(result.passed)


class TestPipeline(unittest.TestCase):
    def test_full_pipeline(self):
        pipeline = CompilerPipeline()
        result = pipeline.compile(VALID_PROGRAM, "test.jky")
        self.assertTrue(result.success)
        self.assertIsNotNone(result.jir)
        self.assertTrue(len(result.jir_text) > 0)
        self.assertTrue(len(result.jir_json) > 0)

    def test_invalid_program(self):
        pipeline = CompilerPipeline()
        result = pipeline.compile('collect bananas', "bad.jky")
        self.assertFalse(result.success)


if __name__ == "__main__":
    unittest.main()
