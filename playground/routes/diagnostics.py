from __future__ import annotations

from datetime import datetime, timezone
from functools import partial
from time import monotonic
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from ..catalog import CALLS, call_for, default_payload, execute_call, payload_for, resolved_path
from ..errors import PayloadError, error_payload
from ..helpers import (  # noqa: F401 — diagnostics_preset_path registered in Jinja globals
    base_context,
    build_client,
    capture_api_call,
    diagnostics_preset_path,
    elapsed_ms,
    get_state,
    get_templates,
    parse_payload_json,
    validate_csrf,
)
from ..state import PlaygroundSettings
from ..views import summarize_payload

router = APIRouter()


def _transport_stats(settings: PlaygroundSettings) -> dict[str, Any]:
    with build_client(settings) as client:
        return client.transport_stats()


@router.get("/playground/diagnostics", response_class=HTMLResponse)
def diagnostics_show(
    request: Request,
    call: str | None = None,
    payload_json: str | None = None,
) -> HTMLResponse:
    settings = get_state(request).snapshot_settings()
    selected_call = call_for(call or CALLS[0].id)
    context: dict[str, Any] = base_context(
        request, page="diagnostics", title="Diagnostics",
        settings=settings, transport_stats=_transport_stats(settings),
    )
    context.update({
        "calls": CALLS,
        "selected_call": selected_call,
        "payload_json": (
            payload_json if payload_json is not None
            else default_payload(selected_call, settings)
        ),
        "result": {"status": "idle"},
    })
    return get_templates(request).TemplateResponse(
        request=request, name="diagnostics.html", context=context,
    )


@router.post("/playground/diagnostics/run", response_class=HTMLResponse)
async def diagnostics_run(request: Request) -> HTMLResponse:
    state = get_state(request)
    settings = state.snapshot_settings()
    form_data = await request.form()
    validate_csrf(request, str(form_data.get("csrf_token") or ""))
    selected_call = call_for(str(form_data.get("call") or CALLS[0].id))
    payload_json = str(form_data.get("payload_json") or "")

    try:
        payload = parse_payload_json(payload_json) if selected_call.takes_payload else None
    except ValueError as exc:
        result: dict[str, Any] = {
            "status": "error", "error": PayloadError(str(exc)), "duration_ms": 0,
        }
    else:
        started_at = monotonic()
        with build_client(settings) as client:
            response = capture_api_call(
                state,
                label=selected_call.label,
                method=selected_call.method,
                path=resolved_path(selected_call, payload),
                fn=lambda: execute_call(client, selected_call, payload),
            )
        duration_ms = elapsed_ms(started_at)
        from octaspace.errors import OctaSpaceError
        if isinstance(response, OctaSpaceError):
            result = {"status": "error", "error": response, "duration_ms": duration_ms}
        else:
            result = {
                "status": "success",
                "data": response.data,
                "response": response,
                "duration_ms": duration_ms,
            }

    context: dict[str, Any] = base_context(
        request, page="diagnostics", title="Diagnostics",
        settings=settings, transport_stats=_transport_stats(settings),
        page_url="/playground/diagnostics",
    )
    context.update({
        "calls": CALLS,
        "selected_call": selected_call,
        "payload_json": payload_json or default_payload(selected_call, settings),
        "result": result,
    })
    return get_templates(request).TemplateResponse(
        request=request, name="diagnostics.html", context=context,
    )


@router.post("/playground/diagnostics/smoke", response_class=HTMLResponse)
async def diagnostics_smoke(request: Request) -> HTMLResponse:
    from ..catalog import smoke_calls
    state = get_state(request)
    settings = state.snapshot_settings()
    form_data = await request.form()
    validate_csrf(request, str(form_data.get("csrf_token") or ""))
    suites = smoke_calls()
    started_at = monotonic()
    suite_results: list[dict[str, Any]] = []

    from octaspace.errors import OctaSpaceError
    with build_client(settings) as client:
        transport_stats = client.transport_stats()
        for suite in suites:
            suite_started = monotonic()
            response = capture_api_call(
                state,
                label=suite.label,
                method=suite.method,
                path=suite.path,
                fn=partial(execute_call, client, suite, payload_for(suite.id, settings)),
            )
            duration_ms = elapsed_ms(suite_started)
            if isinstance(response, OctaSpaceError):
                suite_results.append({
                    "id": suite.id, "label": suite.label,
                    "method": suite.method, "path": suite.path,
                    "requires_auth": suite.requires_auth,
                    "status": "failed", "duration_ms": duration_ms,
                    "error": error_payload(response),
                })
            else:
                suite_results.append({
                    "id": suite.id, "label": suite.label,
                    "method": suite.method, "path": suite.path,
                    "requires_auth": suite.requires_auth,
                    "status": "passed", "duration_ms": duration_ms,
                    "http_status": response.status_code,
                    "request_id": response.request_id,
                    "summary": summarize_payload(response.data),
                })

    failed = sum(1 for r in suite_results if r["status"] == "failed")
    smoke_result: dict[str, Any] = {
        "kind": "sdk_smoke",
        "status": "passed" if failed == 0 else "failed",
        "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "duration_ms": elapsed_ms(started_at),
        "summary": {
            "total": len(suite_results),
            "passed": len(suite_results) - failed,
            "failed": failed,
        },
        "suites": suite_results,
    }

    settings = state.snapshot_settings()
    selected_call = call_for("network.info")
    context: dict[str, Any] = base_context(
        request, page="diagnostics", title="Diagnostics",
        settings=settings, transport_stats=transport_stats,
        page_url="/playground/diagnostics",
    )
    context.update({
        "calls": CALLS,
        "selected_call": selected_call,
        "payload_json": default_payload(selected_call, settings),
        "result": {
            "status": "smoke", "duration_ms": smoke_result["duration_ms"], "data": smoke_result,
        },
    })
    return get_templates(request).TemplateResponse(
        request=request, name="diagnostics.html", context=context,
    )
