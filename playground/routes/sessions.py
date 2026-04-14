from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from octaspace.errors import OctaSpaceError

from ..helpers import (
    base_context,
    build_client,
    capture_api_call,
    get_state,
    get_templates,
    validate_csrf,
)
from ..views import response_data

router = APIRouter()


@router.get("/playground/sessions", response_class=HTMLResponse)
def sessions_index(
    request: Request,
    tab: str | None = None,
    stop_uuid: str | None = None,
    stop_notice: str | None = None,
    stop_error: str | None = None,
    request_id: str | None = None,
) -> HTMLResponse:
    state = get_state(request)
    settings = state.snapshot_settings()
    active_tab = tab if tab in {"current", "recent"} else "current"
    with build_client(settings) as client:
        current_sessions = capture_api_call(
            state,
            label="octa_client.sessions.list",
            method="GET",
            path="/sessions",
            fn=lambda: client.sessions.list(),
        )
        recent_sessions = capture_api_call(
            state,
            label="octa_client.sessions.list(recent: true)",
            method="GET",
            path="/sessions?recent=true",
            fn=lambda: client.sessions.list(recent=True),
        )
        transport_stats = client.transport_stats()

    stop_target = None
    current_data = response_data(current_sessions)
    if isinstance(current_data, list) and stop_uuid:
        stop_target = next(
            (s for s in current_data if isinstance(s, dict) and str(s.get("uuid")) == stop_uuid),
            None,
        )

    context: dict[str, Any] = base_context(
        request, page="sessions", title="Sessions",
        settings=settings, transport_stats=transport_stats,
    )
    context.update({
        "active_tab": active_tab,
        "current_sessions": current_sessions,
        "recent_sessions": recent_sessions,
        "stop_uuid": stop_uuid,
        "stop_notice": stop_notice,
        "stop_error": stop_error,
        "stop_request_id": request_id,
        "stop_target": stop_target,
    })
    return get_templates(request).TemplateResponse(
        request=request, name="sessions.html", context=context,
    )


@router.api_route("/playground/sessions/stop", methods=["POST"], include_in_schema=False)
async def sessions_stop(request: Request) -> RedirectResponse:
    state = get_state(request)
    settings = state.snapshot_settings()
    form_data = await request.form()
    validate_csrf(request, str(form_data.get("csrf_token") or ""))
    active_tab = str(form_data.get("tab") or "current")
    uuid = str(form_data.get("uuid") or "").strip()

    if not uuid:
        params = urlencode({"tab": active_tab, "stop_error": "Session UUID is required"})
        return RedirectResponse(f"/playground/sessions?{params}", status_code=303)

    stop_params: dict[str, Any] = {}
    score_str = str(form_data.get("score") or "").strip()
    if score_str:
        try:
            stop_params["score"] = int(score_str)
        except ValueError:
            params = urlencode({
                "tab": active_tab,
                "stop_error": f"Score must be an integer, got: {score_str!r}",
            })
            return RedirectResponse(f"/playground/sessions?{params}", status_code=303)

    with build_client(settings) as client:
        response = capture_api_call(
            state,
            label=f"octa_client.services.session({uuid}).stop",
            method="POST",
            path=f"/services/{uuid}/stop",
            fn=lambda: client.services.session(uuid).stop(**stop_params),
        )

    if isinstance(response, OctaSpaceError):
        redirect_params: dict[str, str] = {"tab": active_tab, "stop_error": str(response)}
    else:
        redirect_params = {
            "tab": active_tab, "stop_notice": f"Session {uuid} stop request submitted.",
        }
        if response.request_id:
            redirect_params["request_id"] = response.request_id
    return RedirectResponse(f"/playground/sessions?{urlencode(redirect_params)}", status_code=303)
