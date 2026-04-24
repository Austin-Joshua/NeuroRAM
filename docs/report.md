# NeuroRAM — Intelligent Predictive Memory Optimization System

## Abstract

NeuroRAM is an intelligent memory optimization framework designed to predict and prevent memory pressure in real time. The system integrates operating-system telemetry collection, database persistence, machine learning forecasting, risk analysis, and algorithmic optimization into a single decision-support dashboard. NeuroRAM continuously captures system and process-level metrics, stores them in a structured DBMS, predicts near-future RAM usage using a Random Forest model (and optional LSTM), detects potential memory leak patterns through heuristic growth checks, classifies risk levels, and computes a quantitative stability index from 0 to 100. The output includes actionable recommendations generated through a priority scoring and greedy selection strategy. Experimental deployment demonstrates that NeuroRAM enables earlier warning signals than threshold-only monitoring, improves interpretability through multi-factor stability scoring, and supports academic understanding across OS, DBMS, ML, and DAA domains.

## Introduction

Modern computing environments execute multiple concurrent processes with highly variable memory behavior. Conventional monitors display current RAM usage but do not provide predictive intelligence or optimization guidance. This limitation can lead to delayed mitigation, performance degradation, and system instability during high-pressure workloads.

NeuroRAM addresses this gap by combining monitoring and prediction in one architecture. It not only observes memory usage but also forecasts upcoming trends, detects anomalies, classifies operational risk, and suggests practical mitigation steps. The system is designed for educational and practical usage, with a modular implementation that maps directly to core computer science subjects.

## Problem Statement

Existing resource monitors are predominantly reactive. They report current states but rarely:

- predict upcoming memory pressure,
- maintain analyzable historical records,
- provide risk-aware graded alerts, and
- generate algorithm-driven optimization suggestions.

Hence, a proactive and explainable memory optimization system is needed to improve reliability and support timely intervention.

## Literature Survey

1. **System Monitoring Tools**: Utilities such as Task Manager and `top` provide process snapshots but limited predictive analysis.
2. **Time-series Forecasting for Resource Usage**: Prior work applies regression and neural networks for workload forecasting, but often without integrated risk modeling.
3. **Memory Leak Detection Research**: Leak detection frequently relies on profiling instrumentation; lightweight heuristic methods are valuable for runtime monitoring.
4. **Decision-support Dashboards**: Interactive visualization platforms improve human-in-the-loop operations when paired with interpretable indicators.

Research gap: limited unified systems combining OS telemetry, historical DB design, ML forecasting, anomaly heuristics, and algorithmic recommendation in a single educationally complete platform.

## System Design

NeuroRAM follows a modular pipeline:

1. **Collection Layer** (`neuroram/backend/os/collector.py`)
2. **Persistence Layer** (`neuroram/backend/dbms/database.py`)
3. **ML Layer** (`neuroram/backend/mlt/ml_engine.py`, `neuroram/backend/mlt/predictor.py`)
4. **Analytics Layer** (`neuroram/backend/daa/risk_analyzer.py`, `neuroram/backend/daa/stability_index.py`)
5. **Optimization Layer** (`neuroram/backend/daa/optimizer.py`)
6. **Presentation Layer** (`neuroram/frontend/dashboard.py`, entry via root `app.py` or `neuroram/frontend/app.py`)

Each layer is loosely coupled, enabling independent testing and incremental upgrades.

## Architecture

1. `psutil` collects memory/CPU/process features.
2. SQLite stores `system_metrics`, `process_metrics`, `predictions`, and `alerts`.
3. Feature engineering transforms historical telemetry into supervised-learning inputs.
4. Model predicts next RAM utilization.
5. Risk analyzer combines threshold logic and leak heuristic.
6. Stability engine computes a bounded health score.
7. Greedy optimizer ranks and selects high-impact process interventions.
8. Streamlit dashboard visualizes telemetry, forecasts, risk, and recommendations.

## Modules

- **`neuroram/backend/os/collector.py`**: Gathers RAM, swap, available memory, and top process usage.
- **`neuroram/backend/dbms/database.py`**: Auto-creates schema, inserts observations, and provides query APIs.
- **`neuroram/backend/mlt/ml_engine.py`**: Trains Random Forest; supports optional LSTM using TensorFlow.
- **`neuroram/backend/mlt/predictor.py`**: Produces next-step RAM prediction from latest engineered features.
- **`neuroram/backend/daa/risk_analyzer.py`**: Leak heuristic and risk classification.
- **`neuroram/backend/daa/stability_index.py`**: Normalized system health indicator.
- **`neuroram/backend/daa/optimizer.py`**: Process priority score and greedy recommendations.
- **`neuroram/frontend/dashboard.py`**: Streamlit dashboard UI.
- **`neuroram/config/config.py`**: Centralized configuration and thresholds.

## Implementation

### OS Layer

- Memory and process telemetry are collected using `psutil`.
- Metrics include RAM percentage, swap behavior, available memory, process RSS/VMS, and per-process CPU.

### DBMS Layer

- SQLite ensures lightweight persistence and portability.
- Normalized table design separates system-level, process-level, predictive, and alert records.

### ML Layer

- Feature engineering:
  - lag features (`ram_lag_1`, `ram_lag_2`)
  - rolling mean (`ram_roll_mean_3`)
  - temporal context (`hour`, `minute`)
- Primary model: `RandomForestRegressor`.
- Optional model: `LSTM`.
- Model artifacts are serialized for reuse.

### DAA Layer

- Process ranking uses sorting with priority score:
  - `priority_score = 0.7 * rss_mb + 0.3 * cpu_percent`
- Greedy top-k selection produces immediate recommendations.

### UI Layer

- Streamlit app with dark theme and card-oriented visual structure.
- Plotly charts for real-time trends and prediction-vs-actual analysis.
- Sidebar controls for thresholds, refresh behavior, and model selection.

## Results

Observed outcomes from prototype execution:

- Continuous historical memory record supports trend analysis.
- Predictive model gives early warning against upcoming pressure.
- Leak heuristic identifies suspicious monotonic growth trajectories.
- Multi-level risk classification improves operational clarity over binary alerts.
- Stability index condenses system health into a single interpretable score.
- Greedy recommendations prioritize high-impact process-level mitigation.

## Future Scope

- Multi-host distributed telemetry collection
- Online/incremental learning for adaptive models
- Advanced anomaly detection (Isolation Forest, autoencoders)
- Root-cause tagging using process signatures
- Policy-driven optimizer with user-defined constraints
- Container and cloud orchestration integration

## Conclusion

NeuroRAM demonstrates a complete and academically aligned intelligent memory management framework. By integrating OS data collection, DBMS persistence, ML forecasting, heuristic anomaly detection, algorithmic optimization, and interactive visualization, the system shifts memory management from reactive monitoring to proactive decision support. The project satisfies practical performance needs while strongly reinforcing interdisciplinary concepts across OS, DBMS, ML, and DAA.

## IEEE References

[1] G. Grolemund and H. Wickham, *R for Data Science*. Sebastopol, CA, USA: O’Reilly Media, 2017.  
[2] F. Pedregosa *et al.*, “Scikit-learn: Machine Learning in Python,” *J. Mach. Learn. Res.*, vol. 12, pp. 2825–2830, 2011.  
[3] A. Géron, *Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow*, 3rd ed. Sebastopol, CA, USA: O’Reilly Media, 2022.  
[4] B. McKinney, “Data Structures for Statistical Computing in Python,” in *Proc. 9th Python Sci. Conf.*, Austin, TX, USA, 2010, pp. 56–61.  
[5] J. Ousterhout, *A Philosophy of Software Design*, 2nd ed. Palo Alto, CA, USA: Yaknyam Press, 2021.  
[6] A. S. Tanenbaum and H. Bos, *Modern Operating Systems*, 4th ed. Upper Saddle River, NJ, USA: Pearson, 2014.  
[7] R. S. Sutton and A. G. Barto, *Reinforcement Learning: An Introduction*, 2nd ed. Cambridge, MA, USA: MIT Press, 2018.  
[8] L. Breiman, “Random Forests,” *Mach. Learn.*, vol. 45, no. 1, pp. 5–32, 2001.
