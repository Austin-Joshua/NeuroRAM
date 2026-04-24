# NeuroRAM Canonical Workspace

This `neuroram/` directory is the single source of truth for the application codebase.

## Ownership

- `frontend/` - React + Vite web application (primary presentation UI)
- `backend/` - FastAPI and domain logic (`api`, `services`, `os`, `dbms`, `mlt`, `daa`)
- `config/` - runtime configuration and environment parsing
- `streamlit/` - optional Streamlit presentation UI

## Runtime flow

`os -> dbms -> mlt -> daa -> api -> frontend`

## Run paths

- Frontend: `cd neuroram/frontend && npm run dev`
- Backend API entrypoint: `uvicorn api_server:app --reload --port 8000` (from repo root)
- Optional Streamlit: `streamlit run neuroram/streamlit/app.py`
