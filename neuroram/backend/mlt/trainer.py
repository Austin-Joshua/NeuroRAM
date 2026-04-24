"""CLI training and data collection workflows."""

from __future__ import annotations

import time

from neuroram.backend.dbms.database import DatabaseManager
from neuroram.backend.mlt.ml_engine import MLEngine, TENSORFLOW_AVAILABLE
from neuroram.backend.os.collector import collect_process_metrics, collect_system_metrics
from neuroram.config.config import CONFIG


def collect_samples(sample_count: int = 60, interval_sec: int = 2) -> None:
    db = DatabaseManager()
    print(f"Collecting {sample_count} samples at {interval_sec}s interval...")
    for i in range(sample_count):
        system_row = collect_system_metrics()
        process_rows = collect_process_metrics()
        db.insert_system_metric(system_row)
        db.insert_process_metrics(process_rows)
        print(f"[{i + 1}/{sample_count}] RAM: {system_row['ram_percent']:.2f}%")
        time.sleep(interval_sec)


def train_models(train_lstm: bool = False) -> None:
    db = DatabaseManager()
    engine = MLEngine()
    hist_df = db.fetch_system_metrics(limit=1200)
    result = engine.train_random_forest(hist_df)
    print("RandomForest training complete:", result)

    if train_lstm and TENSORFLOW_AVAILABLE:
        lstm_result = engine.train_lstm(hist_df, epochs=10)
        print("LSTM training complete:", lstm_result)
    elif train_lstm:
        print("TensorFlow unavailable. Skipping LSTM.")


if __name__ == "__main__":
    collect_samples(sample_count=40, interval_sec=CONFIG.collection_interval_sec)
    train_models(train_lstm=False)
