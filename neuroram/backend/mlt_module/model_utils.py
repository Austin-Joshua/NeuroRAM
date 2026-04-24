"""Prediction utilities for next RAM usage percentage."""

from __future__ import annotations

import numpy as np
import pandas as pd

from backend.MLT.ml_engine import FEATURE_COLUMNS, MLEngine, TENSORFLOW_AVAILABLE
from neuroram.config.config import CONFIG


def build_latest_feature_row(system_df: pd.DataFrame) -> pd.DataFrame:
    df = system_df.copy()
    try:
        parsed_ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce", format="mixed")
    except TypeError:
        parsed_ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.loc[parsed_ts.notna()].copy()
    df["timestamp"] = parsed_ts[parsed_ts.notna()].dt.tz_convert(None)
    df = df.sort_values("timestamp")
    if len(df) < 3:
        raise ValueError("Need at least 3 rows for feature engineering.")
    if "device_connected_count" not in df.columns:
        df["device_connected_count"] = 0.0
    if "device_event_intensity" not in df.columns:
        df["device_event_intensity"] = 0.0
    df["ram_delta_1"] = df["ram_percent"].diff().fillna(0.0)

    latest = df.iloc[-1]
    feature_df = pd.DataFrame(
        [
            {
                "ram_delta_1": latest["ram_delta_1"],
                "swap_percent": latest["swap_percent"],
                "available_mb": latest["available_mb"],
                "device_connected_count": latest.get("device_connected_count", 0.0),
                "device_event_intensity": latest.get("device_event_intensity", 0.0),
                "minute": latest["timestamp"].minute,
                "hour": latest["timestamp"].hour,
                "ram_lag_1": df.iloc[-2]["ram_percent"],
                "ram_lag_2": df.iloc[-3]["ram_percent"],
                "ram_roll_mean_3": df.tail(3)["ram_percent"].mean(),
            }
        ]
    )
    return feature_df[FEATURE_COLUMNS]


def predict_next_ram(system_df: pd.DataFrame, model_choice: str = "rf") -> float:
    features = build_latest_feature_row(system_df)

    if model_choice == "lstm":
        if not TENSORFLOW_AVAILABLE:
            raise RuntimeError("TensorFlow is unavailable. Use RandomForest model.")
        model, scaler = MLEngine.load_lstm_model()
        x_scaled = scaler.transform(features)
        x_seq = np.repeat(x_scaled[np.newaxis, :, :], CONFIG.lookback_window, axis=1)
        pred = model.predict(x_seq, verbose=0).flatten()[0]
        return float(pred)

    model, scaler = MLEngine.load_rf_model()
    x_scaled = scaler.transform(features)
    pred = model.predict(x_scaled)[0]
    return float(pred)
