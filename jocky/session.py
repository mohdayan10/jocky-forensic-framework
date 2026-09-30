"""Shared live session state between terminal demo and web console.

The terminal demo writes here after each key pipeline step.
Django API views read from this file to serve live (non-fixture) data.
Running the demo twice produces different hashes, build IDs, and findings.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

SESSION_FILE = os.environ.get("JOCKY_SESSION_FILE", "/tmp/jocky_session.json")


def read() -> Dict[str, Any]:
    try:
        with open(SESSION_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def write(updates: Dict[str, Any]) -> None:
    current = read()
    current.update(updates)
    with open(SESSION_FILE, "w") as f:
        json.dump(current, f, indent=2, default=str)


def init(case_id: str = "OP-FALCON-01") -> None:
    with open(SESSION_FILE, "w") as f:
        json.dump({
            "case_id": case_id,
            "run_at": datetime.now(timezone.utc).isoformat(),
        }, f, indent=2)
