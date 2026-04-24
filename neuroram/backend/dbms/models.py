"""DBMS metadata models."""

SYSTEM_METRICS_TABLE = "system_metrics"
PROCESS_METRICS_TABLE = "process_metrics"
PREDICTIONS_TABLE = "prediction_logs"
ALERTS_TABLE = "analysis_reports"
DEVICE_LOGS_TABLE = "device_logs"
MEMORY_LOGS_TABLE = "memory_logs"
ANALYSIS_RESULTS_TABLE = "analysis_reports"

TIMESTAMP_INDEXES = [
    "idx_system_metrics_timestamp",
    "idx_process_metrics_timestamp",
    "idx_prediction_logs_timestamp",
    "idx_analysis_reports_timestamp",
    "idx_device_logs_timestamp",
    "idx_memory_logs_timestamp",
]

PERFORMANCE_INDEXES = [
    "idx_device_logs_device_id",
    "idx_device_logs_event_type",
    "idx_analysis_reports_risk_level",
]
