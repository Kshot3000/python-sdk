from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from ..helpers import (
    base_context,
    build_client,
    capture_api_call,
    config_snapshot,
    get_state,
    get_templates,
)

router = APIRouter()


@router.get("/playground/dashboard", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    state = get_state(request)
    settings = state.snapshot_settings()
    with build_client(settings) as client:
        network = capture_api_call(
            state,
            label="octa_client.network.info",
            method="GET",
            path="/network",
            fn=lambda: client.network.info(),
        )
        if settings.api_key_present:
            profile = capture_api_call(
                state,
                label="octa_client.accounts.profile",
                method="GET",
                path="/accounts",
                fn=lambda: client.accounts.profile(),
            )
            balance = capture_api_call(
                state,
                label="octa_client.accounts.balance",
                method="GET",
                path="/accounts/balance",
                fn=lambda: client.accounts.balance(),
            )
        else:
            profile = None
            balance = None
        transport_stats = client.transport_stats()

    context: dict[str, Any] = base_context(
        request, page="dashboard", title="Dashboard",
        settings=settings, transport_stats=transport_stats,
    )
    context.update({"network": network, "profile": profile, "balance": balance})
    return get_templates(request).TemplateResponse(
        request=request, name="dashboard.html", context=context,
    )


@router.get("/playground/network", response_class=HTMLResponse)
def network(request: Request) -> HTMLResponse:
    state = get_state(request)
    settings = state.snapshot_settings()
    with build_client(settings) as client:
        network_result = capture_api_call(
            state,
            label="octa_client.network.info",
            method="GET",
            path="/network",
            fn=lambda: client.network.info(),
        )
        transport_stats = client.transport_stats()

    context: dict[str, Any] = base_context(
        request, page="network", title="Network",
        settings=settings, transport_stats=transport_stats,
    )
    context.update({"network": network_result, "config_snapshot": config_snapshot(settings)})
    return get_templates(request).TemplateResponse(
        request=request, name="network.html", context=context,
    )
