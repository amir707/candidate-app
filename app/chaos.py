"""In-memory chaos state (core area).

Chaos makes an area's endpoints fail probabilistically so the governor's
monitor can detect a real production incident. State is per-instance and
in-memory by design — the Cloud Run service runs with exactly one
instance (min=max=1) so the toggle affects all traffic. The monitor and
this flag never communicate directly; the live service is the medium.
"""

import os

# Failure probability while chaos is enabled for an area.
FAILURE_RATE = 0.5

_state: dict[str, bool] = {
    # CHAOS_PAYMENTS=true lets a deploy start degraded; default healthy.
    "payments": os.environ.get("CHAOS_PAYMENTS", "").lower() == "true",
}


def state() -> dict:
    return dict(_state)


def set_area(area: str, enabled: bool) -> None:
    _state[area] = enabled


def enabled(area: str) -> bool:
    return _state.get(area, False)
