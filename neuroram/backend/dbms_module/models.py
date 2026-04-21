"""DBMS metadata models."""

SYSTEM_METRICS_TABLE = "system_metrics"
PROCESS_METRICS_TABLE = "process_metrics"
PREDICTIONS_TABLE = "predictions"
ALERTS_TABLE = "alerts"

TIMESTAMP_INDEXES = [
    "idx_system_metrics_timestamp",
    "idx_process_metrics_timestamp",
    "idx_predictions_timestamp",
    "idx_alerts_timestamp",
]
