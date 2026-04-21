"""Centralized constants and defaults for NeuroRAM."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DB_DIR = PACKAGE_ROOT / "db"
MIGRATIONS_DIR = DB_DIR / "migrations"
SEED_DATA_DIR = DB_DIR / "seed_data"
EXPORTS_DIR = DB_DIR / "exports"
MODELS_DIR = PROJECT_ROOT / "models"

# Backward-compatible alias
DATA_DIR = DB_DIR

DB_FILENAME = "neuroram.db"

DEFAULT_LOOKBACK_WINDOW = 12
DEFAULT_COLLECTION_INTERVAL_SEC = 2
DEFAULT_PROCESS_LIMIT = 15

DEFAULT_WARNING_THRESHOLD = 70.0
DEFAULT_CRITICAL_THRESHOLD = 85.0
DEFAULT_EMERGENCY_THRESHOLD = 93.0
DEFAULT_LEAK_GROWTH_THRESHOLD = 7.0
