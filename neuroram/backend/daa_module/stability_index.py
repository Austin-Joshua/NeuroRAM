"""Computes a system stability score in range 0-100."""

from __future__ import annotations

from neuroram.backend.daa_module.risk_analyzer import RiskLevel


def compute_stability_index(ram_percent: float, cpu_percent: float, swap_percent: float, risk_level: RiskLevel) -> float:
    ram_penalty = min(ram_percent * 0.45, 45.0)
    cpu_penalty = min(cpu_percent * 0.20, 20.0)
    swap_penalty = min(swap_percent * 0.20, 20.0)

    risk_penalty_map = {
        RiskLevel.NORMAL: 0.0,
        RiskLevel.WARNING: 7.0,
        RiskLevel.CRITICAL: 12.0,
        RiskLevel.EMERGENCY: 18.0,
    }
    risk_penalty = risk_penalty_map[risk_level]

    score = 100.0 - (ram_penalty + cpu_penalty + swap_penalty + risk_penalty)
    return round(max(0.0, min(100.0, score)), 2)
