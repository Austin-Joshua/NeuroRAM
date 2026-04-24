# NeuroRAM

**NeuroRAM** is a **predictive memory management system** with device intelligence: live RAM and swap telemetry, SQLite history, ML forecasting (RandomForest), and DAA risk analysis—served by **FastAPI** and a **React** dashboard.

## GitHub “About” metadata (improves search & evaluation)

The repository is **public** with default branch **`main`**. GitHub’s **description** and **topics** are not stored in git; set them once on the repo homepage (gear icon **About** → **Edit repository details**) or with the CLI after `gh auth login`:

**Suggested short description (copy-paste):**

> NeuroRAM — predictive memory management system with React + FastAPI: RAM/swap telemetry, device storage insights, ML prediction, and DAA risk scoring (SQLite).

**Suggested topics (add each tag):**  
`react` · `fastapi` · `typescript` · `sqlite` · `machine-learning` · `system-monitoring` · `memory-management` · `telemetry` · `neuroram`

```bash
gh repo edit Austin-Joshua/NeuroRAM --description "NeuroRAM: predictive memory management system — React, FastAPI, SQLite, ML, DAA."
gh repo edit Austin-Joshua/NeuroRAM --add-topic react --add-topic fastapi --add-topic machine-learning --add-topic system-monitoring --add-topic sqlite --add-topic typescript
```

## For evaluators: GitHub visibility and access

**Status check (no login required):** the GitHub API reports this repository as **public** (`"private": false`) with default branch **`main`**. Example check (any machine):

```bash
curl -s https://api.github.com/repos/Austin-Joshua/NeuroRAM
```

In the JSON response, `"private": false` means the repository is **public**, and `"default_branch": "main"` confirms the default branch. Raw files are reachable anonymously, e.g. `README.md` at  
`https://raw.githubusercontent.com/Austin-Joshua/NeuroRAM/main/README.md`.

**If a browser still asks you to sign in before showing the Code tab:** use an **incognito/private** window, confirm the URL is exactly `https://github.com/Austin-Joshua/NeuroRAM`, and rule out VPN, corporate proxies, or extensions blocking `github.com`. The HTML landing page can look like a login prompt even when the repo is public.

**If you ever need to switch visibility yourself (forks, new repos):** GitHub → **Settings** → **General** → **Danger Zone** → **Change repository visibility** → **Public**; confirm **Default branch** is **`main`**. With [GitHub CLI](https://cli.github.com/) after `gh auth login`: `gh repo edit OWNER/REPO --visibility public`.

---

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
OS → DB → ML → DAA → API → UI
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

## API quick check

With the backend running on port 8000:

```bash
curl -s http://127.0.0.1:8000/api/dashboard | python -m json.tool | head -n 40
```

The response is JSON with top-level keys: `ready`, `timestamp_utc`, `metrics`, `devices`, `trends`, `analysis`, and `recommendations`. See `docs/API_DOCS.md` for the full contract.

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

- `STRUCTURE_GUIDE.md` (repository root) and `docs/STRUCTURE_GUIDE.md` — folder roles, modules, data flow
- `docs/README.md` - documentation table of contents
- `docs/SAMPLE_DATA.md` - sample JSON, SQLite notes, how to populate data for review
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
