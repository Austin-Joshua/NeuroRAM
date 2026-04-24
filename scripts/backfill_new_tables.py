"""Backfill migration from legacy telemetry tables into new logging tables.

Usage:
    python -m scripts.backfill_new_tables
    python -m scripts.backfill_new_tables --db-path "path/to/neuroram.db"
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from neuroram.config.config import CONFIG
from neuroram.config.settings import EXPORTS_DIR

BACKFILL_STATUS_PATH = EXPORTS_DIR / "backfill_status.json"


def _table_columns(cur: sqlite3.Cursor, table_name: str) -> list[str]:
    rows = cur.execute(f"PRAGMA table_info({table_name})").fetchall()
    return [str(row[1]) for row in rows]


def _table_exists(cur: sqlite3.Cursor, table_name: str) -> bool:
    row = cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ? LIMIT 1",
        (table_name,),
    ).fetchone()
    return bool(row)


def _rebuild_legacy_tables(conn: sqlite3.Connection) -> dict[str, int]:
    cur = conn.cursor()
    rebuilt = {"system_metrics_rebuilt": 0, "process_metrics_rebuilt": 0}

    if _table_exists(cur, "system_metrics"):
        system_cols = _table_columns(cur, "system_metrics")
        if "cpu_percent" in system_cols:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS system_metrics_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    ram_total_mb REAL NOT NULL,
                    ram_used_mb REAL NOT NULL,
                    ram_percent REAL NOT NULL,
                    swap_total_mb REAL NOT NULL,
                    swap_used_mb REAL NOT NULL,
                    swap_percent REAL NOT NULL,
                    available_mb REAL NOT NULL
                )
                """
            )
            cur.execute(
                """
                INSERT INTO system_metrics_new (
                    timestamp, ram_total_mb, ram_used_mb, ram_percent,
                    swap_total_mb, swap_used_mb, swap_percent, available_mb
                )
                SELECT timestamp, ram_total_mb, ram_used_mb, ram_percent,
                       swap_total_mb, swap_used_mb, swap_percent, available_mb
                FROM system_metrics
                """
            )
            cur.execute("DROP TABLE system_metrics")
            cur.execute("ALTER TABLE system_metrics_new RENAME TO system_metrics")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp)")
            rebuilt["system_metrics_rebuilt"] = 1

    if _table_exists(cur, "process_metrics"):
        process_cols = _table_columns(cur, "process_metrics")
        if "cpu_percent" in process_cols:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS process_metrics_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    pid INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    username TEXT NOT NULL,
                    rss_mb REAL NOT NULL,
                    vms_mb REAL NOT NULL,
                    memory_percent REAL NOT NULL
                )
                """
            )
            cur.execute(
                """
                INSERT INTO process_metrics_new (
                    timestamp, pid, name, username, rss_mb, vms_mb, memory_percent
                )
                SELECT timestamp, pid, name, username, rss_mb, vms_mb, memory_percent
                FROM process_metrics
                """
            )
            cur.execute("DROP TABLE process_metrics")
            cur.execute("ALTER TABLE process_metrics_new RENAME TO process_metrics")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_process_metrics_timestamp ON process_metrics(timestamp)")
            rebuilt["process_metrics_rebuilt"] = 1

    return rebuilt


def backfill(db_path: str, rebuild_legacy_tables: bool = False) -> dict[str, int]:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()
    rebuilt_stats = {"system_metrics_rebuilt": 0, "process_metrics_rebuilt": 0}

    if rebuild_legacy_tables:
        rebuilt_stats = _rebuild_legacy_tables(conn)

    cur.execute(
        """
        INSERT INTO memory_logs (timestamp, ram_percent, ram_used_mb, swap_percent, available_mb)
        SELECT s.timestamp, s.ram_percent, s.ram_used_mb, s.swap_percent, s.available_mb
        FROM system_metrics s
        WHERE NOT EXISTS (
            SELECT 1 FROM memory_logs m
            WHERE m.timestamp = s.timestamp
        )
        """
    )
    memory_added = cur.rowcount if cur.rowcount is not None else 0

    cur.execute(
        """
        INSERT INTO analysis_reports (
            timestamp, risk_level, causes, dos, donts, model_name, confidence, stability_index
        )
        SELECT a.timestamp,
               a.risk_level,
               a.message,
               'Review optimization suggestions and monitor trends.',
               'Avoid heavy workloads during warning/critical periods.',
               COALESCE(p.model_name, 'rf'),
               0.0,
               a.stability_index
        FROM alerts a
        LEFT JOIN (
            SELECT x1.timestamp, x1.model_name
            FROM predictions x1
            WHERE x1.id = (
                SELECT MAX(x2.id)
                FROM predictions x2
                WHERE x2.timestamp <= x1.timestamp
            )
        ) p
        ON p.timestamp <= a.timestamp
        WHERE NOT EXISTS (
            SELECT 1 FROM analysis_reports r
            WHERE r.timestamp = a.timestamp
              AND r.risk_level = a.risk_level
              AND r.causes = a.message
        )
        """
    )
    analysis_added = cur.rowcount if cur.rowcount is not None else 0

    cur.execute(
        """
        INSERT INTO prediction_logs (timestamp, model_name, predicted_ram_percent, actual_ram_percent)
        SELECT p.timestamp, p.model_name, p.predicted_ram_percent, p.actual_ram_percent
        FROM predictions p
        WHERE NOT EXISTS (
            SELECT 1 FROM prediction_logs pl
            WHERE pl.timestamp = p.timestamp
              AND pl.model_name = p.model_name
              AND pl.predicted_ram_percent = p.predicted_ram_percent
        )
        """
    )
    prediction_added = cur.rowcount if cur.rowcount is not None else 0

    conn.commit()
    conn.close()
    stats = {
        "memory_logs_added": int(memory_added),
        "prediction_logs_added": int(prediction_added),
        "analysis_reports_added": int(analysis_added),
        "system_metrics_rebuilt": int(rebuilt_stats["system_metrics_rebuilt"]),
        "process_metrics_rebuilt": int(rebuilt_stats["process_metrics_rebuilt"]),
    }
    payload = {
        "ran_at_utc": datetime.now(timezone.utc).isoformat(),
        "db_path": str(Path(db_path).resolve()),
        "counts": stats,
    }
    BACKFILL_STATUS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill legacy metrics into new log tables.")
    parser.add_argument("--db-path", default=CONFIG.db_path, help="SQLite db path (default: configured db)")
    parser.add_argument(
        "--rebuild-legacy-tables",
        action="store_true",
        help="Rebuild legacy system/process tables to remove cpu columns before backfill.",
    )
    args = parser.parse_args()
    stats = backfill(args.db_path, rebuild_legacy_tables=bool(args.rebuild_legacy_tables))
    print("BACKFILL_OK")
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()

