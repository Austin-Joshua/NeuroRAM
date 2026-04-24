"""Risk and anomaly analysis for memory behavior."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List

import pandas as pd

from neuroram.config.config import CONFIG


class RiskLevel(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


@dataclass
class RiskReport:
    level: RiskLevel
    leak_detected: bool
    reasons: List[str]
    dos: List[str]
    donts: List[str]


def detect_memory_leak(system_df: pd.DataFrame, window: int = 8) -> bool:
    if len(system_df) < window:
        return False

    recent = system_df.tail(window)["ram_percent"].astype(float)
    growth = recent.iloc[-1] - recent.iloc[0]
    strictly_increasing = all(recent.iloc[i] <= recent.iloc[i + 1] for i in range(len(recent) - 1))
    return bool(strictly_increasing and growth >= CONFIG.leak_growth_threshold)


def classify_risk(
    current_ram_percent: float,
    leak_detected: bool,
    predicted_ram_percent: float | None = None,
    device_pressure_score: float = 0.0,
) -> RiskReport:
    reasons: List[str] = []
    dos: List[str] = []
    donts: List[str] = []
    effective_ram = max(current_ram_percent, predicted_ram_percent or current_ram_percent)

    if effective_ram >= CONFIG.emergency_threshold:
        level = RiskLevel.EMERGENCY
        reasons.append("RAM usage crossed emergency threshold.")
    elif effective_ram >= CONFIG.critical_threshold:
        level = RiskLevel.CRITICAL
        reasons.append("RAM usage crossed critical threshold.")
    elif effective_ram >= CONFIG.warning_threshold:
        level = RiskLevel.WARNING
        reasons.append("RAM usage crossed warning threshold.")
    else:
        level = RiskLevel.NORMAL
        reasons.append("RAM usage is in safe range.")

    if leak_detected:
        reasons.append("Monotonic RAM growth suggests a possible memory leak.")
        if level == RiskLevel.NORMAL:
            level = RiskLevel.WARNING
        elif level == RiskLevel.WARNING:
            level = RiskLevel.CRITICAL

    if predicted_ram_percent is not None and predicted_ram_percent > current_ram_percent + 4.0:
        reasons.append("Predicted RAM indicates near-future increase in memory pressure.")
        if level == RiskLevel.NORMAL:
            level = RiskLevel.WARNING
    if device_pressure_score >= 2.0:
        reasons.append("External device activity is high and may affect memory behavior.")
        if level == RiskLevel.NORMAL:
            level = RiskLevel.WARNING

    if level in (RiskLevel.CRITICAL, RiskLevel.EMERGENCY):
        dos.extend(
            [
                "Close high-memory background applications first.",
                "Pause heavy workloads until memory stabilizes.",
                "Safely eject unused removable USB storage devices.",
            ]
        )
        donts.extend(
            [
                "Do not start additional memory-intensive applications.",
                "Do not copy large files to external drives during peak load.",
                "Do not ignore repeated critical/emergency alerts.",
            ]
        )
    elif level == RiskLevel.WARNING:
        dos.extend(
            [
                "Limit optional browser tabs and development tasks.",
                "Monitor trends for 2-3 cycles before raising workload.",
            ]
        )
        donts.extend(
            [
                "Do not keep unused external dongles mounted unnecessarily.",
                "Do not run multiple heavy tools simultaneously.",
            ]
        )
    else:
        dos.extend(
            [
                "Continue normal monitoring at configured refresh interval.",
                "Keep only essential device connections active.",
            ]
        )
        donts.extend(
            [
                "Do not disable monitoring during long-running workloads.",
            ]
        )

    return RiskReport(level=level, leak_detected=leak_detected, reasons=reasons, dos=dos, donts=donts)


def map_health_category(level: RiskLevel, anomaly_detected: bool = False) -> str:
    """Map raw risk levels to UI-friendly categories."""
    if level in {RiskLevel.CRITICAL, RiskLevel.EMERGENCY}:
        return "critical"
    if level == RiskLevel.WARNING or anomaly_detected:
        return "degrading"
    return "stable"
