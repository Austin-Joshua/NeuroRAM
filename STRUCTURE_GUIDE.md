# NeuroRAM Structure Guide

This guide describes where code lives, what each module owns, and how telemetry flows through the platform.

## Top-level folders

- `webapp/` - React user interface for memory and device intelligence
- `backend/` - stable wrapper layer used by API and external callers
- `neuroram/backend/` - canonical implementation modules
- `neuroram/db/` - SQLite file, exports, and reproducible seed fixtures
- `neuroram/config/` - runtime settings and environment parsing
- `docs/` - API, schema, and reviewer-facing documentation
- `tests/` - unit and integration checks

## Canonical backend domains

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

`backend/OS`, `backend/DBMS`, `backend/MLT`, and `backend/DAA` expose compatibility-safe imports and should delegate to canonical implementation modules. New core behavior should be implemented under `neuroram/backend/*` first.

## API surface

- `api_server.py` is the main FastAPI service.
- `backend/api/api_server.py` is compatibility wrapper glue.
- Primary endpoint: `/api/dashboard`.

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

- For architecture: start at `README.md`, then `docs/API_DOCS.md`, then `api_server.py`.
- For data persistence: read `neuroram/backend/dbms/queries.py` and `database.py`.
- For algorithm behavior: read `neuroram/backend/mlt/` and `neuroram/backend/daa/`.
