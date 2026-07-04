"""Feature flags (core area).

Flags are read from flags.json at request time, so a merged PR that
ships a flagged change can be toggled by editing one file. The governor's
verify step checks that medium+ risk changes gate new behavior behind a
flag defined here.
"""

import json
from pathlib import Path

_FLAGS_FILE = Path(__file__).resolve().parent.parent / "flags.json"


def all_flags() -> dict:
    try:
        return json.loads(_FLAGS_FILE.read_text())
    except FileNotFoundError:
        return {}


def enabled(name: str) -> bool:
    return bool(all_flags().get(name, False))
