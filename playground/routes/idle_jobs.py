from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from ..catalog import payload_for
from ..helpers import (
    base_context,
    build_client,
    capture_api_call,
    get_state,
    get_templates,
)

router = APIRouter()


@router.get("/playground/idle-jobs", response_class=HTMLResponse)
def idle_jobs_show(
    request: Request,
    node_id: str | None = None,
    job_id: str | None = None,
) -> HTMLResponse:
    state = get_state(request)
    settings = state.snapshot_settings()
    defaults = payload_for("idle_jobs.find", settings) or {}
    resolved_node_id = node_id or str(defaults.get("node_id", settings.sample_node_id))
    resolved_job_id = job_id or str(defaults.get("job_id", settings.sample_job_id))

    job = None
    logs = None
    with build_client(settings) as client:
        if node_id is not None and job_id is not None:
            job = capture_api_call(
                state,
                label=(
                    f"octa_client.idle_jobs.find("
                    f"node_id: {resolved_node_id}, job_id: {resolved_job_id})"
                ),
                method="GET",
                path=f"/idle_jobs/{resolved_node_id}/{resolved_job_id}",
                fn=lambda: client.idle_jobs.find(
                    node_id=resolved_node_id, job_id=resolved_job_id,
                ),
            )
            logs = capture_api_call(
                state,
                label=(
                    f"octa_client.idle_jobs.logs("
                    f"node_id: {resolved_node_id}, job_id: {resolved_job_id})"
                ),
                method="GET",
                path=f"/idle_jobs/{resolved_node_id}/{resolved_job_id}/logs",
                fn=lambda: client.idle_jobs.logs(
                    node_id=resolved_node_id, job_id=resolved_job_id,
                ),
            )
        transport_stats = client.transport_stats()

    context: dict[str, Any] = base_context(
        request, page="idle_jobs", title="Idle Jobs",
        settings=settings, transport_stats=transport_stats,
    )
    context.update({
        "node_id": resolved_node_id,
        "job_id": resolved_job_id,
        "job": job,
        "logs": logs,
        "requested": node_id is not None and job_id is not None,
    })
    return get_templates(request).TemplateResponse(
        request=request, name="idle_jobs.html", context=context,
    )
