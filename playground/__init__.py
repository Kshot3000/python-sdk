"""OctaSpace SDK Browser Playground (development only — not shipped to PyPI).

Quick start::

    uv sync --group playground
    uvicorn playground.main:app --reload
"""
from .app import create_app

__all__ = ["create_app"]
