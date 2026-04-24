# NeuroRAM — Intelligent Predictive Memory Optimization System

NeuroRAM is an AI-driven memory observability and prediction platform that combines OS-level data collection, DBMS persistence, ML forecasting, risk analytics, and algorithmic optimization in a single Streamlit dashboard.

## Features

- Real-time memory and CPU monitoring using `psutil`
- Per-process memory analysis and ranking
- Historical storage in SQLite with auto table creation
- ML prediction of next-step RAM usage (`RandomForestRegressor`, optional LSTM)
- Memory leak heuristic based on sustained monotonic growth
- Risk classification: `NORMAL`, `WARNING`, `CRITICAL`, `EMERGENCY`
- System stability index from `0-100`
- Greedy recommendation engine for process-level optimization
- Modern dark-themed interactive dashboard with Plotly graphs

## Folder Structure

```text
NeuroRAM/
├── neuroram/
│   ├── frontend/
│   │   ├── app.py            # Streamlit entry (imports dashboard)
│   │   ├── dashboard.py      # full dashboard implementation
│   │   ├── ui_components.py
│   │   ├── styles.css
│   │   ├── components/
│   │   └── assets/
│   ├── backend/
│   │   ├── os/
│   │   │   ├── collector.py
│   │   │   └── system_monitor.py
│   │   ├── dbms/
│   │   │   ├── database.py
│   │   │   ├── models.py
│   │   │   └── queries.py
│   │   ├── mlt/
│   │   │   ├── ml_engine.py
│   │   │   ├── predictor.py
│   │   │   └── trainer.py
│   │   └── daa/
│   │       ├── optimizer.py
│   │       ├── risk_analyzer.py
│   │       └── stability_index.py
│   ├── db/
│   │   ├── neuroram.db
│   │   ├── migrations/
│   │   ├── seed_data/
│   │   └── exports/
│   ├── config/
│   │   ├── config.py
│   │   └── settings.py
│   └── docs/
│       ├── README.md
│       ├── report/
│       ├── ppt/
│       └── diagrams/
├── tests/
│   ├── test_os.py
│   ├── test_dbms.py
│   ├── test_mlt.py
│   └── test_daa.py
├── app.py                      # thin shim → neuroram.frontend.dashboard
├── requirements.txt
└── docs/
    ├── report.md
    ├── presentation.md
    └── viva_qa.md
```

## Setup

1. Create and activate virtual environment:
   - Windows PowerShell:
     - `python -m venv .venv`
     - `.venv\Scripts\Activate.ps1`
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Optional LSTM support:
   - `pip install tensorflow`
4. Optional runtime overrides:
   - Copy `.env.example` to `.env` and adjust thresholds, intervals, DB filename, and CORS origins.

## Run

- Start dashboard:
  - `streamlit run app.py` (root shim; same UI as below)
  - or `streamlit run neuroram/frontend/app.py`
- React makeover frontend (recommended public UI):
  - API server: `uvicorn api_server:app --reload --port 8000`
  - React app: `cd webapp && npm install && npm run dev`
  - Open the Vite URL (usually `http://localhost:5173`)
- Sample data + train RF/LSTM entry flow:
  - `python -m neuroram.backend.mlt.trainer`

## Usage Flow

1. Launch the dashboard.
2. NeuroRAM collects real-time system and process metrics.
3. Data is stored in `neuroram/db/neuroram.db`.
4. When enough data exists, the model trains and predicts next RAM usage.
5. Risk level, leak alerts, and optimization recommendations are generated.

## Database Schema

- `memory_logs`: periodic RAM/swap samples
- `process_metrics`: top memory-consuming process snapshots
- `prediction_logs`: predicted vs actual RAM percentage
- `analysis_reports`: risk level, causes, dos/donts, stability index
- `device_logs`: external device snapshots + connect/disconnect events

## Academic Mapping

- **OS Concepts**: virtual memory, paging pressure, process management, resource allocation
- **DBMS Concepts**: schema normalization, persistence, query design, table-level separation
- **ML Concepts**: feature engineering, train/test split, regression models, model serialization
- **DAA Concepts**: sorting-based process ranking, greedy top-k optimization strategy

## Notes

- The app is non-destructive and does not terminate processes automatically.
- Recommendations are advisory and human-in-the-loop.
