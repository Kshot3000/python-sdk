from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from secrets import compare_digest
from time import monotonic
from typing import Any, cast
from urllib.parse import urlencode

from fastapi import HTTPException, Request
from fastapi.templating import Jinja2Templates

from octaspace import OctaSpaceClient
from octaspace.config import ClientConfig
from octaspace.errors import OctaSpaceError
from octaspace.response import APIResponse

from .catalog import payload_for
from .mock_data import build_mock_transport
from .state import MOCK_SCENARIOS, PlaygroundSettings, PlaygroundState

# ---------------------------------------------------------------------------
# Nav items
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class NavItem:
    id: str
    name: str
    path: str
    badge: str | None = None


NAV_ITEMS: tuple[NavItem, ...] = (
    NavItem(id="dashboard",   name="Dashboard",   path="/playground/dashboard"),
    NavItem(id="network",     name="Network",     path="/playground/network",     badge="public"),
    NavItem(id="apps",        name="Apps",        path="/playground/apps"),
    NavItem(id="nodes",       name="Nodes",       path="/playground/nodes"),
    NavItem(id="sessions",    name="Sessions",    path="/playground/sessions"),
    NavItem(id="services",    name="Services",    path="/playground/services"),
    NavItem(id="idle_jobs",   name="Idle Jobs",   path="/playground/idle-jobs"),
    NavItem(id="diagnostics", name="Diagnostics", path="/playground/diagnostics", badge="mock"),
)


# ---------------------------------------------------------------------------
# FastAPI app-state accessors
# ---------------------------------------------------------------------------

def get_state(request: Request) -> PlaygroundState:
    return cast(PlaygroundState, request.app.state.playground_state)


def get_templates(request: Request) -> Jinja2Templates:
    return cast(Jinja2Templates, request.app.state.templates)


def get_csrf_token(request: Request) -> str:
    return cast(str, request.app.state.csrf_token)


def validate_csrf(request: Request, submitted_token: str | None = None) -> None:
    candidate = (
        (submitted_token or "").strip()
        or request.headers.get("x-csrf-token", "").strip()
        or request.query_params.get("csrf_token", "").strip()
    )
    expected = get_csrf_token(request)
    if not candidate or not compare_digest(candidate, expected):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")


# ---------------------------------------------------------------------------
# Client factory
# ---------------------------------------------------------------------------

def build_client(settings: PlaygroundSettings) -> OctaSpaceClient:
    config = ClientConfig(
        api_key=settings.api_key or None,
        base_url=settings.base_url,
        keep_alive=False,
    )
    if settings.is_mock_active:
        return OctaSpaceClient(config=config, transport=build_mock_transport(settings))
    return OctaSpaceClient(config=config)


def playground_config(settings: PlaygroundSettings) -> ClientConfig:
    return ClientConfig(api_key=settings.api_key or None, base_url=settings.base_url)


def config_snapshot(settings: PlaygroundSettings) -> dict[str, Any]:
    config = playground_config(settings)
    return {
        "urls": config.urls,
        "mock_scenario": settings.mock_scenario,
        "open_timeout": config.open_timeout,
        "read_timeout": config.read_timeout,
        "write_timeout": config.write_timeout,
        "keep_alive": config.keep_alive,
        "pool_size": config.pool_size,
        "pool_timeout": config.pool_timeout,
        "idle_timeout": config.idle_timeout,
        "max_retries": config.max_retries,
        "retry_interval": config.retry_interval,
        "backoff_factor": config.backoff_factor,
    }


# ---------------------------------------------------------------------------
# Request capture
# ---------------------------------------------------------------------------

def capture_api_call(
    state: PlaygroundState,
    *,
    label: str,
    method: str,
    path: str,
    fn: Callable[[], APIResponse],
) -> APIResponse | OctaSpaceError:
    started_at = monotonic()
    try:
        response = fn()
    except OctaSpaceError as exc:
        state.append_request(
            label=label,
            method=method,
            path=path,
            status=_status_for_error(exc),
            duration_ms=elapsed_ms(started_at),
            error=str(exc),
        )
        return exc
    state.append_request(
        label=label,
        method=method,
        path=path,
        status=str(response.status_code),
        duration_ms=elapsed_ms(started_at),
    )
    return response


def elapsed_ms(started_at: float) -> int:
    return round((monotonic() - started_at) * 1000)


def _status_for_error(error: OctaSpaceError) -> str:
    from octaspace.errors import APIError
    if isinstance(error, APIError):
        return str(error.status_code)
    return "ERR"


# ---------------------------------------------------------------------------
# Template context
# ---------------------------------------------------------------------------

def base_context(
    request: Request,
    *,
    page: str,
    title: str,
    settings: PlaygroundSettings,
    transport_stats: dict[str, Any],
    page_url: str | None = None,
) -> dict[str, Any]:
    resolved_page_url = page_url or (
        request.url.path + (f"?{request.url.query}" if request.url.query else "")
    )
    return {
        "request": request,
        "page": page,
        "title": title,
        "page_url": resolved_page_url,
        "csrf_token": get_csrf_token(request),
        "nav_items": NAV_ITEMS,
        "settings": settings,
        "config": playground_config(settings),
        "mock_scenarios": MOCK_SCENARIOS,
        "request_log": get_state(request).request_log(),
        "transport_stats": transport_stats,
        "playground_api_key_present": settings.api_key_present,
        "playground_auth_available": settings.auth_available,
        "playground_mock_active": settings.is_mock_active,
        "playground_mock_scenario": settings.mock_scenario,
        "playground_masked_api_key": settings.masked_api_key,
        "playground_transport_label": settings.transport_label,
        "playground_transport_description": settings.transport_description,
        "playground_timeout_label": _timeout_label(settings),
    }


def _timeout_label(settings: PlaygroundSettings) -> str:
    config = playground_config(settings)
    return f"{config.open_timeout}s / {config.read_timeout}s"


# ---------------------------------------------------------------------------
# URL / routing helpers
# ---------------------------------------------------------------------------

def safe_return_path(path: str | None) -> str:
    candidate = (path or "").strip()
    if candidate.startswith("/") and not candidate.startswith("//"):
        return candidate
    return "/playground/dashboard"


def query_url(request: Request, param: str, value: str) -> str:
    query = dict(request.query_params)
    query[param] = value
    encoded = urlencode(query)
    return f"{request.url.path}?{encoded}" if encoded else request.url.path


def diagnostics_preset_path(
    request: Request,
    call_id: str,
    settings: PlaygroundSettings,
    overrides: dict[str, Any] | None = None,
) -> str:
    payload = payload_for(call_id, settings) or {}
    if overrides:
        payload.update({k: v for k, v in overrides.items() if v not in (None, "")})
    query = urlencode({
        "call": call_id,
        "payload_json": json.dumps(payload, indent=2, ensure_ascii=False),
    })
    return f"/playground/diagnostics?{query}"


# ---------------------------------------------------------------------------
# Payload parsing
# ---------------------------------------------------------------------------

def parse_payload_json(payload_json: str) -> dict[str, Any]:
    if not payload_json.strip():
        return {}
    try:
        parsed = json.loads(payload_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("Payload JSON must be an object")
    return parsed
