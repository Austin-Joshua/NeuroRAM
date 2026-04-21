"""SQLite persistence layer for NeuroRAM."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Dict, Iterable

import pandas as pd

from neuroram.backend.dbms_module.models import TIMESTAMP_INDEXES
from neuroram.backend.dbms_module.queries import CREATE_SCHEMA_SQL
from neuroram.config.config import CONFIG


class DatabaseManager:
    def __init__(self, db_path: str = CONFIG.db_path) -> None:
        self.db_path = db_path
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

    def insert_system_metric(self, row: Dict[str, float]) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO system_metrics (
                    timestamp, cpu_percent, ram_total_mb, ram_used_mb, ram_percent,
                    swap_total_mb, swap_used_mb, swap_percent, available_mb
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["timestamp"],
                    row["cpu_percent"],
                    row["ram_total_mb"],
                    row["ram_used_mb"],
                    row["ram_percent"],
                    row["swap_total_mb"],
                    row["swap_used_mb"],
                    row["swap_percent"],
                    row["available_mb"],
                ),
            )

    def insert_process_metrics(self, rows: Iterable[Dict[str, float]]) -> None:
        with self._conn() as conn:
            conn.executemany(
                """
                INSERT INTO process_metrics (
                    timestamp, pid, name, username, rss_mb, vms_mb, memory_percent, cpu_percent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
                        row["cpu_percent"],
                    )
                    for row in rows
                ],
            )

    def insert_prediction(
        self, timestamp: str, model_name: str, predicted_ram_percent: float, actual_ram_percent: float | None
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO predictions (timestamp, model_name, predicted_ram_percent, actual_ram_percent)
                VALUES (?, ?, ?, ?)
                """,
                (timestamp, model_name, predicted_ram_percent, actual_ram_percent),
            )

    def insert_alert(self, timestamp: str, risk_level: str, message: str, stability_index: float) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO alerts (timestamp, risk_level, message, stability_index)
                VALUES (?, ?, ?, ?)
                """,
                (timestamp, risk_level, message, stability_index),
            )

    def fetch_system_metrics(self, limit: int = 300) -> pd.DataFrame:
        query = """
        SELECT timestamp, cpu_percent, ram_percent, ram_used_mb, swap_percent, available_mb
        FROM system_metrics ORDER BY id DESC LIMIT ?
        """
        with self._conn() as conn:
            df = pd.read_sql_query(query, conn, params=(limit,))
        return df.sort_values("timestamp")

    def fetch_recent_process_metrics(self, limit: int = 50) -> pd.DataFrame:
        query = """
        SELECT timestamp, pid, name, username, rss_mb, vms_mb, memory_percent, cpu_percent
        FROM process_metrics ORDER BY id DESC LIMIT ?
        """
        with self._conn() as conn:
            df = pd.read_sql_query(query, conn, params=(limit,))
        return df

    def fetch_predictions(self, limit: int = 200) -> pd.DataFrame:
        query = """
        SELECT timestamp, model_name, predicted_ram_percent, actual_ram_percent
        FROM predictions ORDER BY id DESC LIMIT ?
        """
        with self._conn() as conn:
            df = pd.read_sql_query(query, conn, params=(limit,))
        return df.sort_values("timestamp")

    def fetch_alerts(self, limit: int = 100) -> pd.DataFrame:
        query = """
        SELECT timestamp, risk_level, message, stability_index
        FROM alerts ORDER BY id DESC LIMIT ?
        """
        with self._conn() as conn:
            df = pd.read_sql_query(query, conn, params=(limit,))
        return df

    def get_index_status(self) -> dict[str, bool]:
        placeholders = ",".join(["?"] * len(TIMESTAMP_INDEXES))
        query = f"""
        SELECT name FROM sqlite_master
        WHERE type='index' AND name IN ({placeholders})
        """
        with self._conn() as conn:
            rows = conn.execute(query, TIMESTAMP_INDEXES).fetchall()
        found = {row[0] for row in rows}
        return {idx: idx in found for idx in TIMESTAMP_INDEXES}
