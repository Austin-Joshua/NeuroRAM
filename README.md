# NeuroRAM

NeuroRAM is a production-grade memory and device intelligence platform built with React, FastAPI, SQLite, and modular OS/DBMS/MLT/DAA layers.

It continuously collects memory and device telemetry, persists history, runs ML forecasting, performs DAA risk analysis, and serves a structured API for a premium SaaS dashboard.

## Core capabilities

- Real-time RAM and swap telemetry collection
- External device monitoring (storage, dongles, adapters)
- ML-based RAM prediction and prediction-vs-actual tracking
- DAA-based risk classification, stability scoring, and process prioritization
- Structured API for dashboards and integrations
- Reviewer-ready docs, scripts, and CI quality gates

## Architecture

```text
OS Collector -> SQLite DBMS -> MLT Predictor -> DAA Analyzer -> FastAPI -> React UI
```

## Quick start

### Backend

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
cd webapp
npm install
npm run dev
```

Open the dashboard at `http://localhost:5173`.

## Project map

- `webapp/` - React SaaS dashboard
- `backend/` - stable production interface layer
- `neuroram/backend/os/` - telemetry and device collection
- `neuroram/backend/dbms/` - schema, persistence, and query access
- `neuroram/backend/mlt/` - model training and prediction
- `neuroram/backend/daa/` - risk, stability, and recommendations
- `neuroram/db/` - runtime DB, exports, and seed data
- `docs/` - architecture, API, schema, and reporting docs
- `tests/` - backend verification suite

## Data flow

1. OS module collects memory/device state.
2. DBMS stores telemetry and historical logs.
3. MLT predicts near-future memory pressure.
4. DAA scores risk severity and recommended actions.
5. FastAPI serves structured data via `/api/dashboard`.
6. React UI renders dashboards, trends, analysis, and history.

## Documentation index

- `STRUCTURE_GUIDE.md` - repository and module responsibilities
- `docs/API_DOCS.md` - endpoint contract and payload reference
- `docs/database_schema.sql` - documented SQL schema
- `webapp/README.md` - frontend development guide

## Environment

Copy `.env.example` to `.env` and adjust values for polling interval, thresholds, DB filename, and CORS origins.

## One-command helpers

- `start_backend.sh` / `start_backend.ps1`
- `start_frontend.sh` / `start_frontend.ps1`

## CI

GitHub Actions validates backend tests/checklist, frontend lint/type/build, and security/dependency hygiene workflows.
