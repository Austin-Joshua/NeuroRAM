# NeuroRAM

NeuroRAM is a production-grade memory and device intelligence platform built with React, FastAPI, SQLite, and modular OS/DBMS/MLT/DAA layers.

It continuously collects memory and device telemetry, persists history, runs ML forecasting, performs DAA risk analysis, and serves a structured API for a premium SaaS dashboard.

## Features

- Real-time RAM and swap telemetry (memory-focused; no CPU dashboard metrics)
- External device intelligence: storage breakdown, usage, connection timeline, activity charts
- ML (RandomForest) next-step RAM prediction with prediction-vs-actual tracking
- DAA risk classification, stability index, greedy process prioritization, do / don’t guidance
- Structured `GET /api/dashboard` contract: `metrics`, `devices`, `trends`, `analysis`, `recommendations`
- Premium React UI: liquid-glass layout, KPI trends, annotated charts with plain-language insights
- SQLite persistence with WAL-friendly access patterns
- GitHub Actions: tests, checklist, frontend lint/build/typecheck, CodeQL, Dependabot
- Docs: architecture, API reference, schema SQL, screenshot placeholders, start scripts

## Architecture

```text
OS Collector -> SQLite DBMS -> MLT Predictor -> DAA Analyzer -> FastAPI -> React UI
```

## Quick start

### Backend

The SQLite file and seed data live under `db/` at the repository root (see `neuroram/config/settings.py`). Run the API from the repository root so imports resolve.

```bash
python -m venv .venv
# Windows
.venv\Scripts\Activate.ps1
# Linux/macOS
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api_server:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the dashboard at `http://localhost:5173`.

## Project map

- `frontend/` - React SaaS dashboard
- `backend/` - stable production interface layer
- `neuroram/backend/os/` - telemetry and device collection
- `neuroram/backend/dbms/` - schema, persistence, and query access
- `neuroram/backend/mlt/` - model training and prediction
- `neuroram/backend/daa/` - risk, stability, and recommendations
- `db/` - SQLite database file, exports, migrations, and seed data
- `docs/` - architecture, API, schema, and reporting docs
- `tests/` - backend verification suite

## Data flow

1. OS module collects memory/device state.
2. DBMS stores telemetry and historical logs.
3. MLT predicts near-future memory pressure.
4. DAA scores risk severity and recommended actions.
5. FastAPI serves structured data via `/api/dashboard`.
6. React UI renders dashboards, trends, analysis, and history.

## Screenshots

Capture the running UI and save under `docs/screenshots/` (see `docs/screenshots/README.md` for naming). Until then, placeholders:

- Dashboard: KPI strip + RAM / prediction charts with spike annotations and insight copy
- Devices: connected device cards, activity chart, visual timeline + table
- Analysis: risk badge, narrative paragraph, what/why/how serious, do’s / don’ts cards
- History: searchable log table

## Documentation index

- `docs/README.md` - documentation table of contents
- `docs/STRUCTURE_GUIDE.md` - repository and module responsibilities
- `docs/API_DOCS.md` - endpoint contract and payload reference
- `docs/database_schema.sql` - documented SQL schema
- `docs/screenshots/README.md` - screenshot naming and demo guidance
- `frontend/README.md` - frontend development guide

## Environment

Copy `.env.example` to `.env` and adjust values for polling interval, thresholds, DB filename, and CORS origins.

## One-command helpers

- `start_backend.sh` / `start_backend.ps1`
- `start_frontend.sh` / `start_frontend.ps1`

## CI

GitHub Actions validates backend tests/checklist, frontend lint/type/build, and security/dependency hygiene workflows.
