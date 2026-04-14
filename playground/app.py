"""OctaSpace SDK Browser Playground — application factory.

The playground is a development-only FastAPI application shipped alongside
the SDK source but NOT included in the PyPI wheel.  It lets developers
verify SDK behaviour against mock scenarios or a live API key directly in
the browser, mirroring the role of the Rails Dummy app in the Ruby gem.

Running
-------
After installing the playground dependency group::

    uv sync --group playground
    uvicorn playground.main:app --reload

Then open http://127.0.0.1:8000/playground/dashboard
"""
from __future__ import annotations

from pathlib import Path
from secrets import token_urlsafe

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .errors import error_payload
from .helpers import (
    base_context,  # noqa: F401 — kept for external use / tests
    build_client,  # noqa: F401
    capture_api_call,  # noqa: F401
    config_snapshot,
    diagnostics_preset_path,
    query_url,
)
from .json_renderer import json_html
from .state import PlaygroundState
from .views import (
    app_ports_count,
    format_bytes,
    format_datetime,
    format_duration,
    format_short_time,
    node_gpu_count,
    node_gpu_model,
    node_location,
    node_ram_label,
    node_summary_rows,
    playground_present,
    response_data,
    response_error,
    response_request_id,
    response_status,
    session_service_badge_class,
    session_service_label,
    session_status_badge_class,
    session_status_label,
    show_service_column,
    transport_description,
    transport_label,
    truncate_value,
)

_ROOT = Path(__file__).resolve().parent


def create_app(state: PlaygroundState | None = None) -> FastAPI:
    """Create and return a configured FastAPI playground application.

    Pass a *PlaygroundState* instance to inject pre-configured state
    (useful in tests).  If omitted, a fresh default state is used.
    """
    app = FastAPI(title="OctaSpace SDK Playground", docs_url=None, redoc_url=None)
    app.state.playground_state = state or PlaygroundState()
    app.state.csrf_token = token_urlsafe(32)

    # --- templates ----------------------------------------------------------
    templates = Jinja2Templates(directory=str(_ROOT / "templates"))
    templates.env.globals.update(
        # layout helpers
        query_url=query_url,
        diagnostics_preset_path=diagnostics_preset_path,
        config_snapshot=config_snapshot,
        present=playground_present,
        # formatting
        format_duration=format_duration,
        format_bytes=format_bytes,
        format_datetime=format_datetime,
        format_short_time=format_short_time,
        truncate_value=truncate_value,
        # response inspection
        response_data=response_data,
        response_error=response_error,
        response_status=response_status,
        response_request_id=response_request_id,
        # node
        node_location=node_location,
        node_gpu_model=node_gpu_model,
        node_gpu_count=node_gpu_count,
        node_ram_label=node_ram_label,
        node_summary_rows=node_summary_rows,
        # app
        app_ports_count=app_ports_count,
        # session
        session_service_label=session_service_label,
        session_service_badge_class=session_service_badge_class,
        session_status_label=session_status_label,
        session_status_badge_class=session_status_badge_class,
        show_service_column=show_service_column,
        # transport
        transport_label=transport_label,
        transport_description=transport_description,
        # error display
        error_payload=error_payload,
    )
    templates.env.filters["json_html"] = json_html
    # Store templates in app state so route handlers can access them
    app.state.templates = templates

    # --- static files -------------------------------------------------------
    app.mount(
        "/playground/static",
        StaticFiles(directory=str(_ROOT / "static")),
        name="playground_static",
    )

    # --- routes -------------------------------------------------------------
    from .routes import router
    app.include_router(router)

    return app
