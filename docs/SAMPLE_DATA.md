# Sample data for reviewers

NeuroRAM persists live telemetry in SQLite under `db/` (see `neuroram/config/settings.py`). The committed repository does **not** include a `*.db` file (ignored by `.gitignore`) so clones stay small.

## Reference dashboard JSON

File: `db/seed_data/dashboard_sample.json`

- Shaped like a **subset** of `GET /api/dashboard` for documentation and UI prototyping.
- Not loaded automatically by the API; use it as a contract reference or to mock responses during frontend development.

## Getting a populated database quickly

1. Start the backend from the repository root: `uvicorn api_server:app --reload --port 8000`
2. Let the background pipeline run for several cycles (it inserts OS → DB samples automatically).
3. Optional: run `python -m scripts.backfill_new_tables` if you need legacy tables filled (see script help).

After telemetry exists, `GET /api/dashboard` returns `ready: true` with full `metrics`, `devices`, `trends`, `analysis`, and `recommendations`.
