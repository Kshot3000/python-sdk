from __future__ import annotations

import copy
import json
import time
from pathlib import Path
from typing import Any

import httpx

from octaspace.errors import APIConnectionError, APITimeoutError, raise_for_response
from octaspace.response import APIResponse

from .state import PlaygroundSettings

# Keep playground fixture data local to the playground so the dev app does not
# depend on the test suite's directory layout.
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
ERROR_SCENARIOS = {"401", "403", "404", "429", "500"}


def _load_fixture(name: str) -> Any:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def _coerce_identifier(value: str) -> int | str:
    try:
        return int(value)
    except ValueError:
        return value


def _normalize_param_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _normalize_params(params: dict[str, Any] | None) -> tuple[tuple[str, str], ...]:
    if not params:
        return ()
    return tuple(sorted((str(key), _normalize_param_value(value)) for key, value in params.items()))


def _json_response(
    status_code: int,
    payload: Any,
    *,
    headers: dict[str, str] | None = None,
) -> APIResponse:
    response_headers = {
        "Content-Type": "application/json",
        "X-Request-Id": f"mock-{status_code}",
    }
    if headers:
        response_headers.update(headers)
    return APIResponse.from_httpx(
        httpx.Response(
            status_code,
            json=payload,
            headers=response_headers,
        )
    )


def _text_response(
    status_code: int,
    payload: str,
    *,
    content_type: str = "text/plain",
) -> APIResponse:
    return APIResponse.from_httpx(
        httpx.Response(
            status_code,
            content=payload.encode("utf-8"),
            headers={
                "Content-Type": content_type,
                "X-Request-Id": f"mock-{status_code}",
            },
        )
    )


class PlaygroundMockTransport:
    def __init__(self, settings: PlaygroundSettings) -> None:
        self._settings = settings
        self._responses: dict[tuple[str, str, tuple[tuple[str, str], ...]], APIResponse] = {}

    def add_response(
        self,
        method: str,
        path: str,
        response: APIResponse,
        *,
        params: dict[str, Any] | None = None,
    ) -> None:
        key = (method.upper(), self._normalize_path(path), _normalize_params(params))
        self._responses[key] = response

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        del body, headers
        scenario = self._settings.mock_scenario
        if scenario == "timeout":
            raise APITimeoutError("Mocked timeout after configured read timeout")
        if scenario == "network-error":
            raise APIConnectionError("Mocked network failure")
        if scenario == "slow":
            time.sleep(3.0)
        if scenario in ERROR_SCENARIOS:
            response_headers = {"Retry-After": "60"} if scenario == "429" else None
            error_response = _json_response(
                int(scenario),
                {"error": f"Mocked {scenario}", "scenario": scenario},
                headers=response_headers,
            )
            raise_for_response(error_response)

        normalized_path = self._normalize_path(path)
        key = (method.upper(), normalized_path, _normalize_params(params))
        response: APIResponse | None = self._responses.get(key)
        if response is None:
            response = self._responses.get((method.upper(), normalized_path, ()))
        if response is None:
            response = _json_response(
                404,
                {
                    "error": f"No mock response for {method.upper()} {normalized_path}",
                    "scenario": "fixtures",
                },
            )
            raise_for_response(response)
        return response

    def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        return self.request("GET", path, params=params, headers=headers)

    def post(
        self,
        path: str,
        *,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        return self.request("POST", path, body=body, headers=headers)

    def put(
        self,
        path: str,
        *,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        return self.request("PUT", path, body=body, headers=headers)

    def patch(
        self,
        path: str,
        *,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        return self.request("PATCH", path, body=body, headers=headers)

    def delete(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        return self.request("DELETE", path, params=params, headers=headers)

    def close(self) -> None:
        return None

    def transport_stats(self) -> dict[str, Any]:
        return {
            "mode": "mock",
            "scenario": self._settings.mock_scenario,
            "label": self._settings.selected_scenario.label,
        }

    @staticmethod
    def _normalize_path(path: str) -> str:
        return path if path.startswith("/") else f"/{path}"


def build_mock_transport(settings: PlaygroundSettings) -> PlaygroundMockTransport:
    transport = PlaygroundMockTransport(settings)

    node_id = settings.sample_node_id
    job_id = settings.sample_job_id
    session_uuid = settings.sample_session_uuid
    coerced_node_id = _coerce_identifier(node_id)
    coerced_job_id = _coerce_identifier(job_id)

    profile = _load_fixture("accounts/show.json")
    balance = _load_fixture("accounts/balance.json")
    apps = _load_fixture("apps/index.json")
    network = _load_fixture("network/info.json")
    nodes = _load_fixture("nodes/index.json")
    node_show = _load_fixture("nodes/show.json")
    sessions = _load_fixture("sessions/index.json")
    recent_sessions = copy.deepcopy(sessions)
    idle_job = _load_fixture("idle_jobs/show.json")
    idle_logs = _load_fixture("idle_jobs/logs.json")
    mr_sessions = _load_fixture("services/mr/index.json")
    vpn_sessions = _load_fixture("services/vpn/index.json")
    service_info = _load_fixture("services/session/info.json")
    service_logs = _load_fixture("services/session/logs.json")

    nodes[0]["id"] = coerced_node_id
    node_show["id"] = coerced_node_id
    sessions[0]["uuid"] = session_uuid
    recent_sessions[0]["uuid"] = f"recent-{session_uuid}"
    recent_sessions[0]["termination_reason"] = 0
    recent_sessions[0]["duration"] = 3600
    idle_job["node_id"] = coerced_node_id
    idle_job["job_id"] = coerced_job_id
    service_info["uuid"] = session_uuid
    mr_sessions[0]["uuid"] = f"mr-{session_uuid}"
    vpn_sessions[0]["uuid"] = f"vpn-{session_uuid}"

    transport.add_response("GET", "/network", _json_response(200, network))
    transport.add_response("GET", "/accounts", _json_response(200, profile))
    transport.add_response("GET", "/accounts/balance", _json_response(200, balance))
    transport.add_response(
        "POST",
        "/accounts",
        _json_response(201, {"wallet": "wallet-mock-001", "status": "generated"}),
    )
    transport.add_response("GET", "/apps", _json_response(200, apps))
    transport.add_response("GET", "/nodes", _json_response(200, nodes))
    transport.add_response("GET", f"/nodes/{node_id}", _json_response(200, node_show))
    transport.add_response(
        "GET",
        f"/nodes/{node_id}/ident",
        _text_response(200, f"ssh-ed25519 AAAA-playground-{node_id} octaspace@mock"),
    )
    transport.add_response(
        "GET",
        f"/nodes/{node_id}/logs",
        _text_response(200, "node log line 1\nnode log line 2\nnode log line 3"),
    )
    transport.add_response(
        "PATCH",
        f"/nodes/{node_id}/prices",
        _json_response(200, {"status": "updated", "node_id": coerced_node_id}),
    )
    transport.add_response(
        "GET",
        f"/nodes/{node_id}/reboot",
        _json_response(200, {"status": "rebooting", "node_id": coerced_node_id}),
    )
    transport.add_response("GET", "/sessions", _json_response(200, sessions))
    transport.add_response(
        "GET",
        "/sessions",
        _json_response(200, recent_sessions),
        params={"recent": True},
    )
    transport.add_response(
        "GET",
        f"/idle_jobs/{node_id}/{job_id}",
        _json_response(200, idle_job),
    )
    transport.add_response(
        "GET",
        f"/idle_jobs/{node_id}/{job_id}/logs",
        _json_response(200, idle_logs),
    )
    transport.add_response("GET", "/services/mr", _json_response(200, mr_sessions))
    transport.add_response(
        "POST",
        "/services/mr",
        _json_response(201, {"uuid": f"new-mr-{session_uuid}", "status": "starting"}),
    )
    transport.add_response("GET", "/services/render", _json_response(200, []))
    transport.add_response(
        "POST",
        "/services/render",
        _json_response(201, {"uuid": f"new-render-{session_uuid}", "status": "queued"}),
    )
    transport.add_response("GET", "/services/vpn", _json_response(200, vpn_sessions))
    transport.add_response(
        "POST",
        "/services/vpn",
        _json_response(201, {"uuid": f"new-vpn-{session_uuid}", "status": "starting"}),
    )
    transport.add_response(
        "GET",
        f"/services/{session_uuid}/info",
        _json_response(200, service_info),
    )
    transport.add_response(
        "GET",
        f"/services/{session_uuid}/logs",
        _json_response(200, service_logs),
    )
    transport.add_response(
        "POST",
        f"/services/{session_uuid}/stop",
        _json_response(200, {"uuid": session_uuid, "status": "stopped"}),
    )

    return transport
