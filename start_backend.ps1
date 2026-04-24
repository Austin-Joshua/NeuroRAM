$ErrorActionPreference = "Stop"

if (!(Test-Path ".venv")) {
  python -m venv .venv
}

.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPYCACHEPREFIX = ".cache/pycache"
uvicorn api_server:app --reload --port 8000
