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

from backend.DAA.optimizer import greedy_optimization_strategy
from backend.DAA.risk_analyzer import RiskLevel, classify_risk, detect_memory_leak, map_health_category
from backend.DAA.stability_index import compute_stability_index
from backend.DBMS.database import DatabaseManager
from backend.MLT.ml_engine import MLEngine
from backend.MLT.predictor import predict_next_ram
from backend.OS.system_monitor import collect_and_store
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
}
PIPELINE_LOCK = threading.Lock()
PIPELINE_STOP = threading.Event()
PIPELINE_THREAD: threading.Thread | None = None


def _set_pipeline_state(**updates: Any) -> None:
    with PIPELINE_LOCK:
        PIPELINE_STATE.update(updates)


def _get_pipeline_state() -> dict[str, Any]:
    with PIPELINE_LOCK:
        return dict(PIPELINE_STATE)


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
        try:
            result = _pipeline_cycle(db, ml, previous_devices, cycle_count)
            previous_devices = result["state"]
            _set_pipeline_state(
                running=True,
                cycles=cycle_count,
                last_cycle_utc=datetime.now(timezone.utc).isoformat(),
                last_error=None,
                last_prediction=result["predicted_ram"],
            )
        except Exception as exc:
            _set_pipeline_state(
                running=True,
                cycles=cycle_count,
                last_cycle_utc=datetime.now(timezone.utc).isoformat(),
                last_error=str(exc),
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
    return rows[cols].fillna("").to_dict(orient="records")


def _storage_file_stats(mountpoint: str | None, max_entries: int = 5000) -> dict[str, int | None]:
    if not mountpoint:
        return {"file_count": None, "folder_count": None}
    try:
        root = str(mountpoint)
        if not os.path.exists(root):
            return {"file_count": None, "folder_count": None}
        files = 0
        folders = 0
        scanned = 0
        for _, dirnames, filenames in os.walk(root):
            folders += len(dirnames)
            files += len(filenames)
            scanned += len(dirnames) + len(filenames)
            if scanned >= max_entries:
                break
        return {"file_count": files, "folder_count": folders}
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
    return events[cols].fillna("").to_dict(orient="records")


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
    if memory.empty:
        return {
            "spike_detected": False,
            "gradual_leak_detected": False,
            "abnormal_pattern": False,
            "predicted_vs_actual_mae": None,
            "predicted_vs_actual_bias": None,
        }
    mem = memory.copy()
    mem["ram_percent"] = pd.to_numeric(mem["ram_percent"], errors="coerce")
    mem = mem.dropna(subset=["ram_percent"])
    if mem.empty:
        return {
            "spike_detected": False,
            "gradual_leak_detected": False,
            "abnormal_pattern": False,
            "predicted_vs_actual_mae": None,
            "predicted_vs_actual_bias": None,
        }
    diffs = mem["ram_percent"].diff().fillna(0.0)
    spike_detected = bool((diffs.abs() > 6.0).any())
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

    return {
        "spike_detected": spike_detected,
        "gradual_leak_detected": gradual_leak_detected,
        "abnormal_pattern": abnormal_pattern,
        "predicted_vs_actual_mae": None if mae is None else round(mae, 3),
        "predicted_vs_actual_bias": None if bias is None else round(bias, 3),
    }


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
    return (
        heavy[["pid", "name", "rss_mb", "memory_percent", "inefficiency_score"]]
        .round({"rss_mb": 2, "memory_percent": 2, "inefficiency_score": 2})
        .fillna("")
        .to_dict(orient="records")
    )


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
        return {
            "ready": False,
            "timestamp_utc": now,
            "message": "No telemetry data available yet.",
            "metrics": {},
            "devices": {},
            "trends": {},
            "analysis": {},
            "recommendations": {},
        }

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

    # Frontend-friendly trend payload (trim and project columns).
    memory_trend = []
    if not memory.empty:
        m = memory.copy().tail(240)
        m = _ensure_columns(m, ["timestamp", "ram_percent", "swap_percent", "ram_used_mb", "available_mb"])
        m["timestamp"] = _parse_ts(m["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        for col in ["ram_percent", "swap_percent", "ram_used_mb", "available_mb"]:
            if col in m.columns:
                m[col] = pd.to_numeric(m[col], errors="coerce").round(3)
        memory_trend = m[["timestamp", "ram_percent", "swap_percent", "ram_used_mb", "available_mb"]].fillna("").to_dict(orient="records")

    prediction_trend = []
    if not predictions.empty:
        pr = predictions.copy().tail(180)
        pr = _ensure_columns(pr, ["timestamp", "predicted_ram_percent", "actual_ram_percent", "model_name"])
        pr["timestamp"] = _parse_ts(pr["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        for col in ["predicted_ram_percent", "actual_ram_percent"]:
            if col in pr.columns:
                pr[col] = pd.to_numeric(pr[col], errors="coerce").round(3)
        prediction_trend = pr[["timestamp", "predicted_ram_percent", "actual_ram_percent", "model_name"]].fillna("").to_dict(orient="records")

    stability_trend = []
    if not alerts.empty:
        al = alerts.copy().tail(180)
        al = _ensure_columns(al, ["timestamp", "risk_level", "stability_index"])
        al["timestamp"] = _parse_ts(al["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        al["stability_index"] = pd.to_numeric(al["stability_index"], errors="coerce").round(3)
        stability_trend = al[["timestamp", "risk_level", "stability_index"]].fillna("").to_dict(orient="records")

    device_activity = []
    if not device_summary.empty:
        ds = device_summary.copy().tail(220)
        ds = _ensure_columns(ds, ["timestamp"])
        ds["timestamp"] = _parse_ts(ds["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        device_activity = ds.fillna("").to_dict(orient="records")

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
            "reasons": risk_report.reasons,
            "memory_patterns": patterns,
            "inefficient_processes": ineff,
            "processes": process.fillna("").head(25).to_dict(orient="records"),
            "logs_preview": analysis_rows.fillna("").head(40).to_dict(orient="records"),
        },
        "recommendations": {
            "category": health_category,
            "dos": risk_report.dos,
            "donts": risk_report.donts,
            "prioritized_actions": structured_recs[:8],
        },
    }

    # Backward-compatible keys for existing consumers.
    response["summary"] = {"text": response["analysis"]["summary"]}
    response["kpis"] = {
        "ram_now_percent": response["metrics"]["ram_now_percent"],
        "predicted_ram_percent": response["metrics"]["predicted_ram_percent"],
        "stability_score": response["metrics"]["stability_score"],
        "risk_status": response["metrics"]["risk_level"],
        "connected_devices": response["metrics"]["connected_devices"],
        "process_count": len(process),
    }
    response["actions"] = {
        "dos": response["recommendations"]["dos"],
        "donts": response["recommendations"]["donts"],
        "reasons": response["analysis"]["reasons"],
        "analysis": response["analysis"]["logs_preview"],
        "alerts": alerts.fillna("").head(50).to_dict(orient="records"),
    }
    return response

