"""SQLite persistence layer for memory+device focused NeuroRAM."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Dict, Iterable, Sequence

import pandas as pd

from backend.DBMS.models import PERFORMANCE_INDEXES, TIMESTAMP_INDEXES
from backend.DBMS.queries import CREATE_SCHEMA_SQL
from neuroram.config.config import CONFIG


class DatabaseManager:
    def __init__(self, db_path: str = CONFIG.db_path) -> None:
        self.db_path = db_path
        self._legacy_schema: dict[str, bool] = {}
        self._init_db()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
        finally:
            conn.commit()
            conn.close()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript(CREATE_SCHEMA_SQL)
            self._legacy_schema = self._detect_legacy_schema(conn)

    @staticmethod
    def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
        rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {str(row[1]) for row in rows}

    def _detect_legacy_schema(self, conn: sqlite3.Connection) -> dict[str, bool]:
        system_cols = self._table_columns(conn, "system_metrics")
        process_cols = self._table_columns(conn, "process_metrics")
        return {
            "system_has_cpu_column": "cpu_percent" in system_cols,
            "process_has_cpu_column": "cpu_percent" in process_cols,
            "memory_logs_exists": bool(self._table_columns(conn, "memory_logs")),
            "process_metrics_exists": bool(process_cols),
        }

    def insert_system_metric(self, row: Dict[str, float]) -> None:
        # Legacy compatibility: preserve caller API while storing only memory-focused data.
        # If a legacy DB is attached, memory_logs remains the canonical write target.
        if not self._legacy_schema.get("memory_logs_exists", False):
            self._init_db()
        self.insert_memory_log(
            timestamp=str(row["timestamp"]),
            ram_percent=float(row["ram_percent"]),
            ram_used_mb=float(row["ram_used_mb"]),
            swap_percent=float(row["swap_percent"]),
            available_mb=float(row["available_mb"]),
        )

    def insert_process_metrics(self, rows: Iterable[Dict[str, float]]) -> None:
        # Never write into legacy cpu-bound process_metrics layouts.
        if self._legacy_schema.get("process_has_cpu_column", True):
            return
        payload = list(rows)
        if not payload:
            return
        with self._conn() as conn:
            conn.executemany(
                """
                INSERT INTO process_metrics (
                    timestamp, pid, name, username, rss_mb, vms_mb, memory_percent
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        row["timestamp"],
                        row["pid"],
                        row["name"],
                        row["username"],
                        row["rss_mb"],
                        row["vms_mb"],
                        row["memory_percent"],
                    )
                    for row in payload
                ],
            )

    def insert_prediction_log(
        self,
        timestamp: str,
        model_name: str,
        predicted_ram_percent: float,
        actual_ram_percent: float | None,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO prediction_logs (timestamp, model_name, predicted_ram_percent, actual_ram_percent)
                VALUES (?, ?, ?, ?)
                """,
                (timestamp, model_name, predicted_ram_percent, actual_ram_percent),
            )

    def insert_analysis_report(
        self,
        timestamp: str,
        risk_level: str,
        causes: str,
        dos: str,
        donts: str,
        model_name: str,
        confidence: float,
        stability_index: float,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO analysis_reports (
                    timestamp, risk_level, causes, dos, donts, model_name, confidence, stability_index
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (timestamp, risk_level, causes, dos, donts, model_name, confidence, stability_index),
            )

    def insert_device_logs(self, rows: Sequence[Dict[str, object]]) -> None:
        if not rows:
            return
        with self._conn() as conn:
            conn.executemany(
                """
                INSERT INTO device_logs (
                    timestamp, event_type, device_type, device_name, device_id, mountpoint,
                    capacity_bytes, used_bytes, usage_percent, source_os, is_connected
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        row.get("timestamp"),
                        row.get("event_type", "snapshot"),
                        row.get("device_type", "unknown"),
                        row.get("device_name", "unknown"),
                        row.get("device_id", "unknown"),
                        row.get("mountpoint"),
                        row.get("capacity_bytes"),
                        row.get("used_bytes"),
                        row.get("usage_percent"),
                        row.get("source_os", "unknown"),
                        int(bool(row.get("is_connected", True))),
                    )
                    for row in rows
                ],
            )

    def insert_memory_log(
        self,
        timestamp: str,
        ram_percent: float,
        ram_used_mb: float,
        swap_percent: float,
        available_mb: float,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO memory_logs (timestamp, ram_percent, ram_used_mb, swap_percent, available_mb)
                VALUES (?, ?, ?, ?, ?)
                """,
                (timestamp, ram_percent, ram_used_mb, swap_percent, available_mb),
            )

    # Backward-compatible method names
    def insert_prediction(self, timestamp: str, model_name: str, predicted_ram_percent: float, actual_ram_percent: float | None) -> None:
        self.insert_prediction_log(timestamp, model_name, predicted_ram_percent, actual_ram_percent)

    def insert_alert(self, timestamp: str, risk_level: str, message: str, stability_index: float) -> None:
        self.insert_analysis_report(
            timestamp=timestamp,
            risk_level=risk_level,
            causes=message,
            dos="Follow recommendation panel.",
            donts="Avoid memory-heavy actions under risk.",
            model_name="rf",
            confidence=0.0,
            stability_index=stability_index,
        )

    def insert_analysis_result(
        self,
        timestamp: str,
        risk_level: str,
        causes: str,
        dos: str,
        donts: str,
        model_name: str,
        confidence: float,
        stability_index: float,
    ) -> None:
        self.insert_analysis_report(timestamp, risk_level, causes, dos, donts, model_name, confidence, stability_index)

    def fetch_system_metrics(self, limit: int = 300) -> pd.DataFrame:
        query = """
        SELECT timestamp, ram_percent, ram_used_mb, swap_percent, available_mb
        FROM memory_logs ORDER BY id DESC LIMIT ?
        """
        with self._conn() as conn:
            df = pd.read_sql_query(query, conn, params=(limit,))
        return df.sort_values("timestamp")

    def fetch_recent_process_metrics(self, limit: int = 50) -> pd.DataFrame:
        query = """
        SELECT timestamp, pid, name, username, rss_mb, vms_mb, memory_percent
        FROM process_metrics ORDER BY id DESC LIMIT ?
        """
        with self._conn() as conn:
            return pd.read_sql_query(query, conn, params=(limit,))

    def fetch_prediction_logs(self, limit: int = 200) -> pd.DataFrame:
        query = """
        SELECT timestamp, model_name, predicted_ram_percent, actual_ram_percent
        FROM prediction_logs ORDER BY id DESC LIMIT ?
        """
        with self._conn() as conn:
            df = pd.read_sql_query(query, conn, params=(limit,))
        return df.sort_values("timestamp")

    def fetch_analysis_reports(self, limit: int = 100) -> pd.DataFrame:
        query = """
        SELECT timestamp, risk_level, causes, dos, donts, model_name, confidence, stability_index
        FROM analysis_reports ORDER BY id DESC LIMIT ?
        """
        with self._conn() as conn:
            return pd.read_sql_query(query, conn, params=(limit,))

    # Backward-compatible fetch method names
    def fetch_predictions(self, limit: int = 200) -> pd.DataFrame:
        return self.fetch_prediction_logs(limit=limit)

    def fetch_alerts(self, limit: int = 100) -> pd.DataFrame:
        reports = self.fetch_analysis_reports(limit=limit)
        if reports.empty:
            return reports
        reports = reports.copy()
        reports["message"] = reports["causes"]
        return reports[["timestamp", "risk_level", "message", "stability_index"]]

    def fetch_analysis_results(self, limit: int = 100) -> pd.DataFrame:
        return self.fetch_analysis_reports(limit=limit)

    def fetch_device_logs(self, limit: int = 150) -> pd.DataFrame:
        query = """
        SELECT timestamp, event_type, device_type, device_name, device_id, mountpoint,
               capacity_bytes, used_bytes, usage_percent, source_os, is_connected
        FROM device_logs ORDER BY id DESC LIMIT ?
        """
        with self._conn() as conn:
            return pd.read_sql_query(query, conn, params=(limit,))

    def fetch_memory_logs(self, limit: int = 300) -> pd.DataFrame:
        query = """
        SELECT timestamp, ram_percent, ram_used_mb, swap_percent, available_mb
        FROM memory_logs ORDER BY id DESC LIMIT ?
        """
        with self._conn() as conn:
            df = pd.read_sql_query(query, conn, params=(limit,))
        return df.sort_values("timestamp")

    def fetch_device_activity_summary(self, limit: int = 200) -> pd.DataFrame:
        query = """
        SELECT timestamp,
               SUM(CASE WHEN is_connected = 1 THEN 1 ELSE 0 END) AS active_devices,
               SUM(CASE WHEN event_type = 'connected' THEN 1 ELSE 0 END) AS connected_events,
               SUM(CASE WHEN event_type = 'disconnected' THEN 1 ELSE 0 END) AS disconnected_events
        FROM (
            SELECT timestamp, event_type, is_connected
            FROM device_logs
            ORDER BY id DESC
            LIMIT ?
        )
        GROUP BY timestamp
        ORDER BY timestamp ASC
        """
        with self._conn() as conn:
            return pd.read_sql_query(query, conn, params=(limit,))

    def get_index_status(self) -> dict[str, bool]:
        target_indexes = [*TIMESTAMP_INDEXES, *PERFORMANCE_INDEXES]
        placeholders = ",".join(["?"] * len(target_indexes))
        query = f"""
        SELECT name FROM sqlite_master
        WHERE type='index' AND name IN ({placeholders})
        """
        with self._conn() as conn:
            rows = conn.execute(query, target_indexes).fetchall()
        found = {row[0] for row in rows}
        return {idx: idx in found for idx in target_indexes}
