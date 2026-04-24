#!/usr/bin/env bash
set -euo pipefail

rm -rf .pytest_cache __pycache__ .cache frontend/dist
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -type f \( -name "*.pyc" -o -name "*.pyo" -o -name "*.pyd" \) -delete
rm -f db/neuroram.db-shm db/neuroram.db-wal

echo "Repository cache/artifact cleanup complete."
