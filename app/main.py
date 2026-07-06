"""Candidate app: the substrate service governed by sprint-governor.

Deliberately small: three business endpoints across two "areas"
(payments, catalog) plus core plumbing. Sprint-governor's agents open
real PRs against this repo; its synthetic monitor probes the deployed
service. Design notes live in the sprint-governor repo
(docs/architecture.md).
"""

import os

from fastapi import FastAPI, Header, HTTPException

from app import chaos
from app.catalog import router as catalog_router
from app.payments import router as payments_router

app = FastAPI(title="candidate-app")
app.include_router(payments_router)
app.include_router(catalog_router)


@app.get("/health")
def health() -> dict:
    """Liveness probe. Deliberately independent of chaos state: the
    monitor derives area health from area endpoints, not from /health.

    Includes build metadata (version, build timestamp) read from
    environment variables so operators can confirm which build is
    serving. Safe defaults are used when the environment variables are
    not set.
    """
    return {
        "status": "ok",
        "version": os.environ.get("APP_VERSION", "unknown"),
        "build_time": os.environ.get("BUILD_TIMESTAMP", "unknown"),
    }


@app.get("/config/chaos")
def get_chaos() -> dict:
    """Read-only view of chaos state (unauthenticated; reading is harmless)."""
    return chaos.state()


@app.post("/config/chaos")
def set_chaos(
    payload: dict,
    x_config_token: str | None = Header(default=None),
) -> dict:
    """Protected chaos toggle. This endpoint is the ONLY chaos control
    used in demos — never Cloud Run env vars, which would create a new
    revision and pollute the traffic-shift story. Setting an area to
    false is the manual kill switch that restores health.
    """
    expected = os.environ.get("CONFIG_TOKEN")
    if not expected or x_config_token != expected:
        raise HTTPException(status_code=403, detail="invalid config token")
    for area, enabled in payload.items():
        chaos.set_area(area, bool(enabled))
    return chaos.state()
