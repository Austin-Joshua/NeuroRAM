"""Prediction utilities for next RAM usage percentage."""

from __future__ import annotations

import numpy as np
import pandas as pd

from neuroram.backend.mlt_module.ml_engine import MLEngine, TENSORFLOW_AVAILABLE
from neuroram.config.config import CONFIG


def build_latest_feature_row(system_df: pd.DataFrame) -> pd.DataFrame:
    df = system_df.copy()
    parsed_ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.loc[parsed_ts.notna()].copy()
    df["timestamp"] = parsed_ts[parsed_ts.notna()].dt.tz_convert(None)
    df = df.sort_values("timestamp")
    if len(df) < 3:
        raise ValueError("Need at least 3 rows for feature engineering.")

    latest = df.iloc[-1]
    return pd.DataFrame(
        [
            {
                "cpu_percent": latest["cpu_percent"],
                "swap_percent": latest["swap_percent"],
                "available_mb": latest["available_mb"],
                "minute": latest["timestamp"].minute,
                "hour": latest["timestamp"].hour,
                "ram_lag_1": df.iloc[-2]["ram_percent"],
                "ram_lag_2": df.iloc[-3]["ram_percent"],
                "ram_roll_mean_3": df.tail(3)["ram_percent"].mean(),
            }
        ]
    )


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
