"""Token types and Token dataclass for the JOCKY language."""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any


class TokenType(Enum):
    # --- Literals ---
    STRING = auto()          # "OP-FALCON-01"
    NUMBER = auto()          # 45, 72
    IDENTIFIER = auto()      # user-defined names

    # --- Keywords: Investigation ---
    CASE = auto()            # case
    TARGET = auto()          # target
    HOSTGROUP = auto()       # hostgroup

    # --- Keywords: Collection ---
    COLLECT = auto()         # collect
    PROCESSES = auto()       # processes
    NETWORK = auto()         # network
    PERSISTENCE = auto()     # persistence
    DRIVERS = auto()         # drivers
    FILE_METADATA = auto()   # file_metadata
    KERNEL_CALLBACKS = auto()  # kernel_callbacks
    HOOK_STATE = auto()      # hook_state
    HIDDEN_PROCESSES = auto()  # hidden_processes
    USERS = auto()             # users

    # --- Keywords: Filters ---
    WHERE = auto()           # WHERE
    IN = auto()              # IN
    AND = auto()             # AND
    WITHIN = auto()          # WITHIN
    WITH = auto()            # WITH
    ACROSS = auto()          # ACROSS
    ALL = auto()             # ALL

    # --- Keywords: Correlation ---
    CORRELATE = auto()       # correlate

    # --- Keywords: Detection ---
    DETECT = auto()          # detect

    # --- Keywords: Output ---
    TIMELINE = auto()        # timeline
    EVIDENCE_GRAPH = auto()  # evidence_graph
    GENERATE = auto()        # generate
    REPORT = auto()          # report
    FORMAT = auto()          # FORMAT

    # --- Time units ---
    SECONDS = auto()         # seconds
    MINUTES = auto()         # minutes
    HOURS = auto()           # hours (e.g., "72h")

    # --- Symbols ---
    LBRACKET = auto()        # [
    RBRACKET = auto()        # ]
    LPAREN = auto()          # (
    RPAREN = auto()          # )
    COMMA = auto()           # ,
    DOT = auto()             # .
    EQUALS = auto()          # ==
    ASSIGN = auto()          # =

    # --- Special ---
    DURATION = auto()        # "72h", "45s", "30m"
    MODIFIED_WITHIN = auto()  # modified_within
    PATH = auto()            # path

    # --- Meta ---
    NEWLINE = auto()
    EOF = auto()
    COMMENT = auto()         # # comment


# Keywords lookup table
KEYWORDS = {
    "case": TokenType.CASE,
    "target": TokenType.TARGET,
    "hostgroup": TokenType.HOSTGROUP,
    "collect": TokenType.COLLECT,
    "processes": TokenType.PROCESSES,
    "network": TokenType.NETWORK,
    "persistence": TokenType.PERSISTENCE,
    "drivers": TokenType.DRIVERS,
    "file_metadata": TokenType.FILE_METADATA,
    "kernel_callbacks": TokenType.KERNEL_CALLBACKS,
    "hook_state": TokenType.HOOK_STATE,
    "hidden_processes": TokenType.HIDDEN_PROCESSES,
    "users": TokenType.USERS,
    "WHERE": TokenType.WHERE,
    "IN": TokenType.IN,
    "AND": TokenType.AND,
    "WITHIN": TokenType.WITHIN,
    "WITH": TokenType.WITH,
    "ACROSS": TokenType.ACROSS,
    "ALL": TokenType.ALL,
    "correlate": TokenType.CORRELATE,
    "detect": TokenType.DETECT,
    "timeline": TokenType.TIMELINE,
    "evidence_graph": TokenType.EVIDENCE_GRAPH,
    "generate": TokenType.GENERATE,
    "report": TokenType.REPORT,
    "FORMAT": TokenType.FORMAT,
    "seconds": TokenType.SECONDS,
    "minutes": TokenType.MINUTES,
    "hours": TokenType.HOURS,
    "modified_within": TokenType.MODIFIED_WITHIN,
    "path": TokenType.PATH,
}


@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:{self.column})"
