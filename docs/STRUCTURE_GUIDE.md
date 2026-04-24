# NeuroRAM Structure Guide

This guide describes where code lives, what each module owns, and how telemetry flows through the platform.

## Top-level folders

- `frontend/` — React user interface for memory and device intelligence (`src/pages`, `src/components`, `src/services`, `src/styles`)
- `backend/` — FastAPI-facing layer: `OS`, `DBMS`, `MLT`, `DAA`, `api`, and `services` (imports used by the API server)
- `neuroram/backend/` — canonical implementation modules (lowercase `os`, `dbms`, `mlt`, `daa` trees mirror domain logic)
- `db/` — SQLite file (`neuroram.db` by default), exports, migrations, and seed fixtures (path configured via `neuroram/config/settings.py`)
- `neuroram/config/` — runtime settings and environment parsing
- `config/` — additional project-level configuration helpers when present
- `docs/` — API, schema, structure, and reviewer-facing documentation
- `scripts/` — maintenance and backfill utilities
- `tests/` — unit and integration checks

## Canonical backend domains (`neuroram/backend/`)

### `neuroram/backend/os/`

- `collector.py`: memory/device sampling from host OS
- `device_monitor.py`: connection state and event capture
- `system_monitor.py`: persistence orchestration entrypoint

### `neuroram/backend/dbms/`

- `queries.py`: schema and index SQL
- `database.py`: insert/fetch operations and DB pragmas
- `models.py`: index metadata and DB constants

### `neuroram/backend/mlt/`

- `ml_engine.py`: model training lifecycle
- `predictor.py`: next-step prediction
- `trainer.py`: sampling + training utility entrypoint

### `neuroram/backend/daa/`

- `risk_analyzer.py`: risk classification and leak heuristics
- `stability_index.py`: stability score calculation
- `optimizer.py`: process prioritization recommendations

## Wrapper layer (`backend/`)

`backend/OS`, `backend/DBMS`, `backend/MLT`, and `backend/DAA` expose compatibility-safe imports and delegate to the canonical `neuroram/backend/*` modules. New core behavior should land under `neuroram/backend/*` first.

## API surface

- `api_server.py` (repository root) — thin entrypoint for `uvicorn api_server:app`
- `backend/api/api_server.py` — FastAPI application and `/api/dashboard` composition
- Primary endpoint: `GET /api/dashboard`

## Data flow

```text
OS -> DBMS -> MLT -> DAA -> API -> UI
```

1. OS collectors read memory/device telemetry.
2. DBMS stores memory logs, process metrics, predictions, analysis, and device logs.
3. MLT predicts near-future memory pressure from historical records.
4. DAA evaluates risk, stability, and top actions.
5. API composes structured JSON for UI consumers.
6. UI renders dashboard, trends, devices, analysis, and history pages.

## Reviewer guidance

- For architecture: start at `README.md`, then `docs/API_DOCS.md`, then `backend/api/api_server.py`.
- For data persistence: read `neuroram/backend/dbms/queries.py` and `database.py`.
- For algorithm behavior: read `neuroram/backend/mlt/` and `neuroram/backend/daa/`.
