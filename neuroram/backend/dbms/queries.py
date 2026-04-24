"""SQL queries used by the DBMS module."""

CREATE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    ram_total_mb REAL NOT NULL,
    ram_used_mb REAL NOT NULL,
    ram_percent REAL NOT NULL,
    swap_total_mb REAL NOT NULL,
    swap_used_mb REAL NOT NULL,
    swap_percent REAL NOT NULL,
    available_mb REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS process_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    pid INTEGER NOT NULL,
    name TEXT NOT NULL,
    username TEXT NOT NULL,
    rss_mb REAL NOT NULL,
    vms_mb REAL NOT NULL,
    memory_percent REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS prediction_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    model_name TEXT NOT NULL,
    predicted_ram_percent REAL NOT NULL,
    actual_ram_percent REAL
);

CREATE TABLE IF NOT EXISTS analysis_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    causes TEXT NOT NULL,
    dos TEXT NOT NULL,
    donts TEXT NOT NULL,
    model_name TEXT NOT NULL,
    confidence REAL NOT NULL,
    stability_index REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS device_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    device_type TEXT NOT NULL,
    device_name TEXT NOT NULL,
    device_id TEXT NOT NULL,
    mountpoint TEXT,
    capacity_bytes INTEGER,
    used_bytes INTEGER,
    usage_percent REAL,
    source_os TEXT NOT NULL,
    is_connected INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS memory_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    ram_percent REAL NOT NULL,
    ram_used_mb REAL NOT NULL,
    swap_percent REAL NOT NULL,
    available_mb REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp
ON system_metrics(timestamp);

CREATE INDEX IF NOT EXISTS idx_process_metrics_timestamp
ON process_metrics(timestamp);

CREATE INDEX IF NOT EXISTS idx_prediction_logs_timestamp
ON prediction_logs(timestamp);

CREATE INDEX IF NOT EXISTS idx_analysis_reports_timestamp
ON analysis_reports(timestamp);

CREATE INDEX IF NOT EXISTS idx_device_logs_timestamp
ON device_logs(timestamp);

CREATE INDEX IF NOT EXISTS idx_device_logs_device_id
ON device_logs(device_id);

CREATE INDEX IF NOT EXISTS idx_device_logs_event_type
ON device_logs(event_type);

CREATE INDEX IF NOT EXISTS idx_memory_logs_timestamp
ON memory_logs(timestamp);

CREATE INDEX IF NOT EXISTS idx_analysis_reports_risk_level
ON analysis_reports(risk_level);
"""
