"""NeuroRAM Predictive Memory Management System (canonical Streamlit UI module)."""

from __future__ import annotations

import os
import time
import json
import io
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from backend.DAA.optimizer import build_actionable_guidance, greedy_optimization_strategy
from backend.DAA.risk_analyzer import RiskLevel, classify_risk, detect_memory_leak
from backend.DAA.stability_index import compute_stability_index
from backend.DBMS.database import DatabaseManager
from backend.MLT.ml_engine import MLEngine, TENSORFLOW_AVAILABLE
from backend.MLT.predictor import predict_next_ram
from backend.OS.collector import collect_process_metrics, collect_system_metrics
from backend.OS.device_monitor import DeviceSnapshot, collect_external_devices, detect_device_events
from neuroram.config.config import CONFIG
from neuroram.config.settings import EXPORTS_DIR

st.set_page_config(page_title="NeuroRAM | Predictive Memory Management System", page_icon="🧠", layout="wide", initial_sidebar_state="collapsed")


def risk_color(level: RiskLevel) -> str:
    return {
        RiskLevel.NORMAL: "#2563EB",
        RiskLevel.WARNING: "#F59E0B",
        RiskLevel.CRITICAL: "#EF4444",
        RiskLevel.EMERGENCY: "#B91C1C",
    }[level]


def get_theme_tokens(theme_mode: str, dark_variant: str) -> dict[str, object]:
    if theme_mode == "Light":
        return {
            "bg": (
                "radial-gradient(ellipse 120% 80% at 0% 0%, rgba(254, 215, 170, 0.55) 0%, transparent 50%), "
                "radial-gradient(ellipse 100% 70% at 100% 10%, rgba(196, 181, 253, 0.45) 0%, transparent 45%), "
                "radial-gradient(ellipse 90% 60% at 50% 100%, rgba(147, 197, 253, 0.45) 0%, transparent 50%), "
                "linear-gradient(165deg, #fff7ed 0%, #fefce8 35%, #eff6ff 70%, #faf5ff 100%)"
            ),
            "text": "#0f172a",
            "sub": "#4338ca",
            "card": (
                "linear-gradient(135deg, rgba(255,255,255,0.98) 0%, rgba(254, 243, 199, 0.35) 40%, "
                "rgba(224, 231, 255, 0.45) 100%)"
            ),
            "top": (
                "linear-gradient(120deg, rgba(251, 191, 36, 0.22) 0%, rgba(255,255,255,0.92) 35%, "
                "rgba(129, 140, 248, 0.18) 65%, rgba(52, 211, 153, 0.15) 100%)"
            ),
            "accent": "#7c3aed",
            "grid": "rgba(15, 23, 42, 0.12)",
            "chart_actual": "#2563EB",
            "chart_pred": "#6d28d9",
            "chart_fill": "rgba(109, 40, 217, 0.12)",
            "chart_multi": ["#2563EB", "#6d28d9", "#c2410c", "#0369a1", "#b45309"],
        }

    # Dark: deep charcoal with blue/gold accents (not pure black).
    dark_palettes: dict[str, dict[str, object]] = {
        "Midnight Indigo": {
            "bg": (
                "radial-gradient(circle at 10% 8%, rgba(59,130,246,0.11) 0%, transparent 34%), "
                "radial-gradient(circle at 92% 4%, rgba(245,158,11,0.08) 0%, transparent 34%), "
                "linear-gradient(155deg, #0b0f0c 0%, #111316 46%, #151812 100%)"
            ),
            "text": "#f8fafc",
            "sub": "#cbd5e1",
            "card": "linear-gradient(125deg, rgba(21,24,18,0.94) 0%, rgba(15,18,16,0.96) 100%)",
            "top": "linear-gradient(115deg, rgba(59,130,246,0.14) 0%, rgba(17,19,22,0.94) 45%, rgba(245,158,11,0.10) 100%)",
            "accent": "#fbbf24",
            "grid": "rgba(226,232,240,0.10)",
            "chart_actual": "#60A5FA",
            "chart_pred": "#fbbf24",
            "chart_fill": "rgba(96,165,250,0.16)",
            "chart_multi": ["#60A5FA", "#fbbf24", "#f87171", "#38bdf8", "#c4b5fd"],
        },
        "Neon Slate": {
            "bg": (
                "radial-gradient(circle at 10% 8%, rgba(59,130,246,0.13) 0%, transparent 32%), "
                "radial-gradient(circle at 92% 4%, rgba(202,138,4,0.12) 0%, transparent 30%), "
                "linear-gradient(150deg, #0a0d0b 0%, #121417 48%, #171915 100%)"
            ),
            "text": "#f8fafc",
            "sub": "#cbd5e1",
            "card": "linear-gradient(125deg, rgba(23,25,21,0.94) 0%, rgba(13,16,14,0.96) 100%)",
            "top": "linear-gradient(115deg, rgba(59,130,246,0.15) 0%, rgba(18,20,23,0.94) 45%, rgba(202,138,4,0.13) 100%)",
            "accent": "#f59e0b",
            "grid": "rgba(226,232,240,0.10)",
            "chart_actual": "#60A5FA",
            "chart_pred": "#f59e0b",
            "chart_fill": "rgba(245,158,11,0.14)",
            "chart_multi": ["#60A5FA", "#f59e0b", "#fb7185", "#22d3ee", "#a78bfa"],
        },
        "Carbon Violet": {
            "bg": (
                "radial-gradient(circle at 10% 8%, rgba(59,130,246,0.12) 0%, transparent 34%), "
                "radial-gradient(circle at 90% 3%, rgba(245,158,11,0.09) 0%, transparent 30%), "
                "linear-gradient(155deg, #0a0d0d 0%, #131417 44%, #19161a 100%)"
            ),
            "text": "#f8fafc",
            "sub": "#cbd5e1",
            "card": "linear-gradient(125deg, rgba(25,22,26,0.94) 0%, rgba(15,16,19,0.96) 100%)",
            "top": "linear-gradient(115deg, rgba(59,130,246,0.14) 0%, rgba(19,20,23,0.94) 45%, rgba(245,158,11,0.11) 100%)",
            "accent": "#fbbf24",
            "grid": "rgba(226,232,240,0.10)",
            "chart_actual": "#60A5FA",
            "chart_pred": "#fbbf24",
            "chart_fill": "rgba(244,114,182,0.12)",
            "chart_multi": ["#60A5FA", "#fbbf24", "#f472b6", "#2dd4bf", "#a78bfa"],
        },
    }
    return dark_palettes.get(dark_variant, dark_palettes["Midnight Indigo"])


def inject_styles(theme_mode: str, dark_variant: str, compact_mode: bool = False) -> None:
    is_light = theme_mode == "Light"
    tokens = get_theme_tokens(theme_mode, dark_variant)
    bg = str(tokens["bg"])
    text = str(tokens["text"])
    sub = str(tokens["sub"])
    card = str(tokens["card"])
    top = str(tokens["top"])
    accent = str(tokens["accent"])
    status_bg = "rgba(255,255,255,0.88)" if is_light else "rgba(20,24,20,0.9)"
    top_border = "rgba(148,163,184,0.35)" if is_light else "rgba(245,158,11,0.26)"
    card_border = "rgba(15,23,42,0.12)" if is_light else "rgba(59,130,246,0.26)"
    card_shadow = "0 6px 20px rgba(15, 23, 42, 0.08)" if is_light else "0 8px 24px rgba(2, 6, 3, 0.55)"
    compact_css = ""
    if compact_mode:
        compact_css = f"""
    .block-container {{
        max-width: 430px !important;
        padding-left: 0.56rem !important;
        padding-right: 0.56rem !important;
        padding-top: 0.42rem !important;
    }}
    .top-shell, .glass-card, .summary-banner, .action-panel {{
        border-radius: 10px !important;
        padding: 0.58rem 0.64rem !important;
    }}
    .title-main {{
        font-size: 1.04rem !important;
    }}
    .title-sub {{
        font-size: 0.76rem !important;
    }}
    .kpi-grid {{
        grid-template-columns: 1fr !important;
        gap: 0.45rem !important;
    }}
    .kpi-value {{
        font-size: 1.05rem !important;
    }}
    """

    css = f"""
    <style>
    .stApp {{
        background: {bg};
        color: {text};
    }}
    .block-container {{
        max-width: 1380px;
        padding-top: 0.7rem;
        padding-bottom: 1rem;
    }}
    .top-shell {{
        border-radius: 16px;
        border: 1px solid {top_border};
        padding: 0.74rem 0.9rem;
        margin-bottom: 0.55rem;
        background: {top};
    }}
    .title-main {{font-size: clamp(1.25rem, 1.4vw, 1.58rem); font-weight: 700;}}
    .title-sub {{font-size: clamp(0.82rem, 0.95vw, 0.96rem); color: {sub}; font-weight: 600;}}
    .status-chip {{
        border-radius: 999px;
        padding: 0.36rem 0.72rem;
        border: 1px solid {top_border};
        font-size: clamp(0.72rem,0.84vw,0.86rem);
        font-weight: 700;
        background: {status_bg};
        color: {text};
    }}
    .glass-card {{
        border-radius: 14px;
        border: 1px solid {card_border};
        background: {card};
        padding: 0.74rem 0.86rem;
        margin-bottom: 0.6rem;
        box-shadow: {card_shadow};
    }}
    .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(178px, 1fr));
        gap: 0.6rem;
        margin-bottom: 0.55rem;
    }}
    .kpi-card {{
        border-radius: 12px;
        border: 1px solid {card_border};
        background: {card};
        box-shadow: {card_shadow};
        padding: 0.66rem 0.78rem;
        min-height: 90px;
    }}
    .kpi-title {{
        display: flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 700;
        color: {sub};
    }}
    .kpi-chip {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 1.3rem;
        height: 1.3rem;
        border-radius: 999px;
        font-size: 0.78rem;
        border: 1px solid {card_border};
        background: {status_bg};
    }}
    .kpi-value {{
        font-size: 1.25rem;
        font-weight: 800;
        color: {text};
        margin-top: 0.18rem;
    }}
    .kpi-hint {{
        font-size: 0.76rem;
        color: {sub};
        margin-top: 0.22rem;
    }}
    .summary-banner {{
        border-radius: 14px;
        border: 1px solid {card_border};
        background: {top};
        box-shadow: {card_shadow};
        padding: 0.82rem 0.9rem;
        margin-bottom: 0.7rem;
    }}
    .summary-title {{
        font-size: clamp(0.86rem, 1.0vw, 1rem);
        font-weight: 700;
        color: {sub};
        margin-bottom: 0.28rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    .summary-text {{
        font-size: clamp(0.86rem, 1.0vw, 0.98rem);
        line-height: 1.45;
        color: {text};
    }}
    .action-panel {{
        border-radius: 12px;
        border: 1px solid {card_border};
        background: {card};
        box-shadow: {card_shadow};
        padding: 0.72rem 0.82rem;
        margin-bottom: 0.6rem;
    }}
    .action-title {{
        font-size: 0.84rem;
        font-weight: 700;
        color: {sub};
        margin-bottom: 0.3rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    .quick-nav-shell {{
        border-radius: 12px;
        border: 1px solid {card_border};
        background: {card};
        box-shadow: {card_shadow};
        padding: 0.48rem 0.62rem 0.1rem 0.62rem;
        margin-bottom: 0.6rem;
    }}
    .quick-nav-label {{
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 700;
        color: {sub};
        margin-bottom: 0.12rem;
    }}
    .section-title {{
        text-transform: uppercase;
        font-size: clamp(0.72rem,0.84vw,0.86rem);
        letter-spacing: 0.06em;
        font-weight: 700;
        color: {sub};
        margin: 0.2rem 0 0.34rem 0;
    }}
    .analysis-block {{
        border-left: 3px solid {accent};
        padding-left: 0.58rem;
        margin-bottom: 0.42rem;
        font-size: clamp(0.78rem,0.9vw,0.92rem);
    }}
    .confidence-badge {{
        display: inline-block;
        border-radius: 999px;
        padding: 0.2rem 0.58rem;
        border: 1px solid transparent;
        font-size: clamp(0.69rem,0.8vw,0.8rem);
        font-weight: 700;
    }}
    .confidence-high {{background: rgba(59,130,246,0.2); color:#2563EB; border-color: rgba(59,130,246,0.35);}}
    .confidence-medium {{background: rgba(245,158,11,0.2); color:#B45309; border-color: rgba(245,158,11,0.35);}}
    .confidence-low {{background: rgba(239,68,68,0.16); color:#B91C1C; border-color: rgba(239,68,68,0.35);}}
    [data-testid="stMetricLabel"] p {{
        color: {sub};
        font-weight: 700;
        letter-spacing: 0.015em;
    }}
    [data-testid="stMetricValue"] {{
        color: {text};
        font-weight: 800;
    }}
    [data-testid="stCaptionContainer"] {{
        color: {sub};
        font-weight: 600;
    }}
    @media (max-width: 1024px) {{
        .block-container {{
            max-width: 960px;
            padding-top: 0.56rem;
            padding-bottom: 0.82rem;
        }}
        .kpi-grid {{
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }}
    }}
    @media (max-width: 768px) {{
        .block-container {{
            max-width: 100%;
            padding-left: 0.62rem;
            padding-right: 0.62rem;
            padding-top: 0.48rem;
        }}
        .top-shell, .glass-card, .summary-banner, .action-panel {{
            border-radius: 10px;
            padding: 0.6rem 0.68rem;
        }}
        .title-main {{
            font-size: 1.08rem;
        }}
        .title-sub {{
            font-size: 0.78rem;
        }}
        .kpi-grid {{
            grid-template-columns: 1fr;
            gap: 0.48rem;
        }}
        .kpi-value {{
            font-size: 1.1rem;
        }}
    }}
    {compact_css}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def style_plot(fig: go.Figure, title: str, theme_mode: str, height: int = 320) -> go.Figure:
    dark_variant = str(st.session_state.get("dark_variant", "Midnight Indigo"))
    tokens = get_theme_tokens(theme_mode, dark_variant)
    is_light = theme_mode == "Light"
    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=10, r=10, t=42, b=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.04)" if is_light else "rgba(255,255,255,0.04)",
        font=dict(color=str(tokens["text"])),
        xaxis=dict(showgrid=True, gridcolor=str(tokens["grid"])),
        yaxis=dict(showgrid=True, gridcolor=str(tokens["grid"])),
    )
    return fig


def _timestamp_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_backfill_status() -> dict:
    status_path = EXPORTS_DIR / "backfill_status.json"
    if not status_path.exists():
        return {"available": False, "message": "Backfill has not been run yet."}
    try:
        payload = json.loads(status_path.read_text(encoding="utf-8"))
        counts = payload.get("counts", {})
        return {
            "available": True,
            "ran_at_utc": payload.get("ran_at_utc", "unknown"),
            "memory_logs_added": int(counts.get("memory_logs_added", 0)),
            "prediction_logs_added": int(counts.get("prediction_logs_added", 0)),
            "analysis_reports_added": int(counts.get("analysis_reports_added", 0)),
        }
    except Exception:
        return {"available": False, "message": "Backfill status file is unreadable."}


def generate_data(db: DatabaseManager, sample_count: int = 80) -> None:
    base = collect_system_metrics()
    rng = np.random.default_rng()
    now = datetime.now(timezone.utc)
    for i in range(sample_count):
        ts = (now - timedelta(seconds=(sample_count - i) * 2)).isoformat()
        ram = float(np.clip(base["ram_percent"] + rng.normal(0, 2.1), 30.0, 95.0))
        swap = float(np.clip(base["swap_percent"] + rng.normal(0, 1.2), 0.0, 98.0))
        row = {
            "timestamp": ts,
            "ram_total_mb": base["ram_total_mb"],
            "ram_used_mb": (ram / 100.0) * base["ram_total_mb"],
            "ram_percent": ram,
            "swap_total_mb": base["swap_total_mb"],
            "swap_used_mb": (swap / 100.0) * base["swap_total_mb"],
            "swap_percent": swap,
            "available_mb": max(1.0, base["ram_total_mb"] - ((ram / 100.0) * base["ram_total_mb"])),
        }
        db.insert_system_metric(row)


def collect_cycle(
    db: DatabaseManager,
    do_collect: bool,
    previous_devices: dict[str, DeviceSnapshot] | None,
) -> tuple[dict | None, pd.DataFrame, pd.DataFrame, dict[str, DeviceSnapshot]]:
    if do_collect:
        system_row = collect_system_metrics()
        process_rows = collect_process_metrics(limit=CONFIG.process_limit)
        db.insert_system_metric(system_row)
        db.insert_process_metrics(process_rows)
        devices = collect_external_devices(include_peripheral_devices=True)
        device_events, current_state = detect_device_events(devices, previous_devices=previous_devices)
        db.insert_device_logs(device_events)
        return system_row, pd.DataFrame(process_rows), pd.DataFrame(device_events), current_state

    hist = db.fetch_system_metrics(limit=1)
    if hist.empty:
        return None, pd.DataFrame(), pd.DataFrame(), previous_devices or {}
    process_hist = db.fetch_recent_process_metrics(limit=CONFIG.process_limit)
    return hist.iloc[-1].to_dict(), process_hist, pd.DataFrame(), previous_devices or {}


def enrich_hist_for_ml(system_df: pd.DataFrame, device_log_df: pd.DataFrame) -> pd.DataFrame:
    if system_df.empty:
        return system_df

    def parse_ts(series: pd.Series) -> pd.Series:
        try:
            return pd.to_datetime(series, utc=True, errors="coerce", format="mixed")
        except TypeError:
            return pd.to_datetime(series, utc=True, errors="coerce")

    hist = system_df.copy()
    hist["timestamp"] = parse_ts(hist["timestamp"])
    hist = hist.dropna(subset=["timestamp"]).sort_values("timestamp")

    device = device_log_df.copy()
    hist["device_connected_count"] = 0.0
    hist["device_event_intensity"] = 0.0
    if not device.empty:
        device["timestamp"] = parse_ts(device["timestamp"])
        device = device.dropna(subset=["timestamp"]).sort_values("timestamp")
        agg = (
            device.groupby("timestamp")
            .agg(
                active_devices=("is_connected", "sum"),
                event_count=("event_type", "count"),
            )
            .reset_index()
            .rename(columns={"active_devices": "device_connected_count", "event_count": "device_event_intensity"})
            .sort_values("timestamp")
        )
        hist = pd.merge_asof(hist, agg, on="timestamp", direction="backward", suffixes=("", "_from_devices"))

        left_connected = "device_connected_count"
        if left_connected not in hist.columns and "device_connected_count_x" in hist.columns:
            left_connected = "device_connected_count_x"
        right_connected = "device_connected_count_from_devices"
        if right_connected not in hist.columns and "device_connected_count_y" in hist.columns:
            right_connected = "device_connected_count_y"

        left_intensity = "device_event_intensity"
        if left_intensity not in hist.columns and "device_event_intensity_x" in hist.columns:
            left_intensity = "device_event_intensity_x"
        right_intensity = "device_event_intensity_from_devices"
        if right_intensity not in hist.columns and "device_event_intensity_y" in hist.columns:
            right_intensity = "device_event_intensity_y"

        if right_connected in hist.columns:
            base_series = hist[left_connected] if left_connected in hist.columns else 0.0
            hist["device_connected_count"] = hist[right_connected].fillna(base_series)
        elif left_connected in hist.columns:
            hist["device_connected_count"] = hist[left_connected]

        if right_intensity in hist.columns:
            base_series = hist[left_intensity] if left_intensity in hist.columns else 0.0
            hist["device_event_intensity"] = hist[right_intensity].fillna(base_series)
        elif left_intensity in hist.columns:
            hist["device_event_intensity"] = hist[left_intensity]

        hist = hist.drop(
            columns=[
                "device_connected_count_x",
                "device_connected_count_y",
                "device_connected_count_from_devices",
                "device_event_intensity_x",
                "device_event_intensity_y",
                "device_event_intensity_from_devices",
            ],
            errors="ignore",
        )
    hist["timestamp"] = hist["timestamp"].dt.tz_convert(None).dt.strftime("%Y-%m-%d %H:%M:%S")
    return hist


def train_predict(hist_df: pd.DataFrame, engine: MLEngine, requested_model: str) -> tuple[float | None, str | None, dict | None]:
    if len(hist_df) < 40:
        return None, "Need at least 40 samples. Click Generate Data.", None
    recent_metrics = st.session_state.get("recent_model_metrics", {})
    if not isinstance(recent_metrics, dict):
        recent_metrics = {}
    st.session_state.recent_model_metrics = recent_metrics

    def paths(model_key: str) -> tuple[str, str]:
        return (CONFIG.lstm_model_path, CONFIG.lstm_scaler_path) if model_key == "lstm" else (CONFIG.rf_model_path, CONFIG.rf_scaler_path)

    def maybe_train(model_key: str) -> tuple[dict | None, str | None]:
        model_path, scaler_path = paths(model_key)
        gate_key = f"last_{model_key}_train_size"
        ready_key = f"model_ready_{model_key}"
        last_train_size = int(st.session_state.get(gate_key, -1))
        needs_retrain = (
            len(hist_df) - last_train_size >= 25
            or last_train_size < 0
            or not st.session_state.get(ready_key, False)
            or not Path(model_path).exists()
            or not Path(scaler_path).exists()
            or model_key not in recent_metrics
        )
        if not needs_retrain:
            return recent_metrics.get(model_key), None
        try:
            metrics = engine.train_lstm(hist_df, epochs=12) if model_key == "lstm" else engine.train_random_forest(hist_df)
        except Exception as exc:  # pragma: no cover
            return None, str(exc)
        st.session_state[gate_key] = len(hist_df)
        st.session_state[ready_key] = True
        recent_metrics[model_key] = metrics
        return metrics, None

    def model_rank(metrics: dict | None) -> tuple[float, float]:
        if not metrics:
            return (-1.0, -float("inf"))
        return (float(metrics.get("r2", -1.0)), -float(metrics.get("rmse", float("inf"))))

    requested = requested_model.lower()
    candidates = ["rf"] + (["lstm"] if TENSORFLOW_AVAILABLE and len(hist_df) >= 60 else [])
    if requested != "auto":
        candidates = ["rf"] if requested == "lstm" and not TENSORFLOW_AVAILABLE else [requested]
    model_errors: dict[str, str] = {}
    for model_key in candidates:
        _, err = maybe_train(model_key)
        if err:
            model_errors[model_key] = err
    available = [m for m in candidates if m in recent_metrics]
    if not available:
        return None, "Model training failed for all candidates.", None
    chosen = sorted(available, key=lambda name: model_rank(recent_metrics[name]), reverse=True)[0]
    pred = float(predict_next_ram(hist_df, model_choice=chosen))
    metrics = recent_metrics.get(chosen, {})
    confidence_score = max(0.0, min(100.0, float(metrics.get("r2", 0.0)) * 100.0 - float(metrics.get("rmse", 0.0)) * 1.8))
    confidence_label = "HIGH" if confidence_score >= 80 else ("MEDIUM" if confidence_score >= 60 else "LOW")
    return pred, None, {
        "selected_model": chosen.upper(),
        "selection_mode": "AUTO" if requested == "auto" else "MANUAL",
        "selected_metrics": metrics,
        "model_metrics": recent_metrics,
        "confidence_score": round(confidence_score, 2),
        "confidence_label": confidence_label,
        "model_errors": model_errors,
    }


def analyze_logs(alert_df: pd.DataFrame) -> dict:
    if alert_df.empty:
        return {"total": 0, "recent_severe": 0, "avg_stability": None, "dominant_risk": "N/A", "summary": "No logs yet."}
    logs = alert_df.copy()
    logs["timestamp"] = pd.to_datetime(logs["timestamp"], utc=True, errors="coerce")
    logs["stability_index"] = pd.to_numeric(logs["stability_index"], errors="coerce")
    logs = logs.dropna(subset=["timestamp"]).sort_values("timestamp", ascending=False)
    recent = logs.head(min(30, len(logs)))
    severe = int(recent["risk_level"].isin({"CRITICAL", "EMERGENCY"}).sum())
    avg_stability = float(recent["stability_index"].mean()) if recent["stability_index"].notna().any() else None
    dominant = str(recent["risk_level"].value_counts().idxmax()) if not recent.empty else "N/A"
    summary = "Stable trend." if severe == 0 else "Potential pressure trend detected."
    return {
        "total": int(len(logs)),
        "recent_severe": severe,
        "avg_stability": avg_stability,
        "dominant_risk": dominant,
        "summary": summary,
        "display_df": logs,
    }


def compute_device_health_score(device_logs: pd.DataFrame) -> dict:
    if device_logs.empty:
        return {
            "score": 100.0,
            "severity": "NORMAL",
            "reasons": ["No external-device anomalies detected in recent logs."],
        }

    df = device_logs.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp", ascending=False).head(80)
    if df.empty:
        return {"score": 100.0, "severity": "NORMAL", "reasons": ["No valid device timestamps for anomaly scoring."]}

    disconnect_rate = float((df["event_type"] == "disconnected").mean())
    usage_series = pd.to_numeric(df.get("usage_percent"), errors="coerce")
    high_usage_ratio = float((usage_series > 85.0).mean()) if usage_series.notna().any() else 0.0
    churn_devices = 0
    for _, grp in df.groupby("device_id"):
        events = set(grp["event_type"].astype(str).str.lower().tolist())
        if "connected" in events and "disconnected" in events:
            churn_devices += 1
    churn_factor = min(1.0, churn_devices / 5.0)
    raw_anomaly = (disconnect_rate * 45.0) + (high_usage_ratio * 35.0) + (churn_factor * 20.0)
    score = max(0.0, min(100.0, 100.0 - raw_anomaly))

    reasons: list[str] = []
    if disconnect_rate >= 0.22:
        reasons.append("Frequent disconnect events detected recently.")
    if high_usage_ratio >= 0.35:
        reasons.append("High removable-storage utilization detected.")
    if churn_devices > 0:
        reasons.append(f"{churn_devices} device(s) show connect/disconnect churn pattern.")
    if not reasons:
        reasons.append("Device behavior is stable in recent cycles.")

    severity = "HIGH" if score < 45 else ("MEDIUM" if score < 72 else "NORMAL")
    return {"score": round(score, 2), "severity": severity, "reasons": reasons}


def get_current_connected_devices(device_logs: pd.DataFrame) -> pd.DataFrame:
    """Latest state per device_id to avoid inflated counts from snapshot rows."""
    if device_logs.empty or "device_id" not in device_logs.columns:
        return pd.DataFrame()
    df = device_logs.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp", ascending=False)
    latest_per_device = df.groupby("device_id", as_index=False).first()
    return latest_per_device[latest_per_device["is_connected"] == 1].copy()


def format_device_details(device_df: pd.DataFrame) -> pd.DataFrame:
    if device_df.empty:
        return device_df
    show = device_df.copy()
    cap = pd.to_numeric(show.get("capacity_bytes"), errors="coerce")
    used = pd.to_numeric(show.get("used_bytes"), errors="coerce")
    show["capacity_gb"] = (cap / (1024**3)).round(2)
    show["used_gb"] = (used / (1024**3)).round(2)
    show["free_gb"] = ((cap - used) / (1024**3)).round(2)
    show["usage_percent"] = pd.to_numeric(show.get("usage_percent"), errors="coerce").round(1)
    cols = [
        "timestamp",
        "device_type",
        "device_name",
        "mountpoint",
        "capacity_gb",
        "used_gb",
        "free_gb",
        "usage_percent",
        "source_os",
    ]
    for col in cols:
        if col not in show.columns:
            show[col] = None
    return show[cols]


def build_device_report_exports(device_report_df: pd.DataFrame) -> tuple[bytes, bytes, bytes]:
    csv_bytes = device_report_df.to_csv(index=False).encode("utf-8")
    json_bytes = device_report_df.to_json(orient="records", indent=2, force_ascii=False).encode("utf-8")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("connected_device_report.csv", csv_bytes)
        zf.writestr("connected_device_report.json", json_bytes)
    return csv_bytes, json_bytes, buffer.getvalue()


def render_kpi_cards(
    current_ram: float,
    predicted_ram: float | None,
    stability: float,
    risk_level: RiskLevel,
    active_devices: int,
    device_health_score: float,
) -> None:
    predicted_label = f"{predicted_ram:.2f}%" if predicted_ram is not None else "N/A"
    delta = ""
    if predicted_ram is not None:
        diff = predicted_ram - current_ram
        delta = f"{'+' if diff >= 0 else ''}{diff:.2f}% vs now"
    cards = [
        ("🖥️", "RAM Now", f"{current_ram:.2f}%", "Live memory usage right now."),
        ("📊", "Predicted RAM", predicted_label, delta or "Needs enough history to predict."),
        ("🧭", "Stability Score", f"{stability:.1f}/100", "Higher score means healthier memory behavior."),
        ("🚦", "Risk Status", risk_level.value, "Overall risk level based on RAM trend and pressure."),
        ("💽", "External Devices", str(active_devices), "Physically connected external devices right now."),
        ("🛡️", "Device Health", f"{device_health_score:.1f}/100", "Higher means fewer disconnect/churn patterns."),
    ]
    html = ['<div class="kpi-grid">']
    for icon, title, value, hint in cards:
        html.append(
            (
                '<div class="kpi-card">'
                f'<div class="kpi-title"><span class="kpi-chip">{icon}</span>{title}</div>'
                f'<div class="kpi-value">{value}</div>'
                f'<div class="kpi-hint">{hint}</div>'
                "</div>"
            )
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def build_system_health_summary(
    current_ram: float,
    predicted_ram: float | None,
    risk_level: RiskLevel,
    stability: float,
    active_devices: int,
) -> str:
    pred_part = "Prediction is warming up." if predicted_ram is None else f"Predicted RAM is {predicted_ram:.1f}%."
    pressure_msg = (
        "Memory pressure looks low."
        if risk_level == RiskLevel.NORMAL
        else "Memory pressure needs attention."
        if risk_level == RiskLevel.WARNING
        else "Memory pressure is high and should be reduced now."
    )
    device_msg = (
        "No external devices detected."
        if active_devices == 0
        else f"{active_devices} external device(s) currently connected."
    )
    return (
        f"Current RAM is {current_ram:.1f}% with stability {stability:.1f}/100. "
        f"{pred_part} {pressure_msg} {device_msg}"
    )


def render_action_panel(
    dos: list[str],
    donts: list[str],
    device_health_severity: str,
    predicted_ram: float | None,
    current_ram: float,
) -> None:
    quick_items: list[str] = []
    if predicted_ram is not None and predicted_ram > current_ram + 2.5:
        quick_items.append("Delay opening new heavy apps for a few minutes.")
    if device_health_severity in {"HIGH", "MEDIUM"}:
        quick_items.append("Safely eject any unused external drives or dongles.")
    quick_items.extend(dos[:2])
    if not quick_items:
        quick_items.append("System is healthy. Keep monitoring while working.")

    st.markdown('<div class="action-panel">', unsafe_allow_html=True)
    st.markdown('<div class="action-title">What Should I Do Now?</div>', unsafe_allow_html=True)
    st.markdown("<br/>".join(f"- {item}" for item in quick_items), unsafe_allow_html=True)
    if donts:
        st.caption("Avoid: " + "; ".join(donts[:2]))
    st.markdown("</div>", unsafe_allow_html=True)


def render_quick_nav() -> str:
    labels = {
        "Overview": "🏠 Overview",
        "Trends": "📈 Trends",
        "Devices": "🖱️ Devices",
        "Actions": "✅ Actions",
    }
    reverse_labels = {v: k for k, v in labels.items()}
    with st.sidebar:
        st.markdown("### ☰ Quick Navigation")
        current = st.session_state.get("quick_nav", "Overview")
        selected_label = st.radio(
            "Navigate",
            options=list(labels.values()),
            index=list(labels.keys()).index(current),
            key="quick_nav_sidebar",
            label_visibility="collapsed",
        )
        selected = reverse_labels.get(selected_label, "Overview")
        st.caption("Use the top-left hamburger icon to collapse/expand this menu.")
    st.session_state.quick_nav = selected
    return selected


def render_header(status_level: RiskLevel, monitoring_enabled: bool, theme_mode: str) -> bool:
    st.markdown('<div class="top-shell">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([5, 4, 2])
    with c1:
        st.markdown('<div class="title-main">🧠 NeuroRAM</div>', unsafe_allow_html=True)
        st.markdown('<div class="title-sub">Predictive Memory Management System for proactive stability</div>', unsafe_allow_html=True)
    with c2:
        dot = risk_color(status_level)
        text = "Monitoring ON" if monitoring_enabled else "Monitoring OFF"
        st.markdown(
            f'<div class="status-chip"><span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:{dot};"></span>{text} | {status_level.value}</div>',
            unsafe_allow_html=True,
        )
    with c3:
        icon = "🌙" if theme_mode == "Light" else "☀️"
        theme_toggle = st.button(icon, width="stretch", help="Toggle light/dark mode")
    st.markdown("</div>", unsafe_allow_html=True)
    return theme_toggle


def main() -> None:
    st.session_state.monitoring_enabled = True
    if "first_load" not in st.session_state:
        st.session_state.first_load = True
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "Dark"
    if "mobile_preview" not in st.session_state:
        st.session_state.mobile_preview = False
    if "quick_nav" not in st.session_state:
        st.session_state.quick_nav = "Overview"
    if "device_state" not in st.session_state:
        st.session_state.device_state = {}

    inject_styles(st.session_state.theme_mode, "Midnight Indigo", compact_mode=bool(st.session_state.mobile_preview))
    db = DatabaseManager()
    engine = MLEngine()

    status_seed = classify_risk(20.0, False).level
    theme_toggle_clicked = render_header(
        status_seed, st.session_state.monitoring_enabled, st.session_state.theme_mode
    )
    if theme_toggle_clicked:
        st.session_state.theme_mode = "Light" if st.session_state.theme_mode == "Dark" else "Dark"
        st.rerun()

    render_quick_nav()

    run_every = "4s"
    st.caption("Live refresh cadence: every 4 seconds.")

    @st.fragment(run_every=run_every)
    def live_runtime_fragment() -> None:
        tokens = get_theme_tokens(st.session_state.theme_mode, "Midnight Indigo")
        compact_mode = bool(st.session_state.mobile_preview)
        active_view = str(st.session_state.get("quick_nav", "Overview"))
        do_collect = True
        st.session_state.first_load = False

        system_row, process_df, device_events_df, current_device_state = collect_cycle(
            db=db,
            do_collect=do_collect,
            previous_devices=st.session_state.device_state,
        )
        st.session_state.device_state = current_device_state

        hist_system = db.fetch_system_metrics(limit=800)
        hist_memory = db.fetch_memory_logs(limit=800)
        device_logs = db.fetch_device_logs(limit=400)
        predictions = db.fetch_predictions(limit=400)
        alerts = db.fetch_alerts(limit=120)
        analysis_hist = db.fetch_analysis_results(limit=120)

        if system_row is None:
            st.info("No telemetry yet. Please wait for the first live collection cycle.")
            return

        hist_for_ml = enrich_hist_for_ml(hist_system, device_logs)
        predicted_ram, prediction_error, model_meta = train_predict(hist_for_ml, engine, "AUTO")

        active_model = model_meta.get("selected_model", "AUTO") if model_meta else "AUTO"
        train_metrics = model_meta.get("selected_metrics", {}) if model_meta else {}
        confidence_score = float(model_meta.get("confidence_score", 0.0) if model_meta else 0.0)
        confidence_label = str(model_meta.get("confidence_label", "LOW") if model_meta else "LOW")
        selection_mode = str(model_meta.get("selection_mode", "MANUAL") if model_meta else "MANUAL")

        current_ram = float(system_row["ram_percent"])
        device_pressure = float(device_events_df["event_type"].isin(["connected", "disconnected"]).sum()) if not device_events_df.empty else 0.0
        leak = detect_memory_leak(hist_system)
        risk_report = classify_risk(
            current_ram_percent=current_ram,
            leak_detected=leak,
            predicted_ram_percent=float(predicted_ram) if predicted_ram is not None else None,
            device_pressure_score=device_pressure,
        )
        effective = max(current_ram, float(predicted_ram) if predicted_ram is not None else current_ram)
        if effective >= CONFIG.emergency_threshold:
            risk_report.level = RiskLevel.EMERGENCY
        elif effective >= CONFIG.critical_threshold:
            risk_report.level = RiskLevel.CRITICAL
        elif effective >= CONFIG.warning_threshold:
            risk_report.level = RiskLevel.WARNING
        else:
            risk_report.level = RiskLevel.NORMAL
        stability = compute_stability_index(current_ram, float(system_row["swap_percent"]), risk_report.level)
        device_health = compute_device_health_score(device_logs)
        proc_source = process_df if not process_df.empty else db.fetch_recent_process_metrics(limit=CONFIG.process_limit)
        recs = greedy_optimization_strategy(proc_source, risk_report.level) if not proc_source.empty else []

        connected_devices = get_current_connected_devices(device_logs)
        active_count = int(len(connected_devices))
        report_source = connected_devices[connected_devices["device_type"].isin(["usb_drive", "input_dongle"])].copy()
        device_report_df = format_device_details(report_source)
        device_report_csv, device_report_json, device_report_zip = build_device_report_exports(device_report_df)

        if do_collect:
            if predicted_ram is not None:
                db.insert_prediction(str(system_row["timestamp"]), active_model.lower(), float(predicted_ram), current_ram)
            db.insert_alert(str(system_row["timestamp"]), risk_report.level.value, " | ".join(risk_report.reasons), stability)
            guidance = build_actionable_guidance(
                risk_level=risk_report.level,
                active_devices=active_count,
                recent_disconnects=int((device_logs["event_type"] == "disconnected").sum()) if not device_logs.empty else 0,
            )
            db.insert_analysis_result(
                timestamp=str(system_row["timestamp"]),
                risk_level=risk_report.level.value,
                causes=" | ".join(risk_report.reasons + guidance["causes"] + device_health["reasons"]),
                dos=" | ".join(risk_report.dos + guidance["dos"]),
                donts=" | ".join(risk_report.donts + guidance["donts"]),
                model_name=active_model,
                confidence=confidence_score,
                stability_index=stability,
            )
            analysis_hist = db.fetch_analysis_results(limit=120)
        backfill_status = read_backfill_status()

        if active_view == "Overview":
            summary_text = build_system_health_summary(
                current_ram=current_ram,
                predicted_ram=predicted_ram,
                risk_level=risk_report.level,
                stability=stability,
                active_devices=active_count,
            )
            st.markdown(
                (
                    '<div class="summary-banner">'
                    '<div class="summary-title">System Health Summary</div>'
                    f'<div class="summary-text">{summary_text}</div>'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

            st.markdown('<div class="section-title">Key Insight Cards</div>', unsafe_allow_html=True)
            render_kpi_cards(
                current_ram=current_ram,
                predicted_ram=predicted_ram,
                stability=stability,
                risk_level=risk_report.level,
                active_devices=active_count,
                device_health_score=float(device_health["score"]),
            )

            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("**What This Means (Plain Language)**")
            if predicted_ram is None:
                st.markdown("- The app is collecting real data now; prediction appears when enough history is available.")
            elif predicted_ram > current_ram + 2.5:
                st.markdown("- Memory usage may increase soon, so avoid opening extra heavy apps right now.")
            else:
                st.markdown("- Memory trend looks stable at this moment.")
            if active_count == 0:
                st.markdown("- No external storage/dongle is currently detected as connected.")
            else:
                st.markdown(f"- {active_count} external device(s) are physically connected right now.")
            st.markdown("- Blue and gold highlights mark healthy zones and warning zones for quick action.")
            st.markdown("</div>", unsafe_allow_html=True)
            render_action_panel(
                dos=risk_report.dos,
                donts=risk_report.donts,
                device_health_severity=str(device_health["severity"]),
                predicted_ram=predicted_ram,
                current_ram=current_ram,
            )

            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("**Backfill Status**")
            if backfill_status["available"]:
                st.caption(f"Last migration run: {backfill_status['ran_at_utc']}")
                b1, b2, b3 = st.columns(3)
                b1.metric("Memory logs added", str(backfill_status["memory_logs_added"]))
                b2.metric("Prediction logs added", str(backfill_status["prediction_logs_added"]))
                b3.metric("Analysis rows added", str(backfill_status["analysis_reports_added"]))
            else:
                st.info(backfill_status["message"])
            st.markdown("</div>", unsafe_allow_html=True)

        if active_view == "Trends":
            st.markdown('<div class="section-title">Live Trends</div>', unsafe_allow_html=True)
        if active_view == "Trends" and compact_mode:
            fig_ram = px.line(
                hist_memory.tail(180),
                x="timestamp",
                y=["ram_percent", "swap_percent"],
                color_discrete_sequence=[str(tokens["chart_actual"]), str(tokens["chart_pred"])],
            )
            st.plotly_chart(style_plot(fig_ram, "Real-time RAM Usage", st.session_state.theme_mode), width="stretch")
            trend_df = hist_memory.copy()
            trend_df["ram_smooth"] = trend_df["ram_percent"].rolling(12, min_periods=1).mean()
            fig_trend = px.line(
                trend_df.tail(240),
                x="timestamp",
                y=["ram_percent", "ram_smooth", "swap_percent"],
                color_discrete_sequence=[str(tokens["chart_actual"]), str(tokens["accent"]), str(tokens["chart_pred"])],
            )
            st.plotly_chart(style_plot(fig_trend, "Historical Memory Trend", st.session_state.theme_mode), width="stretch")
        elif active_view == "Trends":
            g1, g2 = st.columns(2)
            with g1:
                fig_ram = px.line(
                    hist_memory.tail(180),
                    x="timestamp",
                    y=["ram_percent", "swap_percent"],
                    color_discrete_sequence=[str(tokens["chart_actual"]), str(tokens["chart_pred"])],
                )
                st.plotly_chart(style_plot(fig_ram, "Real-time RAM Usage", st.session_state.theme_mode), width="stretch")
            with g2:
                trend_df = hist_memory.copy()
                trend_df["ram_smooth"] = trend_df["ram_percent"].rolling(12, min_periods=1).mean()
                fig_trend = px.line(
                    trend_df.tail(240),
                    x="timestamp",
                    y=["ram_percent", "ram_smooth", "swap_percent"],
                    color_discrete_sequence=[str(tokens["chart_actual"]), str(tokens["accent"]), str(tokens["chart_pred"])],
                )
                st.plotly_chart(style_plot(fig_trend, "Historical Memory Trend", st.session_state.theme_mode), width="stretch")

        if active_view == "Trends" and compact_mode:
            pred_plot = predictions.tail(180).copy()
            if not pred_plot.empty:
                fig_pred = px.line(
                    pred_plot,
                    x="timestamp",
                    y=["actual_ram_percent", "predicted_ram_percent"],
                    color_discrete_sequence=[str(tokens["chart_actual"]), str(tokens["chart_pred"])],
                )
                st.plotly_chart(style_plot(fig_pred, "Prediction vs Actual", st.session_state.theme_mode), width="stretch")
            else:
                st.info("Prediction graph appears after model inference cycles.")
        elif active_view == "Trends":
            g3 = st.columns(1)[0]
            with g3:
                pred_plot = predictions.tail(180).copy()
                if not pred_plot.empty:
                    fig_pred = px.line(
                        pred_plot,
                        x="timestamp",
                        y=["actual_ram_percent", "predicted_ram_percent"],
                        color_discrete_sequence=[str(tokens["chart_actual"]), str(tokens["chart_pred"])],
                    )
                    st.plotly_chart(style_plot(fig_pred, "Prediction vs Actual", st.session_state.theme_mode), width="stretch")
                else:
                    st.info("Prediction graph appears after model inference cycles.")

        if active_view == "Trends":
            gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=stability,
                    number={"suffix": "/100"},
                    title={"text": "Stability Gauge"},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": risk_color(risk_report.level)},
                        "steps": [
                            {"range": [0, 45], "color": "rgba(239,68,68,0.35)"},
                            {"range": [45, 70], "color": "rgba(245,158,11,0.3)"},
                            {"range": [70, 100], "color": "rgba(59,130,246,0.32)"},
                        ],
                    },
                )
            )
            st.plotly_chart(style_plot(gauge, "Stability Gauge", st.session_state.theme_mode, height=300), width="stretch")

        if active_view == "Devices":
            st.markdown('<div class="section-title">Connected Devices</div>', unsafe_allow_html=True)
            device_summary = db.fetch_device_activity_summary(limit=220)
            if device_summary.empty:
                st.info("No device activity yet.")
            else:
                fig_dev = px.line(
                    device_summary,
                    x="timestamp",
                    y=["active_devices", "connected_events", "disconnected_events"],
                    color_discrete_sequence=[str(tokens["accent"]), str(tokens["chart_pred"]), str(tokens["chart_actual"])],
                )
                st.plotly_chart(style_plot(fig_dev, "External Device Activity", st.session_state.theme_mode), width="stretch")
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown(
                "**Database Sync**  \nAll connected-device details and events are stored in SQLite table `device_logs` "
                "(including type, name, mountpoint, capacity/used bytes, and connection state)."
            )
            st.markdown("**Copy Device Report (currently connected storage + dongles)**")
            cexp1, cexp2, cexp3 = st.columns(3)
            cexp1.download_button(
                "CSV",
                data=device_report_csv,
                file_name="connected_device_report.csv",
                mime="text/csv",
                use_container_width=True,
            )
            cexp2.download_button(
                "JSON",
                data=device_report_json,
                file_name="connected_device_report.json",
                mime="application/json",
                use_container_width=True,
            )
            cexp3.download_button(
                "One Click (CSV+JSON)",
                data=device_report_zip,
                file_name="connected_device_report_bundle.zip",
                mime="application/zip",
                use_container_width=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)
            storage_devices = connected_devices[connected_devices["device_type"] == "usb_drive"].copy()
            dongle_devices = connected_devices[connected_devices["device_type"] == "input_dongle"].copy()
            storage_details = format_device_details(storage_devices)
            dongle_details = format_device_details(dongle_devices)
        if active_view == "Devices" and compact_mode:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("**Storage Devices (with capacity details)**")
            if storage_details.empty:
                st.info("No external storage device is currently connected.")
            else:
                st.dataframe(storage_details.head(20), width="stretch", hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("**Mouse/Keyboard Dongles**")
            if dongle_details.empty:
                st.info("No mouse/keyboard dongle detected right now.")
            else:
                st.dataframe(dongle_details.head(20), width="stretch", hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("**Recent Device Event Logs**")
            if device_logs.empty:
                st.info("Device logs will appear after monitoring cycles.")
            else:
                st.dataframe(device_logs.head(40), width="stretch", hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
        elif active_view == "Devices":
            d1, d2 = st.columns([1.35, 1.65])
            with d1:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown("**Storage Devices (with capacity details)**")
                if storage_details.empty:
                    st.info("No external storage device is currently connected.")
                else:
                    st.dataframe(storage_details.head(20), width="stretch", hide_index=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with d2:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown("**Mouse/Keyboard Dongles**")
                if dongle_details.empty:
                    st.info("No mouse/keyboard dongle detected right now.")
                else:
                    st.dataframe(dongle_details.head(20), width="stretch", hide_index=True)
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown("**Recent Device Event Logs**")
                if device_logs.empty:
                    st.info("Device logs will appear after monitoring cycles.")
                else:
                    st.dataframe(device_logs.head(40), width="stretch", hide_index=True)
                st.markdown("</div>", unsafe_allow_html=True)

        if active_view == "Actions":
            st.markdown('<div class="section-title">Activity Timeline</div>', unsafe_allow_html=True)
        if active_view == "Actions" and compact_mode:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            log_summary = analyze_logs(alerts)
            st.metric("Total Alert Logs", log_summary["total"])
            st.metric("Recent Severe", log_summary["recent_severe"])
            st.metric("Dominant Risk", log_summary["dominant_risk"])
            st.caption(log_summary["summary"])
            if not alerts.empty:
                st.dataframe(alerts.head(25), width="stretch", hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            if not analysis_hist.empty:
                st.dataframe(analysis_hist.head(25), width="stretch", hide_index=True)
            else:
                st.info("Analysis logs will appear after active monitoring cycles.")
            st.markdown("</div>", unsafe_allow_html=True)
        elif active_view == "Actions":
            l1, l2 = st.columns(2)
            with l1:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                log_summary = analyze_logs(alerts)
                st.metric("Total Alert Logs", log_summary["total"])
                st.metric("Recent Severe", log_summary["recent_severe"])
                st.metric("Dominant Risk", log_summary["dominant_risk"])
                st.caption(log_summary["summary"])
                if not alerts.empty:
                    st.dataframe(alerts.head(25), width="stretch", hide_index=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with l2:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                if not analysis_hist.empty:
                    st.dataframe(analysis_hist.head(25), width="stretch", hide_index=True)
                else:
                    st.info("Analysis logs will appear after active monitoring cycles.")
                st.markdown("</div>", unsafe_allow_html=True)

        if active_view == "Actions":
            st.markdown('<div class="section-title">Detailed Diagnostics</div>', unsafe_allow_html=True)
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown(f"**Risk Level:** `{risk_report.level.value}`")
            st.markdown(f"**Model:** `{active_model}` ({selection_mode})")
            st.markdown(f"**Device Health Severity:** `{device_health['severity']}`")
            badge = "confidence-high" if confidence_label == "HIGH" else ("confidence-medium" if confidence_label == "MEDIUM" else "confidence-low")
            st.markdown(
                f'<span class="confidence-badge {badge}">Model Confidence: {confidence_score:.2f}% ({confidence_label})</span>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="analysis-block"><strong>Causes</strong><br/>{"<br/>".join("- " + reason for reason in (risk_report.reasons + device_health["reasons"]))}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="analysis-block"><strong>Do\'s</strong><br/>{"<br/>".join("- " + item for item in risk_report.dos)}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="analysis-block"><strong>Don\'ts</strong><br/>{"<br/>".join("- " + item for item in risk_report.donts)}</div>',
                unsafe_allow_html=True,
            )
            if recs:
                st.markdown(
                    '<div class="analysis-block"><strong>Top Optimization Suggestions</strong><br/>'
                    + "<br/>".join([f"- {rec.process_name} (PID {rec.pid}): {rec.recommendation}" for rec in recs[:3]])
                    + "</div>",
                    unsafe_allow_html=True,
                )
            if train_metrics:
                st.caption(
                    f"Model validation: MAE {train_metrics.get('mae', 'n/a')} | RMSE {train_metrics.get('rmse', 'n/a')} | R² {train_metrics.get('r2', 'n/a')}"
                )
            if prediction_error:
                st.warning(prediction_error)
            st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("Download Data"):
            system_csv = hist_system.to_csv(index=False).encode("utf-8")
            device_logs_csv = device_logs.to_csv(index=False).encode("utf-8")
            predictions_csv = predictions.to_csv(index=False).encode("utf-8")
            alerts_csv = alerts.to_csv(index=False).encode("utf-8")
            analysis_csv = analysis_hist.to_csv(index=False).encode("utf-8")

            full_bundle_buffer = io.BytesIO()
            with zipfile.ZipFile(full_bundle_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("system_metrics.csv", system_csv)
                zf.writestr("device_logs.csv", device_logs_csv)
                zf.writestr("predictions.csv", predictions_csv)
                zf.writestr("alerts.csv", alerts_csv)
                zf.writestr("analysis_results.csv", analysis_csv)
                zf.writestr("connected_device_report.csv", device_report_csv)
                zf.writestr("connected_device_report.json", device_report_json)

            st.download_button("System Metrics CSV", system_csv, "system_metrics.csv", "text/csv")
            st.download_button("Device Logs CSV", device_logs_csv, "device_logs.csv", "text/csv")
            st.download_button(
                "Download Everything (ZIP)",
                full_bundle_buffer.getvalue(),
                "neuroram_full_export.zip",
                "application/zip",
            )
        st.caption(f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")

    live_runtime_fragment()


if __name__ == "__main__":
    main()
