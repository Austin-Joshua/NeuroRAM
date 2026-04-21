"""Optimization recommendations using priority scoring and greedy strategy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd

from neuroram.backend.daa_module.risk_analyzer import RiskLevel


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
    ranked["priority_score"] = 0.7 * ranked["rss_mb"].astype(float) + 0.3 * ranked["cpu_percent"].astype(float)
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
