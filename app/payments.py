"""Payments area. Files matching app/payments* map to area `payments`
in sprint-governor's area map; changes here carry payment-path risk."""

import random

from fastapi import APIRouter, HTTPException

from app import chaos, flags

router = APIRouter(prefix="/payments")

SERVICE_FEE_RATE = 0.015


@router.get("/summary")
def payments_summary() -> dict:
    # Chaos injection point: while chaos is on for payments, roughly
    # half of requests fail, which the governor's monitor must detect
    # as an incident from the outside.
    if chaos.enabled("payments") and random.random() < chaos.FAILURE_RATE:
        raise HTTPException(status_code=500, detail="payments backend error")
    captured_total = 15734.50
    body = {
    summary = {
        "currency": "AUD",
        "captured_total": captured_total,
        "pending_total": 1201.00,
        "transactions": 214,
    }
    if flags.enabled("payments_service_fee"):
        body["service_fee"] = round(captured_total * SERVICE_FEE_RATE, 2)
    return body
    if flags.enabled("payments_refund_totals"):
        summary["refunded_total"] = 342.75
    return summary
