"""JOCKY Lexer — Converts raw .jky source text into a stream of tokens."""

from __future__ import annotations

import re
from typing import List

from .tokens import Token, TokenType, KEYWORDS


class LexerError(Exception):
    """Raised when the lexer encounters an unexpected character."""

    def __init__(self, message: str, line: int, column: int):
        self.line = line
        self.column = column
        super().__init__(f"[LEXER] Error at L{line}:{column}: {message}")


class Lexer:
    """Tokenizes JOCKY source code."""

    # Duration pattern: e.g. "72h", "45s", "30m"
    DURATION_RE = re.compile(r"^(\d+)(h|s|m)$")

    def __init__(self, source: str, filename: str = "<stdin>"):
        self.source = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []

    def _peek(self) -> str | None:
        if self.pos < len(self.source):
            return self.source[self.pos]
        return None

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _skip_whitespace(self):
        """Skip spaces and tabs (not newlines — they're significant)."""
        while self.pos < len(self.source) and self.source[self.pos] in (" ", "\t", "\r"):
            self._advance()

    def _skip_comment(self):
        """Skip from # to end of line."""
        while self.pos < len(self.source) and self.source[self.pos] != "\n":
            self._advance()

    def _read_string(self) -> str:
        """Read a quoted string literal (supports both ' and \")."""
        quote = self._advance()  # consume opening quote
        start = self.pos
        result = []
        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch == "\\":
                self._advance()
                if self.pos < len(self.source):
                    escaped = self._advance()
                    escape_map = {"n": "\n", "t": "\t", "\\": "\\", '"': '"', "'": "'"}
                    result.append(escape_map.get(escaped, escaped))
                continue
            if ch == quote:
                self._advance()  # consume closing quote
                return "".join(result)
            result.append(ch)
            self._advance()
        raise LexerError("Unterminated string literal", self.line, self.column)

    def _read_number(self) -> Token:
        """Read a number, possibly followed by a duration suffix."""
        start_col = self.column
        start_line = self.line
        num_str = ""
        while self.pos < len(self.source) and self.source[self.pos].isdigit():
            num_str += self._advance()

        # Check for duration suffix: h, s, m
        if self.pos < len(self.source) and self.source[self.pos] in ("h", "s", "m"):
            suffix = self._advance()
            return Token(TokenType.DURATION, num_str + suffix, start_line, start_col)

        return Token(TokenType.NUMBER, int(num_str), start_line, start_col)

    def _read_identifier(self) -> Token:
        """Read an identifier or keyword."""
        start_col = self.column
        start_line = self.line
        ident = ""
        while self.pos < len(self.source) and (
            self.source[self.pos].isalnum() or self.source[self.pos] in ("_", "-")
        ):
            ident += self._advance()

        # Check keywords
        token_type = KEYWORDS.get(ident, TokenType.IDENTIFIER)
        return Token(token_type, ident, start_line, start_col)

    def tokenize(self) -> List[Token]:
        """Tokenize the entire source and return a list of tokens."""
        self.tokens = []
        last_was_newline = True  # suppress leading newlines

        while self.pos < len(self.source):
            self._skip_whitespace()

            ch = self._peek()
            if ch is None:
                break

            start_line = self.line
            start_col = self.column

            # Newlines
            if ch == "\n":
                self._advance()
                if not last_was_newline:
                    self.tokens.append(Token(TokenType.NEWLINE, "\\n", start_line, start_col))
                    last_was_newline = True
                continue

            last_was_newline = False

            # Comments
            if ch == "#":
                self._skip_comment()
                continue

            # Strings
            if ch in ('"', "'"):
                value = self._read_string()
                self.tokens.append(Token(TokenType.STRING, value, start_line, start_col))
                continue

            # Numbers / Durations
            if ch.isdigit():
                self.tokens.append(self._read_number())
                continue

            # Identifiers / Keywords
            if ch.isalpha() or ch == "_":
                self.tokens.append(self._read_identifier())
                continue

            # Symbols
            symbol_map = {
                "[": TokenType.LBRACKET,
                "]": TokenType.RBRACKET,
                "(": TokenType.LPAREN,
                ")": TokenType.RPAREN,
                ",": TokenType.COMMA,
                ".": TokenType.DOT,
            }

            if ch in symbol_map:
                self._advance()
                self.tokens.append(Token(symbol_map[ch], ch, start_line, start_col))
                continue

            # == vs =
            if ch == "=":
                self._advance()
                if self._peek() == "=":
                    self._advance()
                    self.tokens.append(Token(TokenType.EQUALS, "==", start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.ASSIGN, "=", start_line, start_col))
                continue

            raise LexerError(f"Unexpected character: {ch!r}", start_line, start_col)

        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens

    def tokenize_verbose(self) -> List[Token]:
        """Tokenize with [LEXER] status output for demo."""
        print(f"[LEXER]    Tokenizing {self.filename}...", end="")
        tokens = self.tokenize()
        count = len([t for t in tokens if t.type != TokenType.EOF])
        print(f"          OK  ({count} tokens)")
        return tokens
