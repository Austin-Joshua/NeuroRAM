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


def detect_memory_leak(system_df: pd.DataFrame, window: int = 8) -> bool:
    if len(system_df) < window:
        return False

    recent = system_df.tail(window)["ram_percent"].astype(float)
    growth = recent.iloc[-1] - recent.iloc[0]
    strictly_increasing = all(recent.iloc[i] <= recent.iloc[i + 1] for i in range(len(recent) - 1))
    return bool(strictly_increasing and growth >= CONFIG.leak_growth_threshold)


def classify_risk(current_ram_percent: float, leak_detected: bool) -> RiskReport:
    reasons: List[str] = []

    if current_ram_percent >= CONFIG.emergency_threshold:
        level = RiskLevel.EMERGENCY
        reasons.append("RAM usage crossed emergency threshold.")
    elif current_ram_percent >= CONFIG.critical_threshold:
        level = RiskLevel.CRITICAL
        reasons.append("RAM usage crossed critical threshold.")
    elif current_ram_percent >= CONFIG.warning_threshold:
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

    return RiskReport(level=level, leak_detected=leak_detected, reasons=reasons)
