# NeuroRAM Directory Organization Guide

This project is organized for conceptual clarity under modular layers:

- `webapp/` for React frontend UI
- `neuroram/backend/` for canonical domain logic grouped by academic subjects
- `backend/` for production-facing wrapper layout (`os`, `dbms`, `mlt`, `daa`, `api`, `services`)
- `neuroram/db/` for physical database files and exports
- `neuroram/config/` and `config/` for centralized settings and wrappers

## Frontend (React)

- `webapp/src/pages/` — route-like page modules:
  - `Dashboard.tsx`
  - `Memory.tsx`
  - `Devices.tsx`
  - `Trends.tsx`
  - `Analysis.tsx`
  - `History.tsx`
- `webapp/src/components/` — reusable UI building blocks (`layout`, `cards`, `charts`, `tables`)
- `webapp/src/hooks/useDashboard.ts` — polling + state management
- `webapp/src/services/api.ts` — typed API payload and fetch service
- `webapp/src/App.tsx` — multi-page shell with collapsible sidebar navigation

## Canonical Backend

- `neuroram/backend/os/`
  - `collector.py`: OS telemetry collection (RAM, swap, process-memory data)
  - `device_monitor.py`: external device detection and event generation
  - `system_monitor.py`: collection + persistence orchestration
- `neuroram/backend/dbms/`
  - `database.py`: SQLite schema, inserts, and queries
  - `models.py`: DB metadata definitions
  - `queries.py`: SQL statements
- `neuroram/backend/mlt/`
  - `ml_engine.py`: model training and persistence
  - `predictor.py`: inference for next RAM usage
  - `trainer.py`: CLI sampling + training flow
- `neuroram/backend/daa/`
  - `optimizer.py`: process ranking and greedy suggestions
  - `risk_analyzer.py`: risk classification and leak heuristic
  - `stability_index.py`: stability scoring

## Production Wrapper Backend

- `backend/os`, `backend/dbms`, `backend/mlt`, `backend/daa` — non-breaking wrappers to canonical modules
- `backend/api/api_server.py` — wrapper entrypoint exposing FastAPI app
- `backend/services/pipeline.py` — orchestrator-facing imports for OS -> DBMS -> MLT -> DAA flow
- `config/config.py`, `config/settings.py` — top-level wrappers to canonical config

## Compatibility Note

Legacy `neuroram/backend/*_module/` packages and top-level wrappers re-export the same APIs as canonical modules. Prefer canonical `neuroram.backend.<domain>` for new code and use `backend/` layout for production readability.

## Commands

- `uvicorn api_server:app --reload --port 8000` — FastAPI backend
- `cd webapp && npm run dev` — React dashboard
- `python -m neuroram.backend.mlt.trainer` — collect samples and train models
