from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from ..helpers import get_state, safe_return_path, validate_csrf

router = APIRouter()


@router.api_route("/playground/settings", methods=["POST", "PATCH"], include_in_schema=False)
async def settings_update(request: Request) -> RedirectResponse:
    state = get_state(request)
    form_data = await request.form()
    validate_csrf(request, str(form_data.get("csrf_token") or ""))
    form = {str(k): str(v) for k, v in form_data.items()}
    state.update_settings(form)
    return RedirectResponse(safe_return_path(form.get("return_to")), status_code=303)


@router.api_route("/playground/settings", methods=["DELETE"], include_in_schema=False)
async def settings_reset(request: Request) -> RedirectResponse:
    validate_csrf(request)
    state = get_state(request)
    state.reset_settings()
    return RedirectResponse(
        safe_return_path(request.query_params.get("return_to")),
        status_code=303,
    )


@router.api_route("/playground/request-log", methods=["POST", "DELETE"], include_in_schema=False)
async def request_log_clear(request: Request) -> RedirectResponse:
    submitted_token: str | None = None
    if request.method == "POST":
        form_data = await request.form()
        submitted_token = str(form_data.get("csrf_token") or "")
    validate_csrf(request, submitted_token)
    state = get_state(request)
    state.clear_request_log()
    return RedirectResponse(
        request.headers.get("referer") or "/playground/dashboard",
        status_code=303,
    )
