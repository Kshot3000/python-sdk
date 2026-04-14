from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from ..helpers import (
    base_context,
    build_client,
    capture_api_call,
    get_state,
    get_templates,
)

router = APIRouter()


@router.get("/playground/apps", response_class=HTMLResponse)
def apps(request: Request) -> HTMLResponse:
    state = get_state(request)
    settings = state.snapshot_settings()
    with build_client(settings) as client:
        apps_result = capture_api_call(
            state,
            label="octa_client.apps.list",
            method="GET",
            path="/apps",
            fn=lambda: client.apps.list(),
        )
        transport_stats = client.transport_stats()

    context: dict[str, Any] = base_context(
        request, page="apps", title="Apps",
        settings=settings, transport_stats=transport_stats,
    )
    context.update({"apps": apps_result})
    return get_templates(request).TemplateResponse(
        request=request, name="apps.html", context=context,
    )
