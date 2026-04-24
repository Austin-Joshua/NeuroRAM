$ErrorActionPreference = "Stop"

$paths = @(
  ".pytest_cache",
  "__pycache__",
  ".cache",
  "frontend/dist"
)

foreach ($p in $paths) {
  if (Test-Path $p) {
    Remove-Item -Recurse -Force $p
  }
}

Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | ForEach-Object {
  Remove-Item -Recurse -Force $_.FullName
}

Get-ChildItem -Path . -Recurse -Include "*.pyc","*.pyo","*.pyd" -File | ForEach-Object {
  Remove-Item -Force $_.FullName
}

if (Test-Path "db/neuroram.db-shm") { Remove-Item -Force "db/neuroram.db-shm" }
if (Test-Path "db/neuroram.db-wal") { Remove-Item -Force "db/neuroram.db-wal" }

Write-Host "Repository cache/artifact cleanup complete."
