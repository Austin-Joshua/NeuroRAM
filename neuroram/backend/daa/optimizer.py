"""Optimization recommendations using priority scoring and greedy strategy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd

from neuroram.backend.daa.risk_analyzer import RiskLevel


@dataclass
class OptimizationAdvice:
    process_name: str
    pid: int
    priority_score: float
    recommendation: str


def rank_processes(process_df: pd.DataFrame) -> pd.DataFrame:
    if process_df.empty:
        return process_df

    ranked = process_df.copy()
    ranked["priority_score"] = 0.78 * ranked["rss_mb"].astype(float) + 0.22 * ranked["memory_percent"].astype(float)
    ranked = ranked.sort_values("priority_score", ascending=False)
    return ranked


def greedy_optimization_strategy(process_df: pd.DataFrame, risk_level: RiskLevel) -> List[OptimizationAdvice]:
    if process_df.empty:
        return []

    ranked = rank_processes(process_df)
    top_n = 3 if risk_level in (RiskLevel.CRITICAL, RiskLevel.EMERGENCY) else 2
    selected = ranked.head(top_n)

    advice: List[OptimizationAdvice] = []
    for _, row in selected.iterrows():
        if row["name"].lower() in {"chrome.exe", "msedge.exe", "firefox.exe"}:
            action = "Close unused browser tabs and disable heavy extensions."
        elif row["name"].lower() in {"python.exe", "java.exe", "node.exe"}:
            action = "Profile the workload and reduce concurrent jobs if possible."
        else:
            action = "Review this process and close/restart it if not mission-critical."

        advice.append(
            OptimizationAdvice(
                process_name=str(row["name"]),
                pid=int(row["pid"]),
                priority_score=round(float(row["priority_score"]), 2),
                recommendation=action,
            )
        )
    return advice


def complexity_analysis() -> dict:
    return {
        "ranking": "Sorting process list: O(n log n)",
        "selection": "Choosing top-k candidates: O(k)",
        "overall": "O(n log n)",
    }


def build_actionable_guidance(risk_level: RiskLevel, active_devices: int, recent_disconnects: int) -> dict:
    causes: List[str] = []
    dos: List[str] = []
    donts: List[str] = []

    if active_devices > 0:
        causes.append(f"{active_devices} external device(s) active in recent cycles.")
    if recent_disconnects > 0:
        causes.append(f"{recent_disconnects} disconnection event(s) detected recently.")

    if risk_level in (RiskLevel.CRITICAL, RiskLevel.EMERGENCY):
        dos.extend(
            [
                "Free memory from non-essential processes immediately.",
                "Reduce external-device file transfer load.",
                "Retry monitoring after each optimization action.",
            ]
        )
        donts.extend(
            [
                "Do not run stress workloads until risk falls below WARNING.",
                "Do not keep unnecessary USB/WiFi dongles attached.",
            ]
        )
    elif risk_level == RiskLevel.WARNING:
        dos.extend(
            [
                "Review top memory processes and close optional ones.",
                "Keep external-device activity minimal for next cycles.",
            ]
        )
        donts.extend(
            [
                "Do not launch additional heavy jobs immediately.",
            ]
        )
    else:
        dos.extend(["Continue routine monitoring and periodic cleanup."])
        donts.extend(["Do not disable predictive monitoring controls."])

    if not causes:
        causes.append("No immediate abnormal behavior observed.")
    return {"causes": causes, "dos": dos, "donts": donts}
