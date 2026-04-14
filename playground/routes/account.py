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


@router.get("/playground/account", response_class=HTMLResponse)
def account(request: Request) -> HTMLResponse:
    state = get_state(request)
    settings = state.snapshot_settings()
    with build_client(settings) as client:
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
        request, page="account", title="Account",
        settings=settings, transport_stats=transport_stats,
    )
    context.update({"profile": profile, "balance": balance})
    return get_templates(request).TemplateResponse(
        request=request, name="account.html", context=context,
    )
