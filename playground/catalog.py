from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from octaspace import OctaSpaceClient
from octaspace.response import APIResponse

from .state import PlaygroundSettings


@dataclass(frozen=True, slots=True)
class PlaygroundCall:
    id: str
    label: str
    description: str
    method: str
    path: str
    requires_auth: bool = False
    mutation: bool = False
    takes_payload: bool = False


CALLS: tuple[PlaygroundCall, ...] = (
    PlaygroundCall(
        id="network.info",
        label="octa_client.network.info",
        description="GET /network - public, no auth required",
        method="GET",
        path="/network",
    ),
    PlaygroundCall(
        id="accounts.profile",
        label="octa_client.accounts.profile",
        description="GET /accounts - requires API key",
        method="GET",
        path="/accounts",
        requires_auth=True,
    ),
    PlaygroundCall(
        id="accounts.balance",
        label="octa_client.accounts.balance",
        description="GET /accounts/balance - requires API key",
        method="GET",
        path="/accounts/balance",
        requires_auth=True,
    ),
    PlaygroundCall(
        id="apps.list",
        label="octa_client.apps.list",
        description="GET /apps - requires API key",
        method="GET",
        path="/apps",
        requires_auth=True,
    ),
    PlaygroundCall(
        id="idle_jobs.find",
        label="octa_client.idle_jobs.find(node_id:, job_id:)",
        description="GET /idle_jobs/:node_id/:job_id - requires API key",
        method="GET",
        path="/idle_jobs/:node_id/:job_id",
        requires_auth=True,
        takes_payload=True,
    ),
    PlaygroundCall(
        id="idle_jobs.logs",
        label="octa_client.idle_jobs.logs(node_id:, job_id:)",
        description="GET /idle_jobs/:node_id/:job_id/logs - requires API key",
        method="GET",
        path="/idle_jobs/:node_id/:job_id/logs",
        requires_auth=True,
        takes_payload=True,
    ),
    PlaygroundCall(
        id="nodes.list",
        label="octa_client.nodes.list",
        description="GET /nodes - requires API key",
        method="GET",
        path="/nodes",
        requires_auth=True,
    ),
    PlaygroundCall(
        id="sessions.list",
        label="octa_client.sessions.list",
        description="GET /sessions - requires API key",
        method="GET",
        path="/sessions",
        requires_auth=True,
    ),
    PlaygroundCall(
        id="sessions.list.recent",
        label="octa_client.sessions.list(recent: true)",
        description="GET /sessions?recent=true - requires API key",
        method="GET",
        path="/sessions?recent=true",
        requires_auth=True,
    ),
    PlaygroundCall(
        id="services.mr.list",
        label="octa_client.services.mr.list",
        description="GET /services/mr - requires API key",
        method="GET",
        path="/services/mr",
        requires_auth=True,
    ),
    PlaygroundCall(
        id="services.render.list",
        label="octa_client.services.render.list",
        description="GET /services/render - requires API key",
        method="GET",
        path="/services/render",
        requires_auth=True,
    ),
    PlaygroundCall(
        id="services.vpn.list",
        label="octa_client.services.vpn.list",
        description="GET /services/vpn - requires API key",
        method="GET",
        path="/services/vpn",
        requires_auth=True,
    ),
    PlaygroundCall(
        id="services.mr.create",
        label="octa_client.services.mr.create",
        description="POST /services/mr - requires API key",
        method="POST",
        path="/services/mr",
        requires_auth=True,
        mutation=True,
        takes_payload=True,
    ),
    PlaygroundCall(
        id="services.render.create",
        label="octa_client.services.render.create",
        description="POST /services/render - requires API key",
        method="POST",
        path="/services/render",
        requires_auth=True,
        mutation=True,
        takes_payload=True,
    ),
    PlaygroundCall(
        id="services.vpn.create",
        label="octa_client.services.vpn.create",
        description="POST /services/vpn - requires API key",
        method="POST",
        path="/services/vpn",
        requires_auth=True,
        mutation=True,
        takes_payload=True,
    ),
    PlaygroundCall(
        id="services.session.stop",
        label="octa_client.services.session(uuid).stop",
        description="POST /services/:uuid/stop - requires API key",
        method="POST",
        path="/services/:uuid/stop",
        requires_auth=True,
        mutation=True,
        takes_payload=True,
    ),
)

SMOKE_CALL_IDS: tuple[str, ...] = (
    "network.info",
    "accounts.profile",
    "accounts.balance",
    "apps.list",
    "nodes.list",
    "services.mr.list",
    "services.render.list",
    "services.vpn.list",
    "sessions.list",
    "sessions.list.recent",
)

CALLS_BY_ID = {call.id: call for call in CALLS}


def call_for(call_id: str) -> PlaygroundCall:
    return CALLS_BY_ID.get(call_id, CALLS[0])


def smoke_calls() -> list[PlaygroundCall]:
    return [call_for(call_id) for call_id in SMOKE_CALL_IDS]


def default_payload(call: PlaygroundCall, settings: PlaygroundSettings) -> str:
    payload = payload_for(call.id, settings)
    if payload is None:
        return ""
    return json.dumps(payload, indent=2, ensure_ascii=False)


def payload_for(call_id: str, settings: PlaygroundSettings) -> dict[str, Any] | None:
    node_id = _json_id(settings.sample_node_id)
    job_id = _json_id(settings.sample_job_id)
    uuid = settings.sample_session_uuid

    if call_id in {"idle_jobs.find", "idle_jobs.logs"}:
        return {"node_id": node_id, "job_id": job_id}
    if call_id == "services.mr.create":
        return {
            "node_id": node_id,
            "disk_size": 10,
            "image": "ubuntu:24.04",
            "app": "app-1",
        }
    if call_id == "services.render.create":
        return {"node_id": node_id, "disk_size": 100}
    if call_id == "services.vpn.create":
        return {"node_id": node_id, "subkind": "wg"}
    if call_id == "services.session.stop":
        return {"uuid": uuid, "score": 5}
    return None


def resolved_path(call: PlaygroundCall, payload: dict[str, Any] | None = None) -> str:
    data = payload or {}
    if call.id.startswith("idle_jobs."):
        node_id = data.get("node_id", ":node_id")
        job_id = data.get("job_id", ":job_id")
        suffix = "/logs" if call.id.endswith(".logs") else ""
        return f"/idle_jobs/{node_id}/{job_id}{suffix}"
    if call.id == "services.session.stop":
        uuid = data.get("uuid", ":uuid")
        return f"/services/{uuid}/stop"
    return call.path


def execute_call(
    client: OctaSpaceClient,
    call: PlaygroundCall,
    payload: dict[str, Any] | None = None,
) -> APIResponse:
    data = payload or {}

    if call.id == "network.info":
        return client.network.info()
    if call.id == "accounts.profile":
        return client.accounts.profile()
    if call.id == "accounts.balance":
        return client.accounts.balance()
    if call.id == "apps.list":
        return client.apps.list()
    if call.id == "idle_jobs.find":
        return client.idle_jobs.find(node_id=data["node_id"], job_id=data["job_id"])
    if call.id == "idle_jobs.logs":
        return client.idle_jobs.logs(node_id=data["node_id"], job_id=data["job_id"])
    if call.id == "nodes.list":
        return client.nodes.list()
    if call.id == "sessions.list":
        return client.sessions.list()
    if call.id == "sessions.list.recent":
        return client.sessions.list(recent=True)
    if call.id == "services.mr.list":
        return client.services.mr.list()
    if call.id == "services.render.list":
        return client.services.render.list()
    if call.id == "services.vpn.list":
        return client.services.vpn.list()
    if call.id == "services.mr.create":
        return client.services.mr.create(
            node_id=int(data["node_id"]),
            disk_size=int(data["disk_size"]),
            image=str(data["image"]),
            app=str(data.get("app", "")),
            envs=_string_dict(data.get("envs")),
            ports=_int_list(data.get("ports")),
            http_ports=_int_list(data.get("http_ports")),
            start_command=str(data.get("start_command", "")),
            entrypoint=str(data.get("entrypoint", "")),
        )
    if call.id == "services.render.create":
        return client.services.render.create(**data)
    if call.id == "services.vpn.create":
        return client.services.vpn.create(**data)
    if call.id == "services.session.stop":
        uuid = str(data["uuid"])
        return client.services.session(uuid).stop(
            **{key: value for key, value in data.items() if key != "uuid"}
        )
    raise ValueError(f"Unsupported playground call: {call.id}")


def _json_id(value: str) -> int | str:
    try:
        return int(value)
    except ValueError:
        return value


def _int_list(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    return [int(item) for item in value]


def _string_dict(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key): str(item) for key, item in value.items()}
