"""Tests for the refunded_total field on GET /payments/summary.

The field is gated behind the payments_refund_totals feature flag
(default off), per project flag policy for high risk changes.
"""

from fastapi.testclient import TestClient

from app import chaos, flags
from app.main import app

client = TestClient(app)


def setup_function() -> None:
    chaos.set_area("payments", False)


def test_refund_total_absent_when_flag_off(monkeypatch) -> None:
    monkeypatch.setattr(flags, "enabled", lambda name: False)
    resp = client.get("/payments/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert "refunded_total" not in body


def test_refund_total_present_when_flag_on(monkeypatch) -> None:
    monkeypatch.setattr(flags, "enabled", lambda name: name == "payments_refund_totals")
    resp = client.get("/payments/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["currency"] == "AUD"
    assert body["refunded_total"] == 342.75
