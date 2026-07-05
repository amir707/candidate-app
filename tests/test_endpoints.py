"""Endpoint tests. The governor's reviewer receives per-change coverage
numbers computed against these tests."""

import json
import os

from fastapi.testclient import TestClient

from app import chaos, flags
from app.main import app
from app.payments import SERVICE_FEE_RATE

client = TestClient(app)


def setup_function() -> None:
    # Each test starts healthy; chaos state is process-global.
    chaos.set_area("payments", False)


def _set_flag(monkeypatch, name: str, value: bool) -> None:
    original_all_flags = flags.all_flags()
    patched = dict(original_all_flags)
    patched[name] = value
    monkeypatch.setattr(flags, "all_flags", lambda: patched)


def test_health() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_payments_summary_healthy() -> None:
    resp = client.get("/payments/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["currency"] == "AUD"
    assert body["transactions"] > 0


def test_payments_summary_service_fee_flag_off(monkeypatch) -> None:
    _set_flag(monkeypatch, "payments_service_fee", False)
    resp = client.get("/payments/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert "service_fee" not in body


def test_payments_summary_service_fee_flag_on(monkeypatch) -> None:
    _set_flag(monkeypatch, "payments_service_fee", True)
    resp = client.get("/payments/summary")
    assert resp.status_code == 200
    body = resp.json()
    expected = round(body["captured_total"] * SERVICE_FEE_RATE, 2)
    assert body["service_fee"] == expected


def test_catalog_items() -> None:
    resp = client.get("/catalog/items")
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 3


def test_chaos_requires_token() -> None:
    os.environ["CONFIG_TOKEN"] = "secret-token"
    resp = client.post("/config/chaos", json={"payments": True})
    assert resp.status_code == 403
    # State unchanged after rejected toggle.
    assert client.get("/config/chaos").json()["payments"] is False


def test_chaos_toggle_and_kill_switch() -> None:
    os.environ["CONFIG_TOKEN"] = "secret-token"
    headers = {"X-Config-Token": "secret-token"}

    resp = client.post("/config/chaos", json={"payments": True}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["payments"] is True

    # With chaos on, ~50% of requests fail; over 40 requests we expect
    # both outcomes with overwhelming probability.
    statuses = {client.get("/payments/summary").status_code for _ in range(40)}
    assert statuses == {200, 500}

    # Kill switch: flag off restores health completely.
    client.post("/config/chaos", json={"payments": False}, headers=headers)
    statuses = {client.get("/payments/summary").status_code for _ in range(20)}
    assert statuses == {200}
