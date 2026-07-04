# candidate-app

A candidate app for [agentic-sdlc](https://github.com/amir707/agentic-sdlc):
a deliberately simple FastAPI app that Agentic SDLC's coding agents modify
through real GitHub PRs, and that its synthetic monitor probes in production
(Cloud Run). It is small on purpose — the interesting system is the governance
layer in the agentic-sdlc repo.

## Endpoints

| Endpoint | Area | Notes |
|---|---|---|
| `GET /health` | core | liveness; independent of chaos |
| `GET /payments/summary` | payments | chaos injection point |
| `GET /catalog/items` | catalog | |
| `GET /config/chaos` | core | read chaos state |
| `POST /config/chaos` | core | protected by `X-Config-Token` header (`CONFIG_TOKEN` env) |

Areas: files under `app/payments*` are area `payments`, `app/catalog*` are
`catalog`, everything else `core`. Agentic SDLC's deterministic diff
analysis uses this map.

## Feature flags

`flags.json` at the repo root, read per request (`app/flags.py`). The governor
requires medium+ risk changes to gate new behavior behind a flag.

## Chaos

`POST /config/chaos {"payments": true}` makes `/payments/summary` fail ~50% of
requests, which the Agentic SDLC's monitor detects from the outside as an incident.
`{"payments": false}` is the kill switch. Chaos is toggled only via this
endpoint (never env vars — a Cloud Run env change would create a new revision).
`CHAOS_PAYMENTS=true` can start a deploy degraded.

## Run locally

```bash
pip install -r requirements-dev.txt
uvicorn app.main:app --reload   # http://127.0.0.1:8000
pytest
```

## Deploy

Deployed by sprint-governor's `tools/deploy.py` (Cloud Run, one instance,
tagged preprod revisions, traffic-shift releases). See that repo's README.
