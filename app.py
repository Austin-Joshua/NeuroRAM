"""NeuroRAM - redesigned modern interactive dashboard."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from neuroram.backend.daa.optimizer import greedy_optimization_strategy
from neuroram.backend.daa.risk_analyzer import RiskLevel, classify_risk, detect_memory_leak
from neuroram.backend.daa.stability_index import compute_stability_index
from neuroram.backend.dbms.database import DatabaseManager
from neuroram.backend.mlt.ml_engine import MLEngine, TENSORFLOW_AVAILABLE
from neuroram.backend.mlt.predictor import predict_next_ram
from neuroram.backend.os.collector import collect_process_metrics, collect_system_metrics
from neuroram.config.config import CONFIG


st.set_page_config(page_title="NeuroRAM", page_icon="🧠", layout="wide")


def risk_color(level: RiskLevel) -> str:
    return {
        RiskLevel.NORMAL: "#22C55E",
        RiskLevel.WARNING: "#F59E0B",
        RiskLevel.CRITICAL: "#EF4444",
        RiskLevel.EMERGENCY: "#EF4444",
    }[level]


def inject_styles(theme_mode: str) -> None:
    is_light = theme_mode == "Light"
    bg_gradient = (
        "radial-gradient(circle at 12% 15%, #dbeafe 0%, #f8fafc 45%, #eef2ff 100%)"
        if is_light
        else "radial-gradient(circle at 12% 15%, #1d2b64 0%, #0f172a 42%, #101a33 100%)"
    )
    text_color = "#0f172a" if is_light else "#e2e8f0"
    sub_text_color = "#334155" if is_light else "#cbd5e1"
    title_color = "#0b1220" if is_light else "#f8fafc"
    metric_label_color = "#334155" if is_light else "#cbd5e1"
    metric_value_color = "#0f172a" if is_light else "#f8fafc"
    caption_color = "#334155" if is_light else "#94a3b8"
    status_bg = "rgba(255,255,255,0.85)" if is_light else "rgba(15,23,42,0.55)"
    top_shadow = "0 8px 20px rgba(148,163,184,0.28)" if is_light else "0 10px 30px rgba(2, 6, 23, 0.45)"
    card_shadow = "0 8px 18px rgba(148,163,184,0.22)" if is_light else "0 10px 24px rgba(2, 6, 23, 0.35)"
    card_hover_shadow = "0 12px 20px rgba(148,163,184,0.30)" if is_light else "0 14px 28px rgba(2, 6, 23, 0.48)"
    analysis_border = "rgba(37,99,235,0.72)" if is_light else "rgba(0,245,255,0.7)"
    glass_bg = (
        "linear-gradient(120deg, rgba(37,99,235,0.10) 0%, rgba(255,255,255,0.92) 52%, rgba(250,204,21,0.10) 100%)"
        if is_light
        else "linear-gradient(120deg, rgba(0,245,255,0.10) 0%, rgba(15,23,42,0.72) 58%, rgba(99,102,241,0.16) 100%)"
    )
    top_bg = (
        "linear-gradient(110deg, rgba(59,130,246,0.22) 0%, rgba(255,255,255,0.80) 55%, rgba(234,179,8,0.16) 100%)"
        if is_light
        else "linear-gradient(110deg, rgba(99,102,241,0.24) 0%, rgba(15,23,42,0.72) 55%, rgba(0,245,255,0.20) 100%)"
    )
    css = """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        .stApp {
            font-family: 'Inter', sans-serif;
            color: __TEXT_COLOR__;
            background: __BG_GRADIENT__;
        }
        .block-container {
            max-width: 1380px;
            padding-top: 0.75rem;
            padding-bottom: 1rem;
        }
        [data-testid="stVerticalBlock"] > [data-testid="element-container"] { margin-bottom: 0.25rem; }
        [data-testid="column"] { padding-top: 0.05rem; }
        [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

        .top-shell {
            border: 1px solid rgba(148, 163, 184, 0.25);
            border-radius: 18px;
            padding: 0.7rem 0.9rem;
            margin-bottom: 0.55rem;
            backdrop-filter: blur(10px);
            background: __TOP_BG__;
            box-shadow: __TOP_SHADOW__;
        }
        .title-main { font-size: clamp(1.28rem, 1.4vw, 1.65rem); font-weight: 700; letter-spacing: 0.015em; line-height: 1.15; color: __TITLE_COLOR__; }
        .title-sub { font-size: clamp(0.80rem, 0.92vw, 0.94rem); color: __SUB_TEXT_COLOR__; font-weight: 500; line-height: 1.25; }

        .status-chip {
            border-radius: 999px;
            border: 1px solid rgba(148, 163, 184, 0.3);
            padding: 0.38rem 0.74rem;
            font-size: clamp(0.74rem, 0.85vw, 0.88rem);
            font-weight: 600;
            background: __STATUS_BG__;
            display: inline-flex;
            align-items: center;
            gap: 0.42rem;
        }
        .pulse-dot {
            width: 10px; height: 10px; border-radius: 50%;
            display: inline-block;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(0, 245, 255, 0.35); }
            70% { box-shadow: 0 0 0 12px rgba(0, 245, 255, 0); }
            100% { box-shadow: 0 0 0 0 rgba(0, 245, 255, 0); }
        }

        .glass-card {
            border-radius: 16px;
            border: 1px solid rgba(148, 163, 184, 0.22);
            background: __GLASS_BG__;
            padding: 0.74rem 0.88rem;
            backdrop-filter: blur(8px);
            box-shadow: __CARD_SHADOW__;
            margin-bottom: 0.58rem;
            transition: transform .2s ease, box-shadow .2s ease;
        }
        .glass-card:hover {
            transform: translateY(-2px);
            box-shadow: __CARD_HOVER_SHADOW__;
        }
        .metric-card {
            min-height: 102px;
            display: flex;
            align-items: center;
        }
        .section-title {
            font-size: clamp(0.74rem, 0.85vw, 0.86rem);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-weight: 700;
            color: __SUB_TEXT_COLOR__;
            margin: 0.2rem 0 0.32rem 0;
        }
        [data-testid="stMetricLabel"] p {
            color: __METRIC_LABEL_COLOR__;
            font-weight: 600;
            letter-spacing: 0.01em;
            font-size: clamp(0.72rem, 0.84vw, 0.86rem);
        }
        [data-testid="stMetricValue"] {
            color: __METRIC_VALUE_COLOR__;
            font-weight: 700;
            font-size: clamp(1.22rem, 1.34vw, 1.5rem);
            line-height: 1.15;
        }
        [data-testid="stCaptionContainer"] {
            color: __CAPTION_COLOR__;
            font-weight: 500;
            font-size: clamp(0.7rem, 0.78vw, 0.8rem);
        }
        .stButton > button, .stDownloadButton > button {
            font-size: clamp(0.74rem, 0.86vw, 0.9rem);
            min-height: 2.2rem;
        }
        .stSelectbox label, .stNumberInput label, .stTextInput label, .stToggle label {
            font-size: clamp(0.74rem, 0.84vw, 0.88rem);
            font-weight: 600;
        }
        .analysis-block {
            border-left: 3px solid __ANALYSIS_BORDER__;
            padding-left: 0.62rem;
            margin-bottom: 0.42rem;
            font-size: clamp(0.78rem, 0.9vw, 0.92rem);
            line-height: 1.35;
        }
        .confidence-badge {
            display: inline-block;
            border-radius: 999px;
            padding: 0.24rem 0.62rem;
            font-size: clamp(0.7rem, 0.8vw, 0.8rem);
            font-weight: 700;
            margin-top: 0.2rem;
            margin-bottom: 0.2rem;
            border: 1px solid transparent;
        }
        @media (max-width: 1280px) {
            .top-shell { padding: 0.62rem 0.78rem; }
            .glass-card { padding: 0.66rem 0.76rem; }
            .metric-card { min-height: 96px; }
        }
        @media (max-width: 1024px) {
            .block-container { padding-top: 0.6rem; }
            .top-shell { margin-bottom: 0.45rem; }
            .section-title { margin-bottom: 0.25rem; }
        }
        .confidence-high {
            background: rgba(34, 197, 94, 0.18);
            color: #22c55e;
            border-color: rgba(34, 197, 94, 0.35);
        }
        .confidence-medium {
            background: rgba(245, 158, 11, 0.18);
            color: #f59e0b;
            border-color: rgba(245, 158, 11, 0.35);
        }
        .confidence-low {
            background: rgba(239, 68, 68, 0.16);
            color: #ef4444;
            border-color: rgba(239, 68, 68, 0.35);
        }
        </style>
        """
    css = (
        css.replace("__TEXT_COLOR__", text_color)
        .replace("__BG_GRADIENT__", bg_gradient)
        .replace("__TOP_BG__", top_bg)
        .replace("__SUB_TEXT_COLOR__", sub_text_color)
        .replace("__TITLE_COLOR__", title_color)
        .replace("__METRIC_LABEL_COLOR__", metric_label_color)
        .replace("__METRIC_VALUE_COLOR__", metric_value_color)
        .replace("__CAPTION_COLOR__", caption_color)
        .replace("__GLASS_BG__", glass_bg)
        .replace("__STATUS_BG__", status_bg)
        .replace("__TOP_SHADOW__", top_shadow)
        .replace("__CARD_SHADOW__", card_shadow)
        .replace("__CARD_HOVER_SHADOW__", card_hover_shadow)
        .replace("__ANALYSIS_BORDER__", analysis_border)
    )
    st.markdown(
        css,
        unsafe_allow_html=True,
    )


def style_plot(fig: go.Figure, title: str, theme_mode: str) -> go.Figure:
    is_light = theme_mode == "Light"
    fig.update_layout(
        title=title,
        height=350,
        margin=dict(l=12, r=12, t=48, b=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.03)" if is_light else "rgba(255,255,255,0.03)",
        font=dict(color="#0f172a" if is_light else "#e2e8f0"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#334155" if is_light else "#cbd5e1")),
        xaxis=dict(showgrid=True, gridcolor="rgba(51,65,85,0.18)" if is_light else "rgba(148,163,184,0.14)", zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(51,65,85,0.18)" if is_light else "rgba(148,163,184,0.14)", zeroline=False),
    )
    return fig


def generate_data(db: DatabaseManager, sample_count: int = 70) -> None:
    base = collect_system_metrics()
    rng = np.random.default_rng()
    now = datetime.now(timezone.utc)
    for i in range(sample_count):
        ts = (now - timedelta(seconds=(sample_count - i) * 2)).isoformat()
        ram = float(np.clip(base["ram_percent"] + rng.normal(0, 2.0), 30.0, 95.0))
        cpu = float(np.clip(base["cpu_percent"] + rng.normal(0, 7.5), 2.0, 98.0))
        swap = float(np.clip(base["swap_percent"] + rng.normal(0, 1.4), 0.0, 98.0))
        row = {
            "timestamp": ts,
            "cpu_percent": cpu,
            "ram_total_mb": base["ram_total_mb"],
            "ram_used_mb": (ram / 100.0) * base["ram_total_mb"],
            "ram_percent": ram,
            "swap_total_mb": base["swap_total_mb"],
            "swap_used_mb": (swap / 100.0) * base["swap_total_mb"],
            "swap_percent": swap,
            "available_mb": max(1.0, base["ram_total_mb"] - ((ram / 100.0) * base["ram_total_mb"])),
        }
        db.insert_system_metric(row)


def collect_cycle(db: DatabaseManager, do_collect: bool) -> tuple[dict | None, pd.DataFrame]:
    if do_collect:
        system_row = collect_system_metrics()
        process_rows = collect_process_metrics(limit=CONFIG.process_limit)
        db.insert_system_metric(system_row)
        db.insert_process_metrics(process_rows)
        return system_row, pd.DataFrame(process_rows)

    hist_one = db.fetch_system_metrics(limit=1)
    if hist_one.empty:
        return None, pd.DataFrame()
    process_hist = db.fetch_recent_process_metrics(limit=CONFIG.process_limit)
    return hist_one.iloc[-1].to_dict(), process_hist


def train_predict(
    hist_df: pd.DataFrame,
    engine: MLEngine,
    requested_model: str,
) -> tuple[float | None, str | None, dict | None]:
    if len(hist_df) < 40:
        return None, "Need at least 40 samples. Click Generate Data.", None
    try:
        recent_metrics = st.session_state.get("recent_model_metrics", {})
        if not isinstance(recent_metrics, dict):
            recent_metrics = {}
        st.session_state.recent_model_metrics = recent_metrics

        def model_paths(model_choice: str) -> tuple[str, str]:
            if model_choice == "lstm":
                return CONFIG.lstm_model_path, CONFIG.lstm_scaler_path
            return CONFIG.rf_model_path, CONFIG.rf_scaler_path

        def maybe_train(model_choice: str) -> tuple[dict | None, str | None]:
            model_path, scaler_path = model_paths(model_choice)
            gate_key = f"last_{model_choice}_train_size"
            ready_key = f"model_ready_{model_choice}"
            last_train_size = int(st.session_state.get(gate_key, -1))
            needs_retrain = (
                len(hist_df) - last_train_size >= 25
                or last_train_size < 0
                or not st.session_state.get(ready_key, False)
                or not Path(model_path).exists()
                or not Path(scaler_path).exists()
                or model_choice not in recent_metrics
            )
            if not needs_retrain:
                return recent_metrics.get(model_choice), None

            try:
                if model_choice == "lstm":
                    metrics = engine.train_lstm(hist_df, epochs=12)
                else:
                    metrics = engine.train_random_forest(hist_df)
            except Exception as exc:
                return None, str(exc)

            st.session_state[gate_key] = len(hist_df)
            st.session_state[ready_key] = True
            recent_metrics[model_choice] = metrics
            st.session_state.recent_model_metrics = recent_metrics
            return metrics, None

        def model_score(metrics: dict | None) -> tuple[float, float]:
            if not metrics:
                return -1.0, -float("inf")
            r2 = float(metrics.get("r2", -1.0))
            rmse = float(metrics.get("rmse", float("inf")))
            return r2, -rmse

        requested = requested_model.lower()
        candidate_models: list[str]
        if requested == "auto":
            candidate_models = ["rf"]
            if TENSORFLOW_AVAILABLE and len(hist_df) >= 60:
                candidate_models.append("lstm")
        else:
            candidate_models = [requested]

        model_errors: dict[str, str] = {}
        for model in candidate_models:
            metrics, err = maybe_train(model)
            if err:
                model_errors[model] = err
            elif metrics:
                recent_metrics[model] = metrics

        if requested == "auto":
            available_models = [m for m in candidate_models if m in recent_metrics]
            if not available_models:
                return None, "No trained model available for auto-selection yet.", None
            selected_model = sorted(available_models, key=lambda m: model_score(recent_metrics[m]), reverse=True)[0]
        else:
            selected_model = requested
            if selected_model == "lstm" and (not TENSORFLOW_AVAILABLE or len(hist_df) < 60):
                selected_model = "rf"
            if selected_model not in recent_metrics:
                metrics, err = maybe_train(selected_model)
                if err:
                    return None, err, None
                if metrics:
                    recent_metrics[selected_model] = metrics

        prediction = float(predict_next_ram(hist_df, model_choice=selected_model))
        selected_metrics = recent_metrics.get(selected_model)

        if selected_metrics:
            r2 = float(selected_metrics.get("r2", 0.0))
            rmse = float(selected_metrics.get("rmse", 0.0))
            confidence_score = max(0.0, min(100.0, (r2 * 100.0) - (rmse * 1.8)))
        else:
            confidence_score = 0.0

        if confidence_score >= 80:
            confidence_label = "HIGH"
        elif confidence_score >= 60:
            confidence_label = "MEDIUM"
        else:
            confidence_label = "LOW"

        return (
            prediction,
            None,
            {
                "selected_model": selected_model.upper(),
                "selected_metrics": selected_metrics,
                "model_metrics": recent_metrics,
                "requested_model": requested.upper(),
                "selection_mode": "AUTO" if requested == "auto" else "MANUAL",
                "confidence_score": round(confidence_score, 2),
                "confidence_label": confidence_label,
                "model_errors": model_errors,
            },
        )
    except Exception as exc:
        return None, str(exc), None


def classify_with_ui_thresholds(
    effective_ram: float,
    leak_detected: bool,
    warning_threshold: float,
    critical_threshold: float,
    emergency_threshold: float,
) -> RiskLevel:
    if effective_ram >= emergency_threshold:
        return RiskLevel.EMERGENCY
    if effective_ram >= critical_threshold:
        return RiskLevel.CRITICAL
    if effective_ram >= warning_threshold:
        return RiskLevel.WARNING
    return RiskLevel.WARNING if leak_detected else RiskLevel.NORMAL


def analyze_logs(alert_df: pd.DataFrame) -> dict:
    if alert_df.empty:
        return {
            "summary": "No logs captured yet. Start monitoring and refresh data.",
            "total": 0,
            "recent_severe": 0,
            "avg_stability": None,
            "dominant_risk": "N/A",
            "latest_message": "",
            "suggestion": "Generate data and run monitoring to start analysis.",
            "display_df": alert_df,
        }

    df = alert_df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp", ascending=False)
    df = df.drop_duplicates(subset=["timestamp", "risk_level", "message"])
    df["stability_index"] = pd.to_numeric(df["stability_index"], errors="coerce")

    recent_df = df.head(min(25, len(df)))
    severe_levels = {"CRITICAL", "EMERGENCY"}
    recent_severe = int(recent_df["risk_level"].isin(severe_levels).sum())
    avg_stability = float(recent_df["stability_index"].mean()) if recent_df["stability_index"].notna().any() else None
    dominant_risk = str(recent_df["risk_level"].value_counts().idxmax()) if not recent_df.empty else "N/A"
    latest_message = str(recent_df.iloc[0]["message"]) if not recent_df.empty else ""

    if recent_severe >= 4 or (avg_stability is not None and avg_stability < 45):
        summary = "High risk trend detected in recent logs."
        suggestion = "Apply optimization suggestions now and monitor every refresh cycle."
    elif dominant_risk in {"WARNING", "CRITICAL"}:
        summary = "Moderate pressure trend detected from recent logs."
        suggestion = "Reduce non-essential workload and keep auto-refresh enabled."
    else:
        summary = "System log trend is stable."
        suggestion = "Continue current settings and monitor for sudden spikes."

    return {
        "summary": summary,
        "total": int(len(df)),
        "recent_severe": recent_severe,
        "avg_stability": avg_stability,
        "dominant_risk": dominant_risk,
        "latest_message": latest_message,
        "suggestion": suggestion,
        "display_df": df,
    }


def render_top_bar(status_level: RiskLevel, monitoring_enabled: bool) -> tuple[bool, bool, bool]:
    st.markdown('<div class="top-shell">', unsafe_allow_html=True)
    c_left, c_mid, c_right = st.columns([4, 3, 4])

    with c_left:
        st.markdown('<div class="title-main">NeuroRAM</div>', unsafe_allow_html=True)
        st.markdown('<div class="title-sub">Intelligent Predictive Memory Optimization System</div>', unsafe_allow_html=True)
    with c_mid:
        dot_color = risk_color(status_level)
        st.markdown(
            f'<div class="status-chip"><span class="pulse-dot" style="background:{dot_color};"></span> Live Status: {status_level.value}</div>',
            unsafe_allow_html=True,
        )
    with c_right:
        b1, b2, b3 = st.columns(3)
        start_clicked = b1.button("Start", width="stretch")
        stop_clicked = b2.button("Stop", width="stretch")
        generate_clicked = b3.button("Generate Data", width="stretch")

    st.markdown("</div>", unsafe_allow_html=True)
    return start_clicked, stop_clicked, generate_clicked


def main() -> None:
    if "monitoring_enabled" not in st.session_state:
        st.session_state.monitoring_enabled = True
    if "auto_refresh" not in st.session_state:
        st.session_state.auto_refresh = False
    if "refresh_interval" not in st.session_state:
        st.session_state.refresh_interval = 4
    if "warning_threshold" not in st.session_state:
        st.session_state.warning_threshold = int(CONFIG.warning_threshold)
    if "critical_threshold" not in st.session_state:
        st.session_state.critical_threshold = int(CONFIG.critical_threshold)
    if "emergency_threshold" not in st.session_state:
        st.session_state.emergency_threshold = int(CONFIG.emergency_threshold)
    if "first_load" not in st.session_state:
        st.session_state.first_load = True
    if "manual_refresh_requested" not in st.session_state:
        st.session_state.manual_refresh_requested = True
    if "last_data_pull_ts" not in st.session_state:
        st.session_state.last_data_pull_ts = 0.0
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "Dark"
    if "model_choice" not in st.session_state:
        st.session_state.model_choice = "AUTO"

    inject_styles(st.session_state.theme_mode)
    db = DatabaseManager()
    engine = MLEngine()

    status_seed = classify_risk(20.0, False).level
    start_clicked, stop_clicked, generate_clicked = render_top_bar(status_seed, st.session_state.monitoring_enabled)
    if start_clicked:
        st.session_state.monitoring_enabled = True
    if stop_clicked:
        st.session_state.monitoring_enabled = False
    if generate_clicked:
        generate_data(db, sample_count=80)

    previous_theme_mode = st.session_state.theme_mode
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    ctl1, ctl2, ctl3, ctl4, ctl5, ctl6, ctl7, ctl8 = st.columns([1.1, 1.0, 0.95, 0.95, 0.9, 0.9, 0.9, 0.9])
    with ctl1:
        refresh_now = st.button("Refresh Data", width="stretch")
        if refresh_now:
            st.session_state.manual_refresh_requested = True
    with ctl2:
        st.session_state.auto_refresh = st.toggle("Auto-refresh", value=st.session_state.auto_refresh, key="auto_refresh_toggle")
    with ctl3:
        st.session_state.refresh_interval = st.selectbox(
            "Interval (s)",
            options=[2, 3, 4, 5, 6, 8],
            index=[2, 3, 4, 5, 6, 8].index(st.session_state.refresh_interval)
            if st.session_state.refresh_interval in [2, 3, 4, 5, 6, 8]
            else 2,
            key="refresh_interval_select",
        )
    with ctl4:
        st.session_state.warning_threshold = st.number_input(
            "Warning",
            min_value=50,
            max_value=90,
            value=st.session_state.warning_threshold,
            key="warning_threshold_input",
        )
    with ctl5:
        st.session_state.critical_threshold = st.number_input(
            "Critical",
            min_value=60,
            max_value=95,
            value=st.session_state.critical_threshold,
            key="critical_threshold_input",
        )
    with ctl6:
        st.session_state.emergency_threshold = st.number_input(
            "Emergency",
            min_value=70,
            max_value=99,
            value=st.session_state.emergency_threshold,
            key="emergency_threshold_input",
        )
    with ctl7:
        st.session_state.theme_mode = st.selectbox(
            "Theme",
            options=["Dark", "Light"],
            index=0 if st.session_state.theme_mode == "Dark" else 1,
            key="theme_mode_select",
        )
    with ctl8:
        model_options = ["AUTO (best validation)", "RF", "LSTM (auto-fallback RF)"]
        selected_model = st.selectbox(
            "Model",
            options=model_options,
            index=0 if st.session_state.model_choice == "AUTO" else (1 if st.session_state.model_choice == "RF" else 2),
            key="model_choice_select",
        )
        if selected_model.startswith("AUTO"):
            st.session_state.model_choice = "AUTO"
        elif selected_model.startswith("RF"):
            st.session_state.model_choice = "RF"
        else:
            st.session_state.model_choice = "LSTM"
    st.caption("Data refresh updates metrics/charts only. No forced full-page timed rerun.")
    st.markdown("</div>", unsafe_allow_html=True)
    if st.session_state.theme_mode != previous_theme_mode:
        st.rerun()

    if st.session_state.auto_refresh and st.session_state.monitoring_enabled:
        now_ts = time.time()
        if now_ts - float(st.session_state.last_data_pull_ts) >= float(st.session_state.refresh_interval):
            st.session_state.manual_refresh_requested = True

    should_collect = st.session_state.monitoring_enabled and (
        st.session_state.manual_refresh_requested or st.session_state.first_load or generate_clicked
    )
    st.session_state.first_load = False
    if should_collect:
        st.session_state.manual_refresh_requested = False
        st.session_state.last_data_pull_ts = time.time()

    system_row, proc_df = collect_cycle(db, should_collect)
    hist_df = db.fetch_system_metrics(limit=700)
    pred_df = db.fetch_predictions(limit=350)
    alert_df = db.fetch_alerts(limit=50)
    if system_row is None:
        st.info("No data available yet. Click Generate Data or Start + Refresh Data.")
        return

    predicted_ram, prediction_error, model_meta = train_predict(
        hist_df, engine, requested_model=st.session_state.model_choice
    )
    active_model = model_meta.get("selected_model", st.session_state.model_choice) if model_meta else st.session_state.model_choice
    train_metrics = model_meta.get("selected_metrics") if model_meta else None
    confidence_score = model_meta.get("confidence_score", 0.0) if model_meta else 0.0
    confidence_label = model_meta.get("confidence_label", "LOW") if model_meta else "LOW"
    selection_mode = model_meta.get("selection_mode", "MANUAL") if model_meta else "MANUAL"
    current_ram = float(system_row["ram_percent"])
    effective_ram = max(current_ram, float(predicted_ram) if predicted_ram is not None else current_ram)
    leak_detected = detect_memory_leak(hist_df)
    risk_report = classify_risk(effective_ram, leak_detected=leak_detected)
    risk_report.level = classify_with_ui_thresholds(
        effective_ram=effective_ram,
        leak_detected=leak_detected,
        warning_threshold=float(st.session_state.warning_threshold),
        critical_threshold=float(st.session_state.critical_threshold),
        emergency_threshold=float(st.session_state.emergency_threshold),
    )
    risk_report.reasons = [
        f"Effective RAM considered: {effective_ram:.2f}% (current {current_ram:.2f}%"
        + (f", predicted {predicted_ram:.2f}%" if predicted_ram is not None else "")
        + ").",
        (
            f"Threshold rule hit: warning {st.session_state.warning_threshold}%, "
            f"critical {st.session_state.critical_threshold}%, emergency {st.session_state.emergency_threshold}%."
        ),
    ]
    if leak_detected:
        risk_report.reasons.append("RAM growth trend indicates potential memory leak behavior.")

    stability = compute_stability_index(
        ram_percent=current_ram,
        cpu_percent=float(system_row["cpu_percent"]),
        swap_percent=float(system_row["swap_percent"]),
        risk_level=risk_report.level,
    )

    if predicted_ram is not None:
        db.insert_prediction(str(system_row["timestamp"]), active_model.lower(), predicted_ram, current_ram)
    db.insert_alert(str(system_row["timestamp"]), risk_report.level.value, " | ".join(risk_report.reasons), stability)

    st.markdown('<div class="section-title">Quick Metrics</div>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown('<div class="glass-card metric-card">', unsafe_allow_html=True)
        st.metric("RAM Usage", f"{current_ram:.2f}%")
        st.markdown("</div>", unsafe_allow_html=True)
    with m2:
        st.markdown('<div class="glass-card metric-card">', unsafe_allow_html=True)
        st.metric("Predicted RAM", f"{predicted_ram:.2f}%" if predicted_ram is not None else "N/A")
        st.markdown("</div>", unsafe_allow_html=True)
    with m3:
        st.markdown('<div class="glass-card metric-card">', unsafe_allow_html=True)
        st.metric("CPU Usage", f"{float(system_row['cpu_percent']):.2f}%")
        st.markdown("</div>", unsafe_allow_html=True)
    with m4:
        st.markdown('<div class="glass-card metric-card">', unsafe_allow_html=True)
        st.metric("Stability Score", f"{stability:.2f}/100")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-title">Main Visualization (Bento Layout)</div>', unsafe_allow_html=True)
    lookback = st.slider("Prediction time filter (latest points)", min_value=30, max_value=300, value=120, step=10)
    pred_show = pred_df.tail(lookback).copy()

    # Bento row 1: large live chart + compact gauge
    b1_left, b1_right = st.columns([2, 1])
    with b1_left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        fig_live = px.line(hist_df.tail(140), x="timestamp", y="ram_percent", markers=True)
        if st.session_state.theme_mode == "Light":
            fig_live.update_traces(line=dict(color="#2563EB", width=2.8), fill="tozeroy", fillcolor="rgba(37,99,235,0.14)")
        else:
            fig_live.update_traces(line=dict(color="#00F5FF", width=2.8), fill="tozeroy", fillcolor="rgba(0,245,255,0.16)")
        st.plotly_chart(style_plot(fig_live, "Real-time RAM Usage", st.session_state.theme_mode), width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)
    with b1_right:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
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
                        {"range": [0, 40], "color": "rgba(239,68,68,0.45)"},
                        {"range": [40, 70], "color": "rgba(245,158,11,0.35)"},
                        {"range": [70, 100], "color": "rgba(34,197,94,0.35)"},
                    ],
                },
            )
        )
        gauge.update_layout(
            height=350,
            margin=dict(l=8, r=8, t=40, b=8),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#0f172a" if st.session_state.theme_mode == "Light" else "#e2e8f0"),
        )
        st.plotly_chart(gauge, width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)

    # Bento row 2: trends + prediction analysis
    b2_left, b2_right = st.columns([1, 1])
    with b2_left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        trend_df = hist_df.copy()
        trend_df["ram_smooth"] = trend_df["ram_percent"].rolling(12, min_periods=1).mean()
        trend_palette = ["#2563EB", "#0EA5E9", "#CA8A04", "#7C3AED"] if st.session_state.theme_mode == "Light" else ["#00F5FF", "#6366F1", "#F59E0B", "#22C55E"]
        fig_trend = px.line(
            trend_df,
            x="timestamp",
            y=["ram_percent", "ram_smooth", "cpu_percent", "swap_percent"],
            color_discrete_sequence=trend_palette,
        )
        fig_trend.update_traces(line=dict(width=2.2))
        st.plotly_chart(style_plot(fig_trend, "Historical Multi-metric Trends", st.session_state.theme_mode), width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)
    with b2_right:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        if not pred_show.empty:
            pred_show["actual_ram_percent"] = pred_show["actual_ram_percent"].astype(float)
            pred_show["predicted_ram_percent"] = pred_show["predicted_ram_percent"].astype(float)
            pred_show["err"] = (pred_show["predicted_ram_percent"] - pred_show["actual_ram_percent"]).abs()
            ci = float(pred_show["err"].rolling(10, min_periods=1).mean().iloc[-1] or 1.5)
            pred_show["upper"] = pred_show["predicted_ram_percent"] + ci
            pred_show["lower"] = pred_show["predicted_ram_percent"] - ci
            fig_pred = go.Figure()
            fig_pred.add_trace(
                go.Scatter(
                    x=pred_show["timestamp"],
                    y=pred_show["actual_ram_percent"],
                    name="Actual",
                    line=dict(color="#0F766E" if st.session_state.theme_mode == "Light" else "#22C55E", width=2.2),
                )
            )
            fig_pred.add_trace(
                go.Scatter(
                    x=pred_show["timestamp"],
                    y=pred_show["predicted_ram_percent"],
                    name="Predicted",
                    line=dict(color="#1D4ED8" if st.session_state.theme_mode == "Light" else "#6366F1", width=2.4),
                )
            )
            fig_pred.add_trace(go.Scatter(x=pred_show["timestamp"], y=pred_show["upper"], line=dict(width=0), showlegend=False, hoverinfo="skip"))
            fig_pred.add_trace(
                go.Scatter(
                    x=pred_show["timestamp"],
                    y=pred_show["lower"],
                    line=dict(width=0),
                    fill="tonexty",
                    fillcolor="rgba(29,78,216,0.15)" if st.session_state.theme_mode == "Light" else "rgba(99,102,241,0.15)",
                    name="Confidence band",
                    hoverinfo="skip",
                )
            )
            st.plotly_chart(
                style_plot(fig_pred, "Prediction vs Actual + Confidence Band", st.session_state.theme_mode),
                width="stretch",
            )
        else:
            st.info("Prediction graph appears once predictions are generated.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-title">Insights</div>', unsafe_allow_html=True)
    left_insights, right_insights = st.columns([2, 1])
    with left_insights:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Top Processes")
        proc_source = proc_df if not proc_df.empty else db.fetch_recent_process_metrics(limit=CONFIG.process_limit)
        search = st.text_input("Search process", value="")
        if proc_source.empty:
            st.info("No process data available.")
        else:
            table = (
                proc_source[["name", "pid", "memory_percent", "cpu_percent", "rss_mb"]]
                .sort_values("rss_mb", ascending=False)
                .rename(columns={"name": "Name", "pid": "PID", "memory_percent": "RAM %", "cpu_percent": "CPU %", "rss_mb": "RSS MB"})
            )
            if search.strip():
                table = table[table["Name"].str.contains(search.strip(), case=False, na=False)]
            st.dataframe(table, width="stretch", height=300)
        st.markdown("</div>", unsafe_allow_html=True)

    with right_insights:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Risk Summary")
        st.markdown(f"**Risk Level:** `{risk_report.level.value}`")
        st.markdown(f"**Stability:** `{stability:.2f}/100`")
        st.markdown(f"**ML Model:** `{active_model}` ({selection_mode})")
        badge_class = (
            "confidence-high"
            if confidence_label == "HIGH"
            else ("confidence-medium" if confidence_label == "MEDIUM" else "confidence-low")
        )
        st.markdown(
            f'<div class="confidence-badge {badge_class}">Model Confidence: {confidence_score:.1f}% ({confidence_label})</div>',
            unsafe_allow_html=True,
        )
        if train_metrics:
            st.caption(
                f"Latest training quality - MAE: {train_metrics.get('mae', 'n/a')}, "
                f"RMSE: {train_metrics.get('rmse', 'n/a')}, R²: {train_metrics.get('r2', 'n/a')}"
            )
        if model_meta and model_meta.get("selection_mode") == "AUTO":
            rf_m = (model_meta.get("model_metrics") or {}).get("rf")
            lstm_m = (model_meta.get("model_metrics") or {}).get("lstm")
            if rf_m:
                st.caption(f"RF validation: R² {rf_m.get('r2', 'n/a')} | RMSE {rf_m.get('rmse', 'n/a')}")
            if lstm_m:
                st.caption(f"LSTM validation: R² {lstm_m.get('r2', 'n/a')} | RMSE {lstm_m.get('rmse', 'n/a')}")
        with st.expander("Why this model was chosen", expanded=False):
            model_metrics = (model_meta or {}).get("model_metrics", {})
            rows: list[dict] = []
            rf_metrics = model_metrics.get("rf")
            lstm_metrics = model_metrics.get("lstm")
            if rf_metrics:
                rows.append(
                    {
                        "Model": "RF",
                        "R²": rf_metrics.get("r2", "n/a"),
                        "RMSE": rf_metrics.get("rmse", "n/a"),
                        "MAE": rf_metrics.get("mae", "n/a"),
                        "Train Samples": rf_metrics.get("train_samples", "n/a"),
                        "Test Samples": rf_metrics.get("test_samples", "n/a"),
                    }
                )
            if lstm_metrics:
                rows.append(
                    {
                        "Model": "LSTM",
                        "R²": lstm_metrics.get("r2", "n/a"),
                        "RMSE": lstm_metrics.get("rmse", "n/a"),
                        "MAE": lstm_metrics.get("mae", "n/a"),
                        "Train Samples": lstm_metrics.get("train_samples", "n/a"),
                        "Test Samples": lstm_metrics.get("test_samples", "n/a"),
                    }
                )
            if rows:
                compare_df = pd.DataFrame(rows).sort_values(["R²", "RMSE"], ascending=[False, True])
                st.dataframe(compare_df, width="stretch", hide_index=True)
                st.caption(f"Selected model this refresh: {active_model}")
                st.caption("Selection priority: highest R², then lowest RMSE.")
            else:
                st.info("Model comparison data is not available yet. Generate data and refresh to train models.")
        st.markdown("**Current Guidance:**")
        if risk_report.level in (RiskLevel.CRITICAL, RiskLevel.EMERGENCY):
            st.write("- Close non-essential high RAM processes.")
            st.write("- Click Refresh Data after each change.")
        elif risk_report.level == RiskLevel.WARNING:
            st.write("- Reduce optional app load.")
            st.write("- Observe trend line before next action.")
        else:
            st.write("- System is stable. Continue monitoring.")
        st.markdown("</div>", unsafe_allow_html=True)

    if predicted_ram is not None:
        st.markdown('<div class="section-title">Analysis</div>', unsafe_allow_html=True)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="analysis-block"><strong>Detailed Risk Analysis</strong><br/>Memory pressure is computed from current RAM, predicted RAM, and thresholds.</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="analysis-block"><strong>Prediction Explanation</strong><br/>Prediction is generated by <b>{active_model}</b> using lagged RAM, CPU, swap, availability, and time-context features.</div>',
            unsafe_allow_html=True,
        )
        recs = greedy_optimization_strategy(proc_source, risk_report.level) if not proc_source.empty else []
        if recs:
            suggestions = "<br/>".join([f"- {r.process_name} (PID {r.pid}): {r.recommendation}" for r in recs])
        else:
            suggestions = "- No immediate optimization action required."
        st.markdown(f'<div class="analysis-block"><strong>Optimization Suggestions</strong><br/>{suggestions}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="analysis-block"><strong>System Health Summary</strong><br/>Stability score is <b>{stability:.2f}/100</b> and risk is <b>{risk_report.level.value}</b>.</div>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
    elif prediction_error:
        st.info(prediction_error)

    log_analysis = analyze_logs(alert_df)
    with st.expander("Logs and Alerts", expanded=False):
        if log_analysis["total"] == 0:
            st.info("No alerts logged yet.")
        else:
            st.dataframe(log_analysis["display_df"], width="stretch", height=250)

    st.markdown('<div class="section-title">Log Analysis Results</div>', unsafe_allow_html=True)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    l1, l2, l3, l4 = st.columns(4)
    with l1:
        st.metric("Total Logs", str(log_analysis["total"]))
    with l2:
        st.metric("Recent Severe", str(log_analysis["recent_severe"]))
    with l3:
        stability_text = f"{log_analysis['avg_stability']:.2f}/100" if log_analysis["avg_stability"] is not None else "N/A"
        st.metric("Avg Stability", stability_text)
    with l4:
        st.metric("Dominant Risk", str(log_analysis["dominant_risk"]))
    st.markdown(f"**Analysis Summary:** {log_analysis['summary']}")
    if log_analysis["latest_message"]:
        st.markdown(f"**Latest Log Insight:** `{log_analysis['latest_message']}`")
    st.markdown(f"**Recommended Action:** {log_analysis['suggestion']}")
    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("Download Data", expanded=False):
        st.download_button("Download System Metrics CSV", hist_df.to_csv(index=False).encode("utf-8"), "system_metrics.csv", "text/csv")
        st.download_button("Download Process Metrics CSV", proc_source.to_csv(index=False).encode("utf-8") if not proc_source.empty else b"", "process_metrics.csv", "text/csv")
        st.download_button("Download Predictions CSV", pred_df.to_csv(index=False).encode("utf-8"), "predictions.csv", "text/csv")

    st.caption(f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")


if __name__ == "__main__":
    main()
