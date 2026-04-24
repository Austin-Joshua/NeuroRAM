#!/usr/bin/env bash
set -euo pipefail

if [ ! -d ".venv" ]; then
  python -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPYCACHEPREFIX=".cache/pycache"
uvicorn api_server:app --reload --port 8000
