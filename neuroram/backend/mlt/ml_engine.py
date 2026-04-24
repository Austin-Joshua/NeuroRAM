"""Training and model management for RAM prediction."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from neuroram.config.config import CONFIG

try:
    from tensorflow.keras.layers import LSTM, Dense
    from tensorflow.keras.models import Sequential, load_model

    TENSORFLOW_AVAILABLE = True
except Exception:
    TENSORFLOW_AVAILABLE = False

FEATURE_COLUMNS = [
    "ram_delta_1",
    "swap_percent",
    "available_mb",
    "device_connected_count",
    "device_event_intensity",
    "minute",
    "hour",
    "ram_lag_1",
    "ram_lag_2",
    "ram_roll_mean_3",
]


class MLEngine:
    def __init__(self) -> None:
        Path(CONFIG.model_dir).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def prepare_features(system_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        df = system_df.copy()
        # Handle mixed timestamp formats robustly (with/without timezone offsets).
        try:
            parsed_ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce", format="mixed")
        except TypeError:
            parsed_ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        df = df.loc[parsed_ts.notna()].copy()
        df["timestamp"] = parsed_ts[parsed_ts.notna()].dt.tz_convert(None)
        df = df.sort_values("timestamp")
        if "device_connected_count" not in df.columns:
            df["device_connected_count"] = 0.0
        if "device_event_intensity" not in df.columns:
            df["device_event_intensity"] = 0.0
        numeric_cols = ["ram_percent", "swap_percent", "available_mb"]
        numeric_cols.extend(["device_connected_count", "device_event_intensity"])
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna(subset=numeric_cols).reset_index(drop=True)
        df["ram_delta_1"] = df["ram_percent"].diff().fillna(0.0)
        df["minute"] = df["timestamp"].dt.minute
        df["hour"] = df["timestamp"].dt.hour
        df["ram_lag_1"] = df["ram_percent"].shift(1)
        df["ram_lag_2"] = df["ram_percent"].shift(2)
        df["ram_roll_mean_3"] = df["ram_percent"].rolling(3).mean()
        df["target_next_ram"] = df["ram_percent"].shift(-1)
        df = df.dropna().reset_index(drop=True)

        features = df[FEATURE_COLUMNS]
        target = df["target_next_ram"]
        return features, target

    def train_random_forest(self, system_df: pd.DataFrame) -> dict:
        X, y = self.prepare_features(system_df)
        if len(X) < 30:
            raise ValueError("Not enough data to train model. Collect at least 30 samples.")

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

        model = RandomForestRegressor(n_estimators=250, max_depth=12, random_state=42)
        model.fit(X_train, y_train)
        pred = model.predict(X_test)

        joblib.dump(model, CONFIG.rf_model_path)
        joblib.dump(scaler, CONFIG.rf_scaler_path)

        return {
            "model": "RandomForestRegressor",
            "mae": round(float(mean_absolute_error(y_test, pred)), 4),
            "rmse": round(float(np.sqrt(mean_squared_error(y_test, pred))), 4),
            "r2": round(float(r2_score(y_test, pred)), 4),
            "train_samples": int(len(X_train)),
            "test_samples": int(len(X_test)),
        }

    def train_lstm(self, system_df: pd.DataFrame, epochs: int = 15) -> dict:
        if not TENSORFLOW_AVAILABLE:
            raise RuntimeError("TensorFlow is not installed. LSTM training unavailable.")

        X, y = self.prepare_features(system_df)
        if len(X) < 60:
            raise ValueError("Not enough data to train LSTM. Collect at least 60 samples.")

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        lookback = CONFIG.lookback_window
        seq_X, seq_y = [], []
        for i in range(lookback, len(X_scaled)):
            seq_X.append(X_scaled[i - lookback : i])
            seq_y.append(y.iloc[i])

        seq_X = np.array(seq_X)
        seq_y = np.array(seq_y)

        X_train, X_test, y_train, y_test = train_test_split(seq_X, seq_y, test_size=0.2, random_state=42)
        model = Sequential(
            [
                LSTM(32, input_shape=(X_train.shape[1], X_train.shape[2])),
                Dense(16, activation="relu"),
                Dense(1),
            ]
        )
        model.compile(optimizer="adam", loss="mse")
        model.fit(X_train, y_train, epochs=epochs, batch_size=16, verbose=0)
        pred = model.predict(X_test, verbose=0).flatten()

        model.save(CONFIG.lstm_model_path)
        joblib.dump(scaler, CONFIG.lstm_scaler_path)

        return {
            "model": "LSTM",
            "mae": round(float(mean_absolute_error(y_test, pred)), 4),
            "rmse": round(float(np.sqrt(mean_squared_error(y_test, pred))), 4),
            "r2": round(float(r2_score(y_test, pred)), 4),
            "train_samples": int(len(X_train)),
            "test_samples": int(len(X_test)),
        }

    @staticmethod
    def load_rf_model():
        model = joblib.load(CONFIG.rf_model_path)
        scaler = joblib.load(CONFIG.rf_scaler_path)
        return model, scaler

    @staticmethod
    def load_lstm_model():
        if not TENSORFLOW_AVAILABLE:
            raise RuntimeError("TensorFlow is not installed. LSTM loading unavailable.")
        model = load_model(CONFIG.lstm_model_path)
        scaler = joblib.load(CONFIG.lstm_scaler_path)
        return model, scaler
