# NeuroRAM Directory Organization Guide

This project is organized for conceptual clarity under the `neuroram/` package:

- `neuroram/frontend/` for UI and presentation
- `neuroram/backend/` for domain logic grouped by academic subjects
- `neuroram/db/` for physical database files and exports
- `neuroram/config/` for centralized configuration

## Frontend

- `neuroram/frontend/app.py`  
  Streamlit dashboard entrypoint wrapper.

## Backend

- `neuroram/backend/os/`
  - `collector.py`: OS telemetry collection (RAM, CPU, process data)
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

## Compatibility Note

Root files are kept for backward compatibility with existing commands and imports.
You can run either:

- `streamlit run app.py`
- `streamlit run neuroram/frontend/app.py`
