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


@router.get("/playground/nodes", response_class=HTMLResponse)
def nodes_index(request: Request, selected_id: str | None = None) -> HTMLResponse:
    state = get_state(request)
    settings = state.snapshot_settings()
    selected_node_id = selected_id or request.query_params.get("id")
    with build_client(settings) as client:
        nodes_result = capture_api_call(
            state,
            label="octa_client.nodes.list",
            method="GET",
            path="/nodes",
            fn=lambda: client.nodes.list(),
        )
        selected_node = None
        if selected_node_id:
            selected_node = capture_api_call(
                state,
                label=f"octa_client.nodes.find({selected_node_id})",
                method="GET",
                path=f"/nodes/{selected_node_id}",
                fn=lambda: client.nodes.find(selected_node_id),
            )
        transport_stats = client.transport_stats()

    context: dict[str, Any] = base_context(
        request, page="nodes", title="Nodes",
        settings=settings, transport_stats=transport_stats,
    )
    context.update({
        "nodes": nodes_result,
        "selected_node": selected_node,
        "selected_node_id": selected_node_id,
    })
    return get_templates(request).TemplateResponse(
        request=request, name="nodes_index.html", context=context,
    )


@router.get("/playground/nodes/{node_id}", response_class=HTMLResponse)
def nodes_show(request: Request, node_id: str) -> HTMLResponse:
    state = get_state(request)
    settings = state.snapshot_settings()
    with build_client(settings) as client:
        node = capture_api_call(
            state,
            label=f"octa_client.nodes.find({node_id})",
            method="GET",
            path=f"/nodes/{node_id}",
            fn=lambda: client.nodes.find(node_id),
        )
        transport_stats = client.transport_stats()

    context: dict[str, Any] = base_context(
        request, page="nodes", title="Nodes",
        settings=settings, transport_stats=transport_stats,
    )
    context.update({"node": node, "node_id": node_id})
    return get_templates(request).TemplateResponse(
        request=request, name="node_show.html", context=context,
    )
