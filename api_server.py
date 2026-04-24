"""Uvicorn entrypoint: run ``uvicorn api_server:app`` from the repository root."""

from backend.api.api_server import app

__all__ = ["app"]
