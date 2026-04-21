"""OS monitoring orchestration helpers."""

from __future__ import annotations

from typing import Tuple

import pandas as pd

from neuroram.backend.os_module.collector import collect_process_metrics, collect_system_metrics
from neuroram.backend.dbms_module.database import DatabaseManager


def collect_and_store(db: DatabaseManager, process_limit: int | None = None) -> Tuple[dict, pd.DataFrame]:
    system_row = collect_system_metrics()
    process_rows = collect_process_metrics(limit=process_limit)
    db.insert_system_metric(system_row)
    db.insert_process_metrics(process_rows)
    return system_row, pd.DataFrame(process_rows)
