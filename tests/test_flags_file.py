"""Regression test: flags.json must always be valid, parseable JSON.

Added in response to reviewer feedback on CORE-302 flagging a syntax
error (missing comma / duplicate key) in flags.json. This test fails
loudly if the file ever becomes malformed again.
"""

import json
from pathlib import Path

_FLAGS_FILE = Path(__file__).resolve().parent.parent / "flags.json"


def test_flags_json_is_valid() -> None:
    raw = _FLAGS_FILE.read_text()
    data = json.loads(raw)  # raises if malformed
    assert isinstance(data, dict)
    for key, value in data.items():
        assert isinstance(key, str)
        assert isinstance(value, bool)


def test_flags_json_has_no_duplicate_keys() -> None:
    raw = _FLAGS_FILE.read_text()

    seen: list[str] = []

    def _check_duplicates(pairs):
        for key, _ in pairs:
            assert key not in seen, f"duplicate flag key: {key}"
            seen.append(key)
        return dict(pairs)

    json.loads(raw, object_pairs_hook=_check_duplicates)
