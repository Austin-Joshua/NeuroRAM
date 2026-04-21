"""Collects system and process level memory metrics using psutil."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

import psutil

from neuroram.config.config import CONFIG


def collect_system_metrics() -> Dict[str, float]:
    vm = psutil.virtual_memory()
    sm = psutil.swap_memory()
    cpu = psutil.cpu_percent(interval=0.2)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "cpu_percent": cpu,
        "ram_total_mb": vm.total / (1024 * 1024),
        "ram_used_mb": vm.used / (1024 * 1024),
        "ram_percent": vm.percent,
        "swap_total_mb": sm.total / (1024 * 1024),
        "swap_used_mb": sm.used / (1024 * 1024),
        "swap_percent": sm.percent,
        "available_mb": vm.available / (1024 * 1024),
    }


def collect_process_metrics(limit: int | None = None) -> List[Dict[str, float]]:
    limit = limit or CONFIG.process_limit
    rows: List[Dict[str, float]] = []

    for proc in psutil.process_iter(
        attrs=["pid", "name", "username", "memory_info", "memory_percent", "cpu_percent"]
    ):
        info = proc.info
        mem_info = info.get("memory_info")
        if mem_info is None:
            continue

        rows.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "pid": info.get("pid", -1),
                "name": (info.get("name") or "unknown")[:120],
                "username": (info.get("username") or "unknown")[:120],
                "rss_mb": mem_info.rss / (1024 * 1024),
                "vms_mb": mem_info.vms / (1024 * 1024),
                "memory_percent": float(info.get("memory_percent") or 0.0),
                "cpu_percent": float(info.get("cpu_percent") or 0.0),
            }
        )

    rows.sort(key=lambda x: x["rss_mb"], reverse=True)
    return rows[:limit]
