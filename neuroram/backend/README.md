# NeuroRAM Backend

This folder contains all backend runtime and domain modules for NeuroRAM.

## Subfolders

- `api/` - FastAPI application and route composition (`/api/dashboard`, health/status)
- `services/` - orchestration helpers for cross-domain workflows
- `os/` - live telemetry collectors and device monitoring
- `dbms/` - SQLite schema, persistence, and query access
- `mlt/` - model training/prediction logic
- `daa/` - risk analysis, stability scoring, optimization guidance

## Rules

- Add new backend behavior here (not in legacy wrapper paths).
- Keep imports canonical: `neuroram.backend.*`.
- Persist data through `dbms/database.py` only.
