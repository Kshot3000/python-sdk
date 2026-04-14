"""Uvicorn entry point for the OctaSpace SDK Browser Playground.

The playground is a dev-only tool (not shipped to PyPI).
Run from the project root after installing playground dependencies:

    uv sync --group playground
    uvicorn playground.main:app --reload

Then open:  http://127.0.0.1:8000/playground/dashboard
"""
from __future__ import annotations

from .app import create_app

app = create_app()
