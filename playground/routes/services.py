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


@router.get("/playground/services", response_class=HTMLResponse)
def services_show(request: Request, tab: str | None = None) -> HTMLResponse:
    state = get_state(request)
    settings = state.snapshot_settings()
    active_tab = tab if tab in {"mr", "render", "vpn"} else "mr"
    with build_client(settings) as client:
        mr_sessions = capture_api_call(
            state,
            label="octa_client.services.mr.list",
            method="GET",
            path="/services/mr",
            fn=lambda: client.services.mr.list(),
        )
        render_sessions = capture_api_call(
            state,
            label="octa_client.services.render.list",
            method="GET",
            path="/services/render",
            fn=lambda: client.services.render.list(),
        )
        vpn_sessions = capture_api_call(
            state,
            label="octa_client.services.vpn.list",
            method="GET",
            path="/services/vpn",
            fn=lambda: client.services.vpn.list(),
        )
        transport_stats = client.transport_stats()

    context: dict[str, Any] = base_context(
        request, page="services", title="Services",
        settings=settings, transport_stats=transport_stats,
    )
    context.update({
        "active_tab": active_tab,
        "mr_sessions": mr_sessions,
        "render_sessions": render_sessions,
        "vpn_sessions": vpn_sessions,
    })
    return get_templates(request).TemplateResponse(
        request=request, name="services.html", context=context,
    )
