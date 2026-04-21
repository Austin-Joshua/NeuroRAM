CREATE TABLE IF NOT EXISTS system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    cpu_percent REAL NOT NULL,
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
    memory_percent REAL NOT NULL,
    cpu_percent REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    model_name TEXT NOT NULL,
    predicted_ram_percent REAL NOT NULL,
    actual_ram_percent REAL
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    message TEXT NOT NULL,
    stability_index REAL NOT NULL
);
