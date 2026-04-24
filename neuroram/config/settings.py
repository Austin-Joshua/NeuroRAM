"""Centralized constants and defaults for NeuroRAM."""

from __future__ import annotations

import os
from pathlib import Path


def _load_dotenv(dotenv_path: Path) -> None:
    """Load .env entries into process environment if not already set."""
    if not dotenv_path.exists():
        return
    for raw in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key:
            os.environ.setdefault(key, value)


def _int_env(name: str, fallback: int) -> int:
    value = os.getenv(name)
    if value is None:
        return fallback
    try:
        return int(value)
    except ValueError:
        return fallback


def _float_env(name: str, fallback: float) -> float:
    value = os.getenv(name)
    if value is None:
        return fallback
    try:
        return float(value)
    except ValueError:
        return fallback


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
_load_dotenv(PROJECT_ROOT / ".env")

DB_DIR = PROJECT_ROOT / "db"
MIGRATIONS_DIR = DB_DIR / "migrations"
SEED_DATA_DIR = DB_DIR / "seed_data"
EXPORTS_DIR = DB_DIR / "exports"
MODELS_DIR = PROJECT_ROOT / "models"

# Backward-compatible alias
DATA_DIR = DB_DIR

DB_FILENAME = os.getenv("NEURORAM_DB_FILENAME", "neuroram.db")

DEFAULT_LOOKBACK_WINDOW = _int_env("NEURORAM_LOOKBACK_WINDOW", 12)
DEFAULT_COLLECTION_INTERVAL_SEC = _int_env("NEURORAM_COLLECTION_INTERVAL_SEC", 2)
DEFAULT_PROCESS_LIMIT = _int_env("NEURORAM_PROCESS_LIMIT", 15)

DEFAULT_WARNING_THRESHOLD = _float_env("NEURORAM_WARNING_THRESHOLD", 70.0)
DEFAULT_CRITICAL_THRESHOLD = _float_env("NEURORAM_CRITICAL_THRESHOLD", 85.0)
DEFAULT_EMERGENCY_THRESHOLD = _float_env("NEURORAM_EMERGENCY_THRESHOLD", 93.0)
DEFAULT_LEAK_GROWTH_THRESHOLD = _float_env("NEURORAM_LEAK_GROWTH_THRESHOLD", 7.0)
DEFAULT_CORS_ORIGINS = os.getenv("NEURORAM_CORS_ORIGINS", "*")
