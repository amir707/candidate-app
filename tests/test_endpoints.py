"""Endpoint tests. The governor's reviewer receives per-change coverage
numbers computed against these tests.
"""

import json
import os

from fastapi.testclient import TestClient

from app import chaos, flags
from app.main import app

client = TestClient(app)


def setup_function() -> None:
    # Each test starts healthy; chaos state is process-global.
    chaos.set_area("payments", False)


def test_health() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert "build_time" in body


def test_health_defaults_when_env_unset(monkeypatch) -> None:
    monkeypatch.delenv("APP_VERSION", raising=False)
    monkeypatch.delenv("BUILD_TIMESTAMP", raising=False)
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"status": "ok", "version": "unknown", "build_time": "unknown"}


def test_health_reads_build_metadata_from_env(monkeypatch) -> None:
    monkeypatch.setenv("APP_VERSION", "1.2.3")
    monkeypatch.setenv("BUILD_TIMESTAMP", "2024-01-01T00:00:00Z")
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == "1.2.3"
    assert body["build_time"] == "2024-01-01T00:00:00Z"


def test_payments_summary_healthy() -> None:
    resp = client.get("/payments/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["currency"] == "AUD"
    assert body["transactions"] > 0


def test_payments_summary_service_fee_flag_off(monkeypatch) -> None:
    monkeypatch.setattr(flags, "enabled", lambda name: False)
    resp = client.get("/payments/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert "service_fee" not in body


def test_payments_summary_service_fee_flag_on(monkeypatch) -> None:
    monkeypatch.setattr(flags, "enabled", lambda name: True)
    resp = client.get("/payments/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert "service_fee" in body
    assert body["service_fee"] == round(body["captured_total"] * 0.015, 2)


def test_payments_summary_refund_total_hidden_when_flag_off(monkeypatch) -> None:
    monkeypatch.setattr(flags, "all_flags", lambda: {"payments_refund_totals": False})
    resp = client.get("/payments/summary")
    assert resp.status_code == 200
    assert "refunded_total" not in resp.json()


def test_payments_summary_refund_total_present_when_flag_on(monkeypatch) -> None:
    monkeypatch.setattr(flags, "all_flags", lambda: {"payments_refund_totals": True})
    resp = client.get("/payments/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert "refunded_total" in body
    assert body["refunded_total"] == 342.75
    assert body["currency"] == "AUD"


def test_catalog_items() -> None:
    resp = client.get("/catalog/items")
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 3


def test_catalog_items_unsorted_when_flag_off(monkeypatch) -> None:
    monkeypatch.setattr(
        flags, "all_flags", lambda: {"catalog_items_sorted_by_price": False}
    )
    resp = client.get("/catalog/items")
    assert resp.status_code == 200
    skus = [item["sku"] for item in resp.json()["items"]]
    assert skus == ["MUG-001", "TEA-002", "TEA-001"]


def test_catalog_items_sorted_by_price_ascending_when_flag_on(monkeypatch) -> None:
    monkeypatch.setattr(
        flags, "all_flags", lambda: {"catalog_items_sorted_by_price": True}
    )
    resp = client.get("/catalog/items")
    assert resp.status_code == 200
    prices = [item["price"] for item in resp.json()["items"]]
    assert prices == sorted(prices)
    assert prices[0] == 4.50


def test_catalog_items_count_flag_off(monkeypatch) -> None:
    monkeypatch.setattr(flags, "enabled", lambda name: False)
    resp = client.get("/catalog/items")
    assert resp.status_code == 200
    body = resp.json()
    assert "count" not in body
    assert len(body["items"]) == 3


def test_catalog_items_count_flag_on(monkeypatch) -> None:
    monkeypatch.setattr(flags, "enabled", lambda name: True)
    resp = client.get("/catalog/items")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == len(body["items"])
    assert body["count"] == 3


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
