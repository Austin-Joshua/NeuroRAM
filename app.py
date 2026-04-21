"""Streamlit dashboard for NeuroRAM."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from neuroram.backend.daa.optimizer import complexity_analysis, greedy_optimization_strategy
from neuroram.backend.daa.risk_analyzer import RiskLevel, classify_risk, detect_memory_leak
from neuroram.backend.daa.stability_index import compute_stability_index
from neuroram.backend.dbms.database import DatabaseManager
from neuroram.backend.mlt.ml_engine import MLEngine, TENSORFLOW_AVAILABLE
from neuroram.backend.mlt.predictor import predict_next_ram
from neuroram.backend.os.collector import collect_process_metrics, collect_system_metrics
from neuroram.config.config import CONFIG


if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = "expanded"

st.set_page_config(
    page_title="NeuroRAM",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state=st.session_state.sidebar_state,
)


def _risk_color(level: RiskLevel) -> str:
    return {
        RiskLevel.NORMAL: "#2ecc71",
        RiskLevel.WARNING: "#f1c40f",
        RiskLevel.CRITICAL: "#e67e22",
        RiskLevel.EMERGENCY: "#e74c3c",
    }[level]


def _risk_palette(level: RiskLevel) -> dict[str, str]:
    palettes = {
        RiskLevel.NORMAL: {
            "primary": "#22c55e",
            "secondary": "#10b981",
            "fill": "rgba(34,197,94,0.2)",
        },
        RiskLevel.WARNING: {
            "primary": "#f59e0b",
            "secondary": "#fbbf24",
            "fill": "rgba(245,158,11,0.22)",
        },
        RiskLevel.CRITICAL: {
            "primary": "#f97316",
            "secondary": "#fb923c",
            "fill": "rgba(249,115,22,0.22)",
        },
        RiskLevel.EMERGENCY: {
            "primary": "#ef4444",
            "secondary": "#f87171",
            "fill": "rgba(239,68,68,0.24)",
        },
    }
    return palettes[level]


def _theme_tokens(theme_mode: str) -> dict[str, str]:
    if theme_mode == "Light":
        return {
            "app_bg": "linear-gradient(145deg, #f5f7fb 0%, #e8efff 55%, #fff7e6 100%)",
            "text": "#0b1f3a",
            "muted_text": "#334e7a",
            "sidebar_bg": "rgba(255, 255, 255, 0.9)",
            "sidebar_border": "rgba(11, 31, 58, 0.14)",
            "input_bg": "rgba(11, 31, 58, 0.04)",
            "input_border": "rgba(11, 31, 58, 0.18)",
            "card_bg": "rgba(255, 255, 255, 0.82)",
            "card_border": "rgba(11, 31, 58, 0.14)",
            "card_shadow": "0 10px 26px rgba(15, 23, 42, 0.12)",
            "badge_bg": "rgba(255, 255, 255, 0.92)",
            "metric_border_hover": "rgba(234, 179, 8, 0.65)",
            "scroll_track": "rgba(11, 31, 58, 0.08)",
            "grid": "rgba(51, 78, 122, 0.2)",
            "plot_bg": "rgba(255,255,255,0.65)",
            "card_tint_1": "rgba(14, 165, 233, 0.12)",
            "card_tint_2": "rgba(234, 179, 8, 0.1)",
        }
    return {
        "app_bg": "radial-gradient(circle at 20% 20%, #121f3c 0%, #0f172a 45%, #101b34 100%)",
        "text": "#e8eef8",
        "muted_text": "#c8d5ea",
        "sidebar_bg": "rgba(11, 23, 43, 0.78)",
        "sidebar_border": "rgba(255, 255, 255, 0.08)",
        "input_bg": "rgba(255, 255, 255, 0.06)",
        "input_border": "rgba(255, 255, 255, 0.1)",
        "card_bg": "rgba(255, 255, 255, 0.06)",
        "card_border": "rgba(255, 255, 255, 0.14)",
        "card_shadow": "0 10px 30px rgba(2, 6, 23, 0.45)",
        "badge_bg": "rgba(255, 255, 255, 0.08)",
        "metric_border_hover": "rgba(234, 179, 8, 0.55)",
        "scroll_track": "rgba(148, 163, 184, 0.08)",
        "grid": "rgba(148,163,184,0.15)",
        "plot_bg": "rgba(255,255,255,0.02)",
        "card_tint_1": "rgba(59, 130, 246, 0.14)",
        "card_tint_2": "rgba(245, 158, 11, 0.12)",
    }


def apply_theme(theme_mode: str) -> None:
    t = _theme_tokens(theme_mode)
    css = """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        .stApp {
            font-family: 'Inter', sans-serif;
            background: __APP_BG__;
            color: __TEXT__;
        }
        section[data-testid="stMain"] p,
        section[data-testid="stMain"] label,
        section[data-testid="stMain"] li,
        section[data-testid="stMain"] h1,
        section[data-testid="stMain"] h2,
        section[data-testid="stMain"] h3,
        section[data-testid="stMain"] h4,
        section[data-testid="stMain"] h5 {
            color: __TEXT__ !important;
        }
        [data-testid="stSidebar"] {
            background: __SIDEBAR_BG__;
            backdrop-filter: blur(12px);
            border-right: 1px solid __SIDEBAR_BORDER__;
        }
        [data-testid="collapsedControl"] button,
        [data-testid="stSidebarCollapseButton"] button {
            background: __CARD_BG__ !important;
            border: 1px solid __CARD_BORDER__ !important;
            border-radius: 10px !important;
            min-height: 2.1rem !important;
            min-width: 2.1rem !important;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        [data-testid="collapsedControl"] button,
        [data-testid="stSidebarCollapseButton"] button {
            color: transparent !important;
            font-size: 0 !important;
            text-indent: -9999px !important;
            overflow: hidden !important;
        }
        [data-testid="collapsedControl"] button:hover,
        [data-testid="stSidebarCollapseButton"] button:hover {
            transform: scale(1.04);
            border-color: __METRIC_HOVER__ !important;
        }
        [data-testid="collapsedControl"] button svg,
        [data-testid="stSidebarCollapseButton"] button svg {
            display: none !important;
        }
        [data-testid="collapsedControl"] button::before,
        [data-testid="stSidebarCollapseButton"] button::before {
            content: "☰";
            color: __TEXT__;
            font-size: 1.05rem;
            font-weight: 700;
            line-height: 1;
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] label {
            color: __TEXT__ !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] [data-baseweb="input"] > div {
            background: __INPUT_BG__ !important;
            border: 1px solid __INPUT_BORDER__ !important;
            border-radius: 12px !important;
        }
        .panel-card {
            padding: 1.15rem;
            border-radius: 18px;
            background: linear-gradient(120deg, __CARD_BG__ 0%, __CARD_TINT_1__ 55%, __CARD_TINT_2__ 100%);
            border: 1px solid __CARD_BORDER__;
            margin-bottom: 1rem;
            box-shadow: __CARD_SHADOW__;
            backdrop-filter: blur(14px);
            transition: transform 0.22s ease, box-shadow 0.22s ease;
        }
        .panel-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 14px 34px rgba(2, 6, 23, 0.5);
        }
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 0.4rem 0.8rem;
            border-radius: 999px;
            font-weight: 600;
            border: 1px solid __CARD_BORDER__;
            background: __BADGE_BG__;
        }
        .pulse-dot {
            height: 10px;
            width: 10px;
            border-radius: 50%;
            display: inline-block;
            animation: pulse 1.7s infinite;
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.35); }
            70% { box-shadow: 0 0 0 12px rgba(255, 255, 255, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); }
        }
        .hero-title {
            text-align: center;
            font-size: 2.3rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
            letter-spacing: 0.2px;
            color: __TEXT__;
        }
        .hero-subtitle {
            text-align: center;
            opacity: 0.85;
            margin-bottom: 0.9rem;
            color: __MUTED_TEXT__;
        }
        div[data-testid="stMetric"] {
            border-radius: 16px;
            padding: 0.6rem 0.8rem;
            background: __CARD_BG__;
            border: 1px solid __CARD_BORDER__;
            backdrop-filter: blur(12px);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        div[data-testid="stMetric"]:hover {
            transform: scale(1.02);
            border-color: __METRIC_HOVER__;
        }
        .alert-card {
            border-radius: 14px;
            padding: 0.75rem 0.9rem;
            margin-bottom: 0.5rem;
            border: 1px solid __CARD_BORDER__;
            animation: fadeIn 0.35s ease-out;
        }
        .sidebar-group-title {
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin: 0.15rem 0 0.32rem 0;
            opacity: 0.85;
        }
        @keyframes fadeIn {
            from { opacity: 0.35; transform: translateY(3px); }
            to { opacity: 1; transform: translateY(0); }
        }
        ::-webkit-scrollbar { width: 10px; height: 10px; }
        ::-webkit-scrollbar-track { background: __SCROLL_TRACK__; border-radius: 10px; }
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, #00ADB5 0%, #0ea5e9 100%);
            border-radius: 10px;
        }
        </style>
    """
    css = (
        css.replace("__APP_BG__", t["app_bg"])
        .replace("__TEXT__", t["text"])
        .replace("__MUTED_TEXT__", t["muted_text"])
        .replace("__SIDEBAR_BG__", t["sidebar_bg"])
        .replace("__SIDEBAR_BORDER__", t["sidebar_border"])
        .replace("__INPUT_BG__", t["input_bg"])
        .replace("__INPUT_BORDER__", t["input_border"])
        .replace("__CARD_BG__", t["card_bg"])
        .replace("__CARD_BORDER__", t["card_border"])
        .replace("__CARD_SHADOW__", t["card_shadow"])
        .replace("__BADGE_BG__", t["badge_bg"])
        .replace("__METRIC_HOVER__", t["metric_border_hover"])
        .replace("__SCROLL_TRACK__", t["scroll_track"])
        .replace("__CARD_TINT_1__", t["card_tint_1"])
        .replace("__CARD_TINT_2__", t["card_tint_2"])
    )
    st.markdown(
        css,
        unsafe_allow_html=True,
    )


def render_header(risk_level: RiskLevel) -> None:
    color = _risk_color(risk_level)
    st.markdown('<div class="hero-title">NeuroRAM</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-subtitle">Intelligent Predictive Memory Optimization System</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="panel-card">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
                <div>
                    <div style="font-size:1.05rem;font-weight:600;">Real-time memory intelligence dashboard</div>
                    <div style="opacity:0.85;">OS telemetry + DBMS history + ML forecasting + DAA optimization</div>
                </div>
                <div class="status-badge">
                    <span class="pulse-dot" style="background:{color};"></span>
                    Live Status: {risk_level.value}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_startup_db_status(db: DatabaseManager) -> None:
    if st.session_state.get("startup_db_status_shown", False):
        return

    index_status = db.get_index_status()
    all_present = all(index_status.values())

    with st.expander("Startup DB Integrity Check", expanded=True):
        if all_present:
            st.success("All required timestamp indexes are present in the active database.")
        else:
            st.warning("Some timestamp indexes are missing in the active database.")
        st.caption(f"Active DB file: {db.db_path}")
        for idx_name, present in index_status.items():
            mark = "OK" if present else "MISSING"
            st.write(f"- `{idx_name}`: {mark}")

    st.session_state.startup_db_status_shown = True


def style_plotly(fig: go.Figure, title: str, risk_level: RiskLevel, theme_mode: str) -> go.Figure:
    palette = _risk_palette(risk_level)
    t = _theme_tokens(theme_mode)
    fig.update_layout(
        title=title,
        height=320,
        margin=dict(l=10, r=10, t=45, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=t["plot_bg"],
        font=dict(color=t["text"]),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=t["muted_text"])),
        xaxis=dict(showgrid=True, gridcolor=t["grid"], zeroline=False),
        yaxis=dict(showgrid=True, gridcolor=t["grid"], zeroline=False),
    )
    for i, trace in enumerate(fig.data):
        color = palette["primary"] if i == 0 else palette["secondary"]
        trace.update(line=dict(color=color, width=2.8))
        if i == 0 and getattr(trace, "fill", None):
            trace.update(fillcolor=palette["fill"])
    return fig


def build_stability_gauge(stability_index: float, risk_level: RiskLevel, theme_mode: str) -> go.Figure:
    palette = _risk_palette(risk_level)
    t = _theme_tokens(theme_mode)
    return go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=stability_index,
            number={"suffix": "/100", "font": {"color": t["text"], "size": 28}},
            title={"text": "Stability Gauge", "font": {"color": t["text"], "size": 16}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#94a3b8"},
                "bar": {"color": palette["primary"]},
                "bgcolor": "rgba(255,255,255,0.04)",
                "borderwidth": 1,
                "bordercolor": "rgba(255,255,255,0.18)",
                "steps": [
                    {"range": [0, 40], "color": "rgba(239,68,68,0.5)"},
                    {"range": [40, 70], "color": "rgba(245,158,11,0.45)"},
                    {"range": [70, 100], "color": "rgba(34,197,94,0.45)"},
                ],
            },
        )
    ).update_layout(
        height=250,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=t["text"]),
    )


def style_process_table(process_table: pd.DataFrame, theme_mode: str) -> pd.io.formats.style.Styler:
    text_color = "#0f172a" if theme_mode == "Light" else "#e2e8f0"

    def row_style(row):
        ram = float(row["RAM %"])
        if ram >= 8:
            color = "rgba(239,68,68,0.22)"
        elif ram >= 4:
            color = "rgba(245,158,11,0.2)"
        else:
            color = "rgba(34,197,94,0.14)"
        return [f"background-color: {color}; color: {text_color};" for _ in row]

    return (
        process_table.style.apply(row_style, axis=1)
        .format({"RAM %": "{:.2f}", "CPU %": "{:.2f}", "RSS MB": "{:.2f}"})
        .set_properties(**{"border-color": "rgba(255,255,255,0.1)"})
    )


def maybe_collect_data(db: DatabaseManager, collect_now: bool) -> tuple[dict | None, pd.DataFrame]:
    if collect_now:
        system_row = collect_system_metrics()
        process_rows = collect_process_metrics()
        db.insert_system_metric(system_row)
        db.insert_process_metrics(process_rows)
        proc_df = pd.DataFrame(process_rows)
        return system_row, proc_df

    hist_df = db.fetch_system_metrics(limit=1)
    if hist_df.empty:
        return None, pd.DataFrame()
    latest = hist_df.iloc[-1].to_dict()
    latest["timestamp"] = str(hist_df.iloc[-1]["timestamp"])
    process_hist = db.fetch_recent_process_metrics(limit=CONFIG.process_limit)
    return latest, process_hist


def train_or_predict(
    hist_df: pd.DataFrame,
    ml_engine: MLEngine,
    model_choice: str,
) -> tuple[float | None, str | None]:
    predicted_ram = None
    prediction_error = None

    if len(hist_df) >= 40:
        try:
            should_retrain = not Path(CONFIG.rf_model_path).exists() if model_choice == "rf" else not Path(
                CONFIG.lstm_model_path
            ).exists()
            train_gate_key = f"last_train_size_{model_choice}"
            last_train_size = st.session_state.get(train_gate_key, -1)
            if len(hist_df) % 25 == 0 and len(hist_df) != last_train_size:
                should_retrain = True

            if should_retrain:
                if model_choice == "rf":
                    ml_engine.train_random_forest(hist_df)
                elif TENSORFLOW_AVAILABLE:
                    ml_engine.train_lstm(hist_df, epochs=6)
                st.session_state[train_gate_key] = len(hist_df)

            predicted_ram = predict_next_ram(hist_df, model_choice=model_choice)
        except Exception as exc:
            prediction_error = str(exc)

    return predicted_ram, prediction_error


def main() -> None:
    db = DatabaseManager()
    ml_engine = MLEngine()

    if "monitoring_enabled" not in st.session_state:
        st.session_state.monitoring_enabled = True
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "Dark"
    if "model_choice" not in st.session_state:
        st.session_state.model_choice = "rf"
    if "first_data_load" not in st.session_state:
        st.session_state.first_data_load = True

    st.sidebar.title("Control Center")
    st.sidebar.caption("Live controls and guidance")
    dark_mode_enabled = st.sidebar.toggle("Dark mode", value=st.session_state.theme_mode == "Dark")
    st.session_state.theme_mode = "Dark" if dark_mode_enabled else "Light"
    apply_theme(st.session_state.theme_mode)

    st.sidebar.markdown('<div class="sidebar-group-title">Monitoring</div>', unsafe_allow_html=True)
    st.session_state.monitoring_enabled = st.sidebar.toggle(
        "Start/Stop Monitoring", value=st.session_state.monitoring_enabled
    )
    refresh_now = st.sidebar.button("Refresh Data Now", width="stretch")
    if st.sidebar.button("Show DB index evidence again", width="stretch"):
        st.session_state.startup_db_status_shown = False
    st.sidebar.caption("Data refreshes only when you click refresh.")
    st.sidebar.divider()

    st.sidebar.markdown('<div class="sidebar-group-title">Risk Thresholds</div>', unsafe_allow_html=True)
    warning_threshold = st.sidebar.slider("Warning Threshold (%)", 50, 90, int(CONFIG.warning_threshold))
    critical_threshold = st.sidebar.slider("Critical Threshold (%)", 60, 95, int(CONFIG.critical_threshold))
    emergency_threshold = st.sidebar.slider("Emergency Threshold (%)", 70, 99, int(CONFIG.emergency_threshold))
    st.sidebar.divider()
    collect_now = st.session_state.monitoring_enabled and (refresh_now or st.session_state.first_data_load)
    st.session_state.first_data_load = False
    system_row, proc_df = maybe_collect_data(db, collect_now)
    hist_df = db.fetch_system_metrics(limit=600)
    if system_row is None:
        st.warning("No telemetry found yet. Enable monitoring to start collecting data.")
        return

    model_choice = st.session_state.model_choice

    leak_detected = detect_memory_leak(hist_df)
    predicted_ram, prediction_error = train_or_predict(hist_df, ml_engine, model_choice)

    current_ram = float(system_row["ram_percent"])
    predicted_for_risk = float(predicted_ram) if predicted_ram is not None else current_ram
    effective_ram = max(current_ram, predicted_for_risk)
    risk_report = classify_risk(effective_ram, leak_detected)
    if predicted_ram is not None and predicted_for_risk > current_ram:
        risk_report.reasons.append(
            f"Proactive escalation applied: predicted RAM ({predicted_for_risk:.2f}%) exceeds current RAM ({current_ram:.2f}%)."
        )

    # Threshold overrides from UI for adaptive session sensitivity.
    original_level = risk_report.level
    if effective_ram >= emergency_threshold:
        risk_report.level = RiskLevel.EMERGENCY
    elif effective_ram >= critical_threshold:
        risk_report.level = RiskLevel.CRITICAL
    elif effective_ram >= warning_threshold and risk_report.level == RiskLevel.NORMAL:
        risk_report.level = RiskLevel.WARNING
    if risk_report.level != original_level:
        risk_report.reasons.append(
            f"Risk level adjusted by sidebar thresholds (W:{warning_threshold} C:{critical_threshold} E:{emergency_threshold})."
        )

    stability_index = compute_stability_index(
        ram_percent=float(system_row["ram_percent"]),
        cpu_percent=float(system_row["cpu_percent"]),
        swap_percent=float(system_row["swap_percent"]),
        risk_level=risk_report.level,
    )

    db.insert_alert(
        timestamp=str(system_row["timestamp"]),
        risk_level=risk_report.level.value,
        message=" | ".join(risk_report.reasons),
        stability_index=stability_index,
    )
    if predicted_ram is not None:
        db.insert_prediction(str(system_row["timestamp"]), model_choice, predicted_ram, float(system_row["ram_percent"]))

    render_header(risk_report.level)
    render_startup_db_status(db)
    with st.expander("Advanced Controls", expanded=False):
        model_options = ["rf", "lstm"] if TENSORFLOW_AVAILABLE else ["rf"]
        default_index = model_options.index(st.session_state.model_choice) if st.session_state.model_choice in model_options else 0
        st.session_state.model_choice = st.selectbox(
            "Prediction Model",
            options=model_options,
            index=default_index,
            format_func=lambda x: "RandomForest" if x == "rf" else "LSTM",
        )
        st.caption("Adjust model here when needed.")
    model_choice = st.session_state.model_choice

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("RAM Usage", f"{float(system_row['ram_percent']):.2f}%", help="Current system RAM utilization percentage.")
    m2.metric(
        "Predicted RAM",
        f"{predicted_ram:.2f}%" if predicted_ram is not None else "N/A",
        help="Forecasted near-future RAM usage from selected ML model.",
    )
    m3.metric("CPU Usage", f"{float(system_row['cpu_percent']):.2f}%", help="Current CPU utilization percentage.")
    m4.metric("Stability Index", f"{stability_index:.2f}/100", help="Composite system health score.")

    st.progress(min(int(float(system_row["ram_percent"])), 100), text="Current RAM pressure")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.subheader("Real-time RAM Usage")
        rt_df = hist_df.tail(60)
        fig_rt = px.line(rt_df, x="timestamp", y="ram_percent", markers=True)
        fig_rt.update_traces(fill="tozeroy")
        fig_rt = style_plotly(fig_rt, "Recent RAM (%)", risk_report.level, st.session_state.theme_mode)
        st.plotly_chart(fig_rt, width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.subheader("Historical Trends")
        hist_chart_df = hist_df.copy()
        hist_chart_df["ram_rolling"] = hist_chart_df["ram_percent"].rolling(15, min_periods=1).mean()
        fig_hist = px.line(
            hist_chart_df,
            x="timestamp",
            y=["ram_percent", "ram_rolling", "cpu_percent"],
        )
        fig_hist = style_plotly(fig_hist, "RAM, Rolling RAM, and CPU (%)", risk_report.level, st.session_state.theme_mode)
        st.plotly_chart(fig_hist, width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    pred_df = db.fetch_predictions(limit=250)
    p1, p2 = st.columns([2, 1])
    with p1:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.subheader("Prediction vs Actual Comparison")
        if pred_df.empty:
            st.info("Prediction history will appear after sufficient training data.")
        else:
            fig_pred = px.line(pred_df, x="timestamp", y=["predicted_ram_percent", "actual_ram_percent"])
            fig_pred = style_plotly(fig_pred, "Prediction Accuracy Trend", risk_report.level, st.session_state.theme_mode)
            st.plotly_chart(fig_pred, width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)
    with p2:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.plotly_chart(
            build_stability_gauge(stability_index, risk_report.level, st.session_state.theme_mode),
            width="stretch",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.subheader("Top Memory-consuming Processes")
    if proc_df.empty:
        st.info("No process data currently available.")
    else:
        process_table = (
            proc_df[["name", "pid", "memory_percent", "cpu_percent", "rss_mb"]]
            .sort_values("rss_mb", ascending=False)
            .rename(columns={"name": "Name", "pid": "PID", "memory_percent": "RAM %", "cpu_percent": "CPU %", "rss_mb": "RSS MB"})
            .reset_index(drop=True)
        )
        styled = style_process_table(process_table[["Name", "PID", "RAM %", "CPU %", "RSS MB"]], st.session_state.theme_mode)
        st.dataframe(styled, width="stretch", height=280)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.subheader("Alerts, Risk, and Optimization")
    if risk_report.level == RiskLevel.NORMAL:
        st.markdown('<div class="alert-card" style="background:rgba(34,197,94,0.15);">System state is healthy.</div>', unsafe_allow_html=True)
    elif risk_report.level == RiskLevel.WARNING:
        st.markdown('<div class="alert-card" style="background:rgba(245,158,11,0.15);">System approaching pressure limits. Review top processes.</div>', unsafe_allow_html=True)
    elif risk_report.level == RiskLevel.CRITICAL:
        st.markdown('<div class="alert-card" style="background:rgba(239,68,68,0.18);">Critical pressure detected. Immediate optimization advised.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-card" style="background:rgba(239,68,68,0.24);">Emergency pressure detected. Aggressive mitigation needed.</div>', unsafe_allow_html=True)

    for reason in risk_report.reasons:
        st.write(f"- {reason}")
    if leak_detected:
        st.warning("Leak heuristic triggered: sustained monotonic RAM growth detected.")

    recommendations = greedy_optimization_strategy(proc_df, risk_report.level)
    if recommendations:
        for rec in recommendations:
            st.write(f"- `{rec.process_name}` (PID {rec.pid}) score {rec.priority_score}: {rec.recommendation}")
    else:
        st.write("- No optimization action required.")
    st.markdown("</div>", unsafe_allow_html=True)

    if prediction_error:
        st.warning(f"Prediction unavailable: {prediction_error}")

    recent_alerts = db.fetch_alerts(limit=20)
    with st.expander("Recent Logs and Alerts", expanded=False):
        st.dataframe(recent_alerts, width="stretch")

    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.subheader("What needs attention and how to fix it")
    if risk_report.level in (RiskLevel.CRITICAL, RiskLevel.EMERGENCY):
        st.write("- Lower memory pressure by closing high-RAM processes from the top process table.")
        st.write("- Increase `Warning/Critical/Emergency` thresholds only if your machine normally runs at high RAM.")
        st.write("- Keep monitoring ON and click `Refresh Data Now` to verify improvement after each change.")
    elif risk_report.level == RiskLevel.WARNING:
        st.write("- You are near limits. Close optional apps and browser tabs.")
        st.write("- Observe prediction trend. If predicted RAM stays high, tune thresholds conservatively.")
        st.write("- Use optimization suggestions for first actions.")
    else:
        st.write("- System is stable. Keep default thresholds and periodic checks.")
        st.write("- If behavior changes, review logs and recommendation panel.")
    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("DAA Complexity Analysis"):
        complexity = complexity_analysis()
        st.write(f"- Process ranking: {complexity['ranking']}")
        st.write(f"- Candidate selection: {complexity['selection']}")
        st.write(f"- Overall: {complexity['overall']}")

    with st.expander("Download Data"):
        st.download_button(
            label="Download System Metrics CSV",
            data=hist_df.to_csv(index=False).encode("utf-8"),
            file_name="system_metrics.csv",
            mime="text/csv",
        )
        st.download_button(
            label="Download Process Metrics CSV",
            data=proc_df.to_csv(index=False).encode("utf-8"),
            file_name="process_metrics.csv",
            mime="text/csv",
        )
        st.download_button(
            label="Download Predictions CSV",
            data=pred_df.to_csv(index=False).encode("utf-8"),
            file_name="predictions.csv",
            mime="text/csv",
        )

    last_refresh = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    mode_text = "Running" if st.session_state.monitoring_enabled else "Paused"
    st.caption(f"Monitoring: {mode_text} | Last data refresh: {last_refresh}")


if __name__ == "__main__":
    main()
