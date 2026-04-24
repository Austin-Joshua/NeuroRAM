"""OS monitoring orchestration helpers."""

from __future__ import annotations

from typing import Tuple

import pandas as pd

from backend.DBMS.database import DatabaseManager
from backend.OS.collector import collect_process_metrics, collect_system_metrics
from backend.OS.device_monitor import DeviceSnapshot, collect_external_devices, detect_device_events


def collect_and_store(
    db: DatabaseManager,
    process_limit: int | None = None,
    previous_devices: dict[str, DeviceSnapshot] | None = None,
) -> Tuple[dict, pd.DataFrame, pd.DataFrame, dict[str, DeviceSnapshot]]:
    system_row = collect_system_metrics()
    process_rows = collect_process_metrics(limit=process_limit)
    db.insert_system_metric(system_row)
    db.insert_process_metrics(process_rows)

    # Include peripheral devices so input/wifi dongles are captured in event logs.
    devices = collect_external_devices(include_peripheral_devices=True)
    device_events, current_state = detect_device_events(devices, previous_devices=previous_devices)
    db.insert_device_logs(device_events)
    return system_row, pd.DataFrame(process_rows), pd.DataFrame(device_events), current_state
