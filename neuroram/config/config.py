"""Project-wide settings for NeuroRAM."""

from dataclasses import dataclass

from neuroram.config.settings import (
    DB_DIR,
    DB_FILENAME,
    DEFAULT_COLLECTION_INTERVAL_SEC,
    DEFAULT_CRITICAL_THRESHOLD,
    DEFAULT_EMERGENCY_THRESHOLD,
    DEFAULT_LEAK_GROWTH_THRESHOLD,
    DEFAULT_LOOKBACK_WINDOW,
    DEFAULT_PROCESS_LIMIT,
    DEFAULT_WARNING_THRESHOLD,
    EXPORTS_DIR,
    MIGRATIONS_DIR,
    MODELS_DIR,
    SEED_DATA_DIR,
)

DB_DIR.mkdir(parents=True, exist_ok=True)
MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)
SEED_DATA_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class AppConfig:
    db_path: str = str((DB_DIR / DB_FILENAME).resolve())
    model_dir: str = str(MODELS_DIR.resolve())
    rf_model_path: str = str((MODELS_DIR / "rf_model.joblib").resolve())
    scaler_path: str = str((MODELS_DIR / "scaler.joblib").resolve())
    lstm_model_path: str = str((MODELS_DIR / "lstm_model.keras").resolve())
    lookback_window: int = DEFAULT_LOOKBACK_WINDOW
    collection_interval_sec: int = DEFAULT_COLLECTION_INTERVAL_SEC
    process_limit: int = DEFAULT_PROCESS_LIMIT

    warning_threshold: float = DEFAULT_WARNING_THRESHOLD
    critical_threshold: float = DEFAULT_CRITICAL_THRESHOLD
    emergency_threshold: float = DEFAULT_EMERGENCY_THRESHOLD
    leak_growth_threshold: float = DEFAULT_LEAK_GROWTH_THRESHOLD


CONFIG = AppConfig()
