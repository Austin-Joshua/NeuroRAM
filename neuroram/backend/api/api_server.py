"""FastAPI service exposing structured NeuroRAM dashboard data for React frontend."""

from __future__ import annotations

import threading
import time
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from neuroram.backend.daa.optimizer import greedy_optimization_strategy
from neuroram.backend.daa.risk_analyzer import RiskLevel, classify_risk, detect_memory_leak, map_health_category
from neuroram.backend.daa.stability_index import compute_stability_index
from neuroram.backend.dbms.database import DatabaseManager
from neuroram.backend.mlt.ml_engine import MLEngine
from neuroram.backend.mlt.predictor import predict_next_ram
from neuroram.backend.os.system_monitor import collect_and_store
from neuroram.config.config import CONFIG

app = FastAPI(title="NeuroRAM API", version="2.0.0")


def _cors_origins() -> list[str]:
    raw = CONFIG.cors_origins_raw.strip()
    if not raw:
        return ["*"]
    if raw == "*":
        return ["*"]
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    return origins or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


PIPELINE_STATE: dict[str, Any] = {
    "running": False,
    "cycles": 0,
    "last_cycle_utc": None,
    "last_error": None,
    "last_prediction": None,
    "last_success_utc": None,
    "last_cycle_duration_ms": None,
}
FILE_STATS_CACHE: dict[str, tuple[float, dict[str, int | None]]] = {}
FILE_STATS_TTL_SEC = 60.0


PIPELINE_LOCK = threading.Lock()
PIPELINE_STOP = threading.Event()
PIPELINE_THREAD: threading.Thread | None = None


def _set_pipeline_state(**updates: Any) -> None:
    with PIPELINE_LOCK:
        PIPELINE_STATE.update(updates)


def _get_pipeline_state() -> dict[str, Any]:
    with PIPELINE_LOCK:
        return dict(PIPELINE_STATE)


def _empty_dashboard_payload(now: str, message: str) -> dict[str, Any]:
    return {
        "ready": False,
        "timestamp_utc": now,
        "message": message,
        "metrics": {
            "ram_now_percent": 0.0,
            "predicted_ram_percent": None,
            "stability_score": 0.0,
            "risk_level": "NORMAL",
            "health_category": "stable",
            "connected_devices": 0,
            "connected_storage": 0,
            "connected_dongles": 0,
            "connected_network_adapters": 0,
            "pipeline": _get_pipeline_state(),
        },
        "devices": {
            "connected": [],
            "storage": [],
            "dongles": [],
            "network_adapters": [],
            "timeline": [],
        },
        "trends": {
            "memory": [],
            "prediction": [],
            "stability": [],
            "device_activity": [],
        },
        "analysis": {
            "summary": "No telemetry data available yet.",
            "what_why_how": {
                "what": "No memory telemetry has been collected yet.",
                "why": "The pipeline has not produced enough samples for analysis.",
                "how_serious": "Low - waiting for initial data collection.",
                "impact": "Low - waiting for initial data collection.",
            },
            "algorithm": "ML (RandomForest) + DAA (risk classification, stability indexing, greedy optimization)",
            "reasons": [],
            "memory_patterns": {
                "spike_detected": False,
                "gradual_leak_detected": False,
                "abnormal_pattern": False,
                "predicted_vs_actual_mae": None,
                "predicted_vs_actual_bias": None,
                "severity": "low",
                "explanations": ["Insufficient data."],
                "spike_timestamps": [],
            },
            "inefficient_processes": [],
            "processes": [],
            "logs_preview": [],
            "narrative": "Telemetry is starting up. Once samples accumulate, NeuroRAM will explain memory pressure, device effects, and forecast quality in plain language.",
            "graph_insights": {
                "memory": {
                    "what": "Waiting for memory samples.",
                    "why": "The collector has not written enough history yet.",
                    "next": "Keep the backend running; charts will populate automatically.",
                },
                "prediction": {"what": "No forecast history yet.", "why": "The model needs a short warm-up window.", "next": "Predictions appear after initial training cycles."},
                "stability": {"what": "Stability trend not available.", "why": "No analysis snapshots yet.", "next": "Risk and stability curves will appear shortly."},
                "device_activity": {"what": "No device activity series yet.", "why": "Device logs are empty.", "next": "Connect a device to see timeline and activity charts."},
            },
        },
        "recommendations": {
            "category": "stable",
            "dos": ["Keep telemetry running for at least a few cycles."],
            "donts": ["Do not stop collection before baseline data is available."],
            "prioritized_actions": [],
        },
    }


def _pipeline_cycle(
    db: DatabaseManager,
    ml: MLEngine,
    previous_devices: dict[str, Any],
    cycle_count: int,
) -> dict[str, Any]:
    system_row, process_df, _, current_state = collect_and_store(
        db=db,
        process_limit=CONFIG.process_limit,
        previous_devices=previous_devices,
    )
    history = db.fetch_system_metrics(limit=1200)

    predicted_ram = None
    model_ready = Path(CONFIG.rf_model_path).exists() and Path(CONFIG.rf_scaler_path).exists()
    should_train = len(history) >= 40 and (not model_ready or cycle_count % 120 == 0)
    if should_train:
        ml.train_random_forest(history)
        model_ready = True
    if model_ready and len(history) >= 3:
        try:
            predicted_ram = float(predict_next_ram(history, "rf"))
            db.insert_prediction(
                timestamp=str(system_row["timestamp"]),
                model_name="rf",
                predicted_ram_percent=predicted_ram,
                actual_ram_percent=float(system_row["ram_percent"]),
            )
        except Exception:
            predicted_ram = None

    leak_detected = detect_memory_leak(history, window=8) if len(history) >= 8 else False
    risk_report = classify_risk(
        current_ram_percent=float(system_row["ram_percent"]),
        leak_detected=bool(leak_detected),
        predicted_ram_percent=predicted_ram,
    )
    stability = compute_stability_index(
        ram_percent=float(system_row["ram_percent"]),
        swap_percent=float(system_row["swap_percent"]),
        risk_level=risk_report.level,
    )
    confidence = 0.9 if predicted_ram is not None else 0.55
    db.insert_analysis_report(
        timestamp=str(system_row["timestamp"]),
        risk_level=risk_report.level.value,
        causes=" | ".join(risk_report.reasons),
        dos=" | ".join(risk_report.dos),
        donts=" | ".join(risk_report.donts),
        model_name="rf",
        confidence=confidence,
        stability_index=float(stability),
    )
    if not process_df.empty:
        _ = greedy_optimization_strategy(process_df, risk_report.level)
    return {
        "state": current_state,
        "predicted_ram": predicted_ram,
    }


def _pipeline_loop() -> None:
    db = DatabaseManager()
    ml = MLEngine()
    previous_devices: dict[str, Any] = {}
    cycle_count = 0
    while not PIPELINE_STOP.is_set():
        cycle_count += 1
        cycle_start = time.perf_counter()
        try:
            result = _pipeline_cycle(db, ml, previous_devices, cycle_count)
            previous_devices = result["state"]
            duration_ms = round((time.perf_counter() - cycle_start) * 1000.0, 2)
            _set_pipeline_state(
                running=True,
                cycles=cycle_count,
                last_cycle_utc=datetime.now(timezone.utc).isoformat(),
                last_error=None,
                last_prediction=result["predicted_ram"],
                last_success_utc=datetime.now(timezone.utc).isoformat(),
                last_cycle_duration_ms=duration_ms,
            )
        except Exception as exc:
            duration_ms = round((time.perf_counter() - cycle_start) * 1000.0, 2)
            _set_pipeline_state(
                running=True,
                cycles=cycle_count,
                last_cycle_utc=datetime.now(timezone.utc).isoformat(),
                last_error=str(exc),
                last_cycle_duration_ms=duration_ms,
            )
        PIPELINE_STOP.wait(CONFIG.collection_interval_sec)
    _set_pipeline_state(running=False)


def _start_pipeline_if_needed() -> None:
    global PIPELINE_THREAD
    if PIPELINE_THREAD and PIPELINE_THREAD.is_alive():
        return
    PIPELINE_STOP.clear()
    PIPELINE_THREAD = threading.Thread(target=_pipeline_loop, name="neuroram-pipeline", daemon=True)
    PIPELINE_THREAD.start()
    _set_pipeline_state(running=True)


@app.on_event("startup")
def startup_event() -> None:
    _start_pipeline_if_needed()


@app.on_event("shutdown")
def shutdown_event() -> None:
    PIPELINE_STOP.set()


def _parse_ts(series: pd.Series) -> pd.Series:
    try:
        return pd.to_datetime(series, utc=True, errors="coerce", format="mixed")
    except TypeError:
        return pd.to_datetime(series, utc=True, errors="coerce")


def _device_group(device_type: str) -> str:
    lowered = str(device_type).lower()
    if lowered == "usb_drive":
        return "storage"
    if lowered in {"input_dongle", "wifi_dongle"}:
        return "input_dongle" if lowered == "input_dongle" else "network_adapter"
    return "other"


def _latest_connected_devices(device_logs: pd.DataFrame) -> pd.DataFrame:
    if device_logs.empty or "device_id" not in device_logs.columns:
        return pd.DataFrame()
    df = device_logs.copy()
    df["timestamp"] = _parse_ts(df["timestamp"])
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp", ascending=False)
    latest = df.groupby("device_id", as_index=False).first()
    latest = latest[latest["is_connected"] == 1].copy()
    if latest.empty:
        return latest
    latest["device_group"] = latest["device_type"].map(_device_group)
    return latest


def _attach_connection_duration(connected: pd.DataFrame, device_logs: pd.DataFrame) -> pd.DataFrame:
    if connected.empty or device_logs.empty:
        return connected
    now = datetime.now(timezone.utc)
    logs = device_logs.copy()
    logs = _ensure_columns(logs, ["device_id", "timestamp", "event_type", "is_connected"])
    logs["timestamp"] = _parse_ts(logs["timestamp"])
    logs = logs.dropna(subset=["timestamp"]).sort_values("timestamp")
    durations: dict[str, float] = {}
    for device_id, grp in logs.groupby("device_id"):
        last_disconnect = grp.loc[grp["event_type"] == "disconnected", "timestamp"]
        disconnect_time = last_disconnect.iloc[-1] if not last_disconnect.empty else None
        post = grp if disconnect_time is None else grp[grp["timestamp"] > disconnect_time]
        connected_rows = post[post["is_connected"] == 1]
        if connected_rows.empty:
            continue
        start = connected_rows["timestamp"].iloc[0]
        durations[str(device_id)] = max(0.0, (now - start.to_pydatetime()).total_seconds())
    out = connected.copy()
    out["connection_duration_sec"] = out["device_id"].astype(str).map(durations).fillna(0.0).round(0)
    return out


def _format_device_rows(df: pd.DataFrame, device_logs: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty:
        return []
    rows = _attach_connection_duration(df, device_logs)
    cap = pd.to_numeric(rows.get("capacity_bytes"), errors="coerce")
    used = pd.to_numeric(rows.get("used_bytes"), errors="coerce")
    rows["capacity_gb"] = (cap / (1024**3)).round(2)
    rows["used_gb"] = (used / (1024**3)).round(2)
    rows["free_gb"] = ((cap - used) / (1024**3)).round(2)
    rows["usage_percent"] = pd.to_numeric(rows.get("usage_percent"), errors="coerce").round(1)
    rows["device_group"] = rows.get("device_group", rows["device_type"].map(_device_group))
    cols = [
        "timestamp",
        "device_id",
        "device_name",
        "device_type",
        "device_group",
        "mountpoint",
        "capacity_gb",
        "used_gb",
        "free_gb",
        "usage_percent",
        "connection_duration_sec",
        "source_os",
    ]
    for col in cols:
        if col not in rows.columns:
            rows[col] = None
    projected = rows[cols]
    return projected.where(pd.notna(projected), None).to_dict(orient="records")


def _storage_file_stats(mountpoint: str | None, max_entries: int = 5000) -> dict[str, int | None]:
    if not mountpoint:
        return {"file_count": None, "folder_count": None}
    try:
        root = str(mountpoint)
        if not os.path.exists(root):
            return {"file_count": None, "folder_count": None}
        cached = FILE_STATS_CACHE.get(root)
        now = time.time()
        if cached and now - cached[0] < FILE_STATS_TTL_SEC:
            return cached[1]
        files = 0
        folders = 0
        scanned = 0
        for _, dirnames, filenames in os.walk(root):
            folders += len(dirnames)
            files += len(filenames)
            scanned += len(dirnames) + len(filenames)
            if scanned >= max_entries:
                break
        result = {"file_count": files, "folder_count": folders}
        FILE_STATS_CACHE[root] = (now, result)
        return result
    except Exception:
        return {"file_count": None, "folder_count": None}


def _device_timeline(device_logs: pd.DataFrame, limit: int = 140) -> list[dict[str, Any]]:
    if device_logs.empty:
        return []
    df = device_logs.copy()
    df = _ensure_columns(df, ["timestamp", "event_type", "device_id", "device_name", "device_type", "mountpoint", "usage_percent"])
    df["timestamp"] = _parse_ts(df["timestamp"])
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp", ascending=False)
    events = df[df["event_type"].isin(["connected", "disconnected"])].head(limit).copy()
    if events.empty:
        return []
    events["device_group"] = events["device_type"].map(_device_group)
    cols = ["timestamp", "event_type", "device_id", "device_name", "device_type", "device_group", "mountpoint", "usage_percent"]
    for col in cols:
        if col not in events.columns:
            events[col] = None
    events["timestamp"] = events["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    projected = events[cols]
    return projected.where(pd.notna(projected), None).to_dict(orient="records")


def _dongle_buffer_state(device_logs: pd.DataFrame) -> dict[str, str]:
    if device_logs.empty:
        return {}
    df = device_logs.copy()
    df = _ensure_columns(df, ["timestamp", "device_type", "event_type", "device_id"])
    df["timestamp"] = _parse_ts(df["timestamp"])
    df = df.dropna(subset=["timestamp"])
    df = df[df["device_type"].isin(["input_dongle", "wifi_dongle"])]
    if df.empty:
        return {}
    states: dict[str, str] = {}
    for device_id, grp in df.groupby("device_id"):
        recent = grp.sort_values("timestamp", ascending=False).head(40)
        disconnects = int((recent["event_type"] == "disconnected").sum())
        snapshots = int((recent["event_type"] == "snapshot").sum())
        if disconnects >= 2:
            state = "unstable"
        elif snapshots >= 6:
            state = "active"
        else:
            state = "idle"
        states[str(device_id)] = state
    return states


def _ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in columns:
        if col not in out.columns:
            out[col] = None
    return out


def _memory_pattern_analysis(memory: pd.DataFrame, predictions: pd.DataFrame) -> dict[str, Any]:
    empty = {
        "spike_detected": False,
        "gradual_leak_detected": False,
        "abnormal_pattern": False,
        "predicted_vs_actual_mae": None,
        "predicted_vs_actual_bias": None,
        "severity": "low",
        "explanations": ["Insufficient data for pattern analysis."],
        "spike_timestamps": [],
    }
    if memory.empty:
        return dict(empty)
    mem = memory.copy()
    mem["ram_percent"] = pd.to_numeric(mem["ram_percent"], errors="coerce")
    mem = mem.dropna(subset=["ram_percent"])
    if mem.empty:
        return dict(empty)
    mem["_ts_raw"] = mem["timestamp"]
    mem["timestamp"] = _parse_ts(mem["timestamp"])
    mem = mem.dropna(subset=["timestamp"]).sort_values("timestamp")
    diffs = mem["ram_percent"].diff().fillna(0.0)
    spike_mask = diffs.abs() > 6.0
    spike_detected = bool(spike_mask.any())
    spike_rows = mem.loc[spike_mask, "timestamp"]
    spike_timestamps = [t.strftime("%Y-%m-%d %H:%M:%S") for t in spike_rows.head(8)]
    gradual_leak_detected = bool(detect_memory_leak(mem, window=8))
    abnormal_pattern = bool(mem["ram_percent"].tail(30).std() > 4.8 if len(mem) >= 30 else False)

    mae = None
    bias = None
    if not predictions.empty and {"predicted_ram_percent", "actual_ram_percent"}.issubset(predictions.columns):
        p = predictions.copy()
        p["predicted_ram_percent"] = pd.to_numeric(p["predicted_ram_percent"], errors="coerce")
        p["actual_ram_percent"] = pd.to_numeric(p["actual_ram_percent"], errors="coerce")
        p = p.dropna(subset=["predicted_ram_percent", "actual_ram_percent"]).tail(40)
        if not p.empty:
            errs = p["predicted_ram_percent"] - p["actual_ram_percent"]
            mae = float(errs.abs().mean())
            bias = float(errs.mean())

    severity = "low"
    explanations = []
    if spike_detected:
        explanations.append("Short-term RAM jumps were detected between consecutive cycles.")
        severity = "medium"
    if gradual_leak_detected:
        explanations.append("Sustained monotonic RAM growth indicates potential memory leak behavior.")
        severity = "high"
    if abnormal_pattern:
        explanations.append("Observed RAM volatility is above normal operational spread.")
        if severity == "low":
            severity = "medium"
    if not explanations:
        explanations.append("Memory trend appears stable with no major anomalies in recent windows.")

    return {
        "spike_detected": spike_detected,
        "gradual_leak_detected": gradual_leak_detected,
        "abnormal_pattern": abnormal_pattern,
        "predicted_vs_actual_mae": None if mae is None else round(mae, 3),
        "predicted_vs_actual_bias": None if bias is None else round(bias, 3),
        "severity": severity,
        "explanations": explanations,
        "spike_timestamps": spike_timestamps,
    }


def _graph_insights(
    patterns: dict[str, Any],
    risk_level: RiskLevel,
    current_ram: float,
    predicted_ram: float | None,
    stability: float,
    connected_devices: int,
    device_events_recent: int,
) -> dict[str, dict[str, str]]:
    """Short storytelling blocks for each chart (what / why / next). UI maps `next` to 'What it means'."""
    spike = bool(patterns.get("spike_detected"))
    leak = bool(patterns.get("gradual_leak_detected"))
    volatile = bool(patterns.get("abnormal_pattern"))
    mae = patterns.get("predicted_vs_actual_mae")
    bias = patterns.get("predicted_vs_actual_bias")

    mem_what = (
        "RAM and swap usage moved noticeably in the recent window."
        if spike or volatile
        else "RAM usage has been relatively steady in the recent window."
    )
    mem_why_parts: list[str] = []
    if spike:
        mem_why_parts.append("One or more sharp step changes in RAM percent were detected between samples.")
    if leak:
        mem_why_parts.append("A sustained upward drift suggests possible leak-like growth.")
    if connected_devices and device_events_recent:
        mem_why_parts.append("External device connect/disconnect activity coincides with some of these samples.")
    if not mem_why_parts:
        mem_why_parts.append("No strong anomaly signature in the latest memory trend slice.")
    mem_next = (
        "Expect continued pressure if background workloads stay high; watch the next prediction cycle."
        if (predicted_ram is not None and predicted_ram > current_ram + 2)
        else "Near-term usage is likely to track recent levels unless workload mix changes."
    )

    pred_what = "Model tracks predicted RAM versus observed values over time."
    pred_why = (
        f"Mean absolute error is about {mae:.2f} points."
        if isinstance(mae, (int, float))
        else "Not enough paired prediction/actual rows yet to score error tightly."
    )
    if isinstance(bias, (int, float)) and abs(float(bias)) > 1.0:
        pred_why += f" Signed bias {float(bias):+.2f} suggests the model tends to {'over' if bias > 0 else 'under'}-estimate."
    pred_next = (
        "If bias persists, refresh training data or reduce bursty workloads before trusting long horizons."
        if isinstance(mae, (int, float)) and float(mae) > 4
        else "Forecasts should remain useful for short-horizon planning."
    )

    stab_what = f"Stability index is near {stability:.1f}/100 based on RAM, swap, and risk posture."
    stab_why = (
        "Higher risk or swap use drags the score down."
        if risk_level != RiskLevel.NORMAL
        else "Risk and swap pressure are within calmer bands."
    )
    stab_next = "If risk escalates, expect the stability curve to dip until pressure eases."

    dev_what = "Device activity aggregates connects, disconnects, and concurrent attachments per timestamp bucket."
    dev_why = (
        "Frequent attach/detach churn can correlate with memory volatility on some hosts."
        if device_events_recent >= 6
        else "Device churn has been modest in the sampled window."
    )
    dev_next = "Eject unused storage and dongles when not needed to reduce noise and I/O pressure."

    return {
        "memory": {"what": mem_what, "why": " ".join(mem_why_parts), "next": mem_next},
        "prediction": {"what": pred_what, "why": pred_why, "next": pred_next},
        "stability": {"what": stab_what, "why": stab_why, "next": stab_next},
        "device_activity": {"what": dev_what, "why": dev_why, "next": dev_next},
    }


def _narrative_analysis(
    current_ram: float,
    risk_level: RiskLevel,
    health_category: str,
    patterns: dict[str, Any],
    reasons: list[str],
    connected_devices: int,
) -> str:
    """Single human-readable paragraph for dashboards and external reviewers."""
    sev = str(patterns.get("severity", "low"))
    bits: list[str] = [
        f"System RAM is near {current_ram:.1f}% with overall health marked as {health_category}.",
        f"Risk is assessed at {risk_level.value} with pattern severity {sev}.",
    ]
    if patterns.get("spike_detected"):
        bits.append("Short-term memory spikes were observed.")
    if patterns.get("gradual_leak_detected"):
        bits.append("A gradual upward drift suggests investigating for a possible memory leak.")
    if patterns.get("abnormal_pattern"):
        bits.append("RAM variability is higher than typical steady operation.")
    if connected_devices:
        bits.append(f"There are {connected_devices} active external device(s); heavy removable I/O can amplify pressure.")
    if reasons:
        bits.append("Key signals: " + " ".join(reasons[:3]))
    bits.append("This may lead to reduced responsiveness if pressure continues without mitigation.")
    return " ".join(bits)


def _ineff_by_pid(ineff: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    m: dict[int, dict[str, Any]] = {}
    for r in ineff:
        p = r.get("pid")
        if p is None:
            continue
        try:
            m[int(p)] = r
        except (TypeError, ValueError):
            continue
    return m


def _enrich_process_rows(process_slice: pd.DataFrame, ineff_by_pid: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    if process_slice.empty:
        return []
    rows = process_slice.to_dict(orient="records")
    for row in rows:
        pid = row.get("pid")
        if pid is None:
            continue
        try:
            pk = int(pid)
        except (TypeError, ValueError):
            continue
        src = ineff_by_pid.get(pk)
        if src is None:
            continue
        if row.get("inefficiency_score") is None and src.get("inefficiency_score") is not None:
            row["inefficiency_score"] = src.get("inefficiency_score")
    return rows


def _inefficient_processes(process_df: pd.DataFrame) -> list[dict[str, Any]]:
    if process_df.empty:
        return []
    p = process_df.copy()
    p["rss_mb"] = pd.to_numeric(p["rss_mb"], errors="coerce")
    p["memory_percent"] = pd.to_numeric(p["memory_percent"], errors="coerce")
    p = p.dropna(subset=["rss_mb", "memory_percent"])
    if p.empty:
        return []
    p["inefficiency_score"] = (0.7 * p["rss_mb"]) + (18.0 * p["memory_percent"])
    heavy = p[(p["rss_mb"] > 350.0) | (p["memory_percent"] > 4.0)].sort_values("inefficiency_score", ascending=False).head(6)
    out = heavy[["pid", "name", "rss_mb", "memory_percent", "inefficiency_score"]].round({"rss_mb": 2, "memory_percent": 2, "inefficiency_score": 2})
    return out.where(pd.notna(out), None).to_dict(orient="records")


def _dedupe_prioritized_actions(recs: list[dict[str, str]], max_items: int = 8) -> list[dict[str, str]]:
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for r in recs:
        key = (str(r.get("action") or "")).strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(r)
        if len(out) >= max_items:
            break
    return out


def _structured_recommendations(
    risk_level: RiskLevel,
    dos: list[str],
    donts: list[str],
    ineff: list[dict[str, Any]],
    connected_devices: int,
) -> list[dict[str, str]]:
    recs: list[dict[str, str]] = []
    if risk_level in {RiskLevel.CRITICAL, RiskLevel.EMERGENCY}:
        recs.append({"priority": "high", "action": "Reduce top memory-heavy processes immediately.", "why": "System is under high memory pressure."})
    if ineff:
        recs.append(
            {
                "priority": "high" if float(ineff[0].get("memory_percent", 0)) > 8.0 else "medium",
                "action": f"Investigate process '{ineff[0].get('name', 'unknown')}' (PID {ineff[0].get('pid', '-')}).",
                "why": "Marked as inefficient by memory intensity score.",
            }
        )
    if connected_devices > 0:
        recs.append({"priority": "medium", "action": "Eject unused external devices and dongles.", "why": "Reduces external-device pressure and churn."})
    if dos:
        recs.append({"priority": "medium", "action": dos[0], "why": "Recommended by risk analyzer."})
    if donts:
        recs.append({"priority": "low", "action": f"Avoid: {donts[0]}", "why": "Prevents avoidable memory instability."})
    return recs[:6]


@app.get("/api/health")
def health() -> dict[str, Any]:
    _start_pipeline_if_needed()
    return {"status": "ok", "time_utc": datetime.now(timezone.utc).isoformat(), "pipeline": _get_pipeline_state()}


@app.get("/api/pipeline/status")
def pipeline_status() -> dict[str, Any]:
    _start_pipeline_if_needed()
    return {"time_utc": datetime.now(timezone.utc).isoformat(), "pipeline": _get_pipeline_state()}


@app.get("/api/dashboard")
def dashboard() -> dict[str, Any]:
    _start_pipeline_if_needed()
    db = DatabaseManager()

    system = db.fetch_system_metrics(limit=520)
    memory = db.fetch_memory_logs(limit=520)
    predictions = db.fetch_predictions(limit=220)
    alerts = db.fetch_alerts(limit=120)
    analysis_rows = db.fetch_analysis_results(limit=80)
    device_logs = db.fetch_device_logs(limit=900)
    process = db.fetch_recent_process_metrics(limit=40)
    device_summary = db.fetch_device_activity_summary(limit=280)

    now = datetime.now(timezone.utc).isoformat()
    if system.empty:
        return _empty_dashboard_payload(now, "No telemetry data available yet.")

    latest = system.iloc[-1]
    current_ram = float(latest["ram_percent"])
    swap_percent = float(latest["swap_percent"])

    predicted_ram = None
    if not predictions.empty and "predicted_ram_percent" in predictions.columns:
        p = pd.to_numeric(predictions["predicted_ram_percent"], errors="coerce").dropna()
        if not p.empty:
            predicted_ram = float(p.iloc[-1])

    mem_for_leak = memory.copy() if not memory.empty else system.copy()
    leak_detected = bool(detect_memory_leak(mem_for_leak, window=8))
    patterns = _memory_pattern_analysis(memory, predictions)
    risk_report = classify_risk(
        current_ram_percent=current_ram,
        leak_detected=leak_detected,
        predicted_ram_percent=predicted_ram,
        device_pressure_score=float(
            0.0
            if device_logs.empty
            else (_ensure_columns(device_logs, ["event_type"])["event_type"].isin(["connected", "disconnected"]).sum() / 10.0)
        ),
    )
    stability = compute_stability_index(current_ram, swap_percent, risk_report.level)
    health_category = map_health_category(
        risk_report.level,
        anomaly_detected=bool(patterns["spike_detected"] or patterns["gradual_leak_detected"] or patterns["abnormal_pattern"]),
    )

    connected = _latest_connected_devices(device_logs)
    dongle_states = _dongle_buffer_state(device_logs)
    formatted_connected = _format_device_rows(connected, device_logs)
    for row in formatted_connected:
        if row.get("device_group") in {"input_dongle", "network_adapter"}:
            row["buffer_state"] = dongle_states.get(str(row.get("device_id", "")), "idle")
        if row.get("device_group") == "storage":
            stats = _storage_file_stats(str(row.get("mountpoint") or ""))
            row.update(stats)

    storage = [r for r in formatted_connected if r.get("device_group") == "storage"]
    dongles = [r for r in formatted_connected if r.get("device_group") == "input_dongle"]
    network_adapters = [r for r in formatted_connected if r.get("device_group") == "network_adapter"]

    ineff = _inefficient_processes(process)
    ineff_by_pid = _ineff_by_pid(ineff)
    algo_recs = greedy_optimization_strategy(process, risk_report.level) if not process.empty else []
    structured_recs = _structured_recommendations(
        risk_level=risk_report.level,
        dos=risk_report.dos,
        donts=risk_report.donts,
        ineff=ineff,
        connected_devices=len(formatted_connected),
    )
    for rec in algo_recs[:3]:
        structured_recs.append(
            {
                "priority": "medium" if risk_report.level == RiskLevel.WARNING else "high",
                "action": f"Process '{rec.process_name}' (PID {rec.pid}): {rec.recommendation}",
                "why": f"Priority score {rec.priority_score}",
            }
        )
    structured_recs = _dedupe_prioritized_actions(structured_recs, max_items=8)

    recent_device_events = 0
    if not device_logs.empty:
        ev = _ensure_columns(device_logs, ["event_type"])
        recent_device_events = int(ev["event_type"].isin(["connected", "disconnected"]).tail(200).sum())

    narrative = _narrative_analysis(
        current_ram=current_ram,
        risk_level=risk_report.level,
        health_category=health_category,
        patterns=patterns,
        reasons=risk_report.reasons,
        connected_devices=len(formatted_connected),
    )
    how_serious_line = (
        f"{risk_report.level.value} operational risk with {patterns.get('severity', 'low')} pattern severity; "
        f"stability score {round(float(stability), 1)}/100."
    )
    graph_insights = _graph_insights(
        patterns=patterns,
        risk_level=risk_report.level,
        current_ram=current_ram,
        predicted_ram=predicted_ram,
        stability=float(stability),
        connected_devices=len(formatted_connected),
        device_events_recent=recent_device_events,
    )

    # Frontend-friendly trend payload (trim and project columns).
    memory_trend = []
    if not memory.empty:
        m = memory.copy().tail(240)
        m = _ensure_columns(m, ["timestamp", "ram_percent", "swap_percent", "ram_used_mb", "available_mb"])
        m["timestamp"] = _parse_ts(m["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        for col in ["ram_percent", "swap_percent", "ram_used_mb", "available_mb"]:
            if col in m.columns:
                m[col] = pd.to_numeric(m[col], errors="coerce").round(3)
        memory_trend = m[["timestamp", "ram_percent", "swap_percent", "ram_used_mb", "available_mb"]].where(pd.notna(m), None).to_dict(orient="records")

    prediction_trend = []
    if not predictions.empty:
        pr = predictions.copy().tail(180)
        pr = _ensure_columns(pr, ["timestamp", "predicted_ram_percent", "actual_ram_percent", "model_name"])
        pr["timestamp"] = _parse_ts(pr["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        for col in ["predicted_ram_percent", "actual_ram_percent"]:
            if col in pr.columns:
                pr[col] = pd.to_numeric(pr[col], errors="coerce").round(3)
        prediction_trend = pr[["timestamp", "predicted_ram_percent", "actual_ram_percent", "model_name"]].where(pd.notna(pr), None).to_dict(orient="records")

    stability_trend = []
    if not alerts.empty:
        al = alerts.copy().tail(180)
        al = _ensure_columns(al, ["timestamp", "risk_level", "stability_index"])
        al["timestamp"] = _parse_ts(al["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        al["stability_index"] = pd.to_numeric(al["stability_index"], errors="coerce").round(3)
        stability_trend = al[["timestamp", "risk_level", "stability_index"]].where(pd.notna(al), None).to_dict(orient="records")

    device_activity = []
    if not device_summary.empty:
        ds = device_summary.copy().tail(220)
        ds = _ensure_columns(ds, ["timestamp"])
        ds["timestamp"] = _parse_ts(ds["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        device_activity = ds.where(pd.notna(ds), None).to_dict(orient="records")

    response = {
        "ready": True,
        "timestamp_utc": now,
        "metrics": {
            "ram_now_percent": round(current_ram, 2),
            "predicted_ram_percent": None if predicted_ram is None else round(predicted_ram, 2),
            "stability_score": round(float(stability), 2),
            "risk_level": risk_report.level.value,
            "health_category": health_category,
            "connected_devices": len(formatted_connected),
            "connected_storage": len(storage),
            "connected_dongles": len(dongles),
            "connected_network_adapters": len(network_adapters),
            "pipeline": _get_pipeline_state(),
        },
        "devices": {
            "connected": formatted_connected,
            "storage": storage,
            "dongles": dongles,
            "network_adapters": network_adapters,
            "timeline": _device_timeline(device_logs),
        },
        "trends": {
            "memory": memory_trend,
            "prediction": prediction_trend,
            "stability": stability_trend,
            "device_activity": device_activity,
        },
        "analysis": {
            "summary": (
                f"Current RAM is {round(current_ram, 2)}%. "
                f"Risk is {risk_report.level.value} and health category is {health_category}."
            ),
            "narrative": narrative,
            "graph_insights": graph_insights,
            "what_why_how": {
                "what": narrative.split(".")[0] + "." if narrative else "Memory and device posture is being assessed.",
                "why": (patterns.get("explanations") or [risk_report.reasons[0] if risk_report.reasons else "No single dominant cause identified."])[0],
                "how_serious": how_serious_line,
                "impact": how_serious_line,
            },
            "algorithm": "ML (RandomForest) + DAA (risk classification, stability indexing, greedy optimization)",
            "reasons": risk_report.reasons,
            "memory_patterns": patterns,
            "inefficient_processes": ineff,
            "processes": _enrich_process_rows(process.where(pd.notna(process), None).head(25), ineff_by_pid),
            "logs_preview": analysis_rows.where(pd.notna(analysis_rows), None).head(40).to_dict(orient="records"),
        },
        "recommendations": {
            "category": health_category,
            "dos": risk_report.dos,
            "donts": risk_report.donts,
            "prioritized_actions": structured_recs,
        },
    }

    return response

