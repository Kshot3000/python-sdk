from __future__ import annotations

import httpx
import pytest

from octaspace._transport.mock_transport import MockTransport
from octaspace.errors import ConfigurationError, NotFoundError
from octaspace.response import APIResponse


def _response(status_code: int, payload) -> APIResponse:
    if isinstance(payload, bytes):
        return APIResponse.from_httpx(
            httpx.Response(
                status_code,
                content=payload,
                headers={"Content-Type": "application/octet-stream"},
            )
        )
    return APIResponse.from_httpx(httpx.Response(status_code, json=payload))


def test_mock_transport_all_verbs_and_stats() -> None:
    transport = MockTransport()
    transport.add_response("GET", "/nodes", _response(200, []))
    transport.add_response("POST", "/accounts", _response(201, {"ok": True}))
    transport.add_response("PUT", "/nodes/1", _response(200, {"updated": True}))
    transport.add_response("PATCH", "/nodes/1/prices", _response(200, {"patched": True}))
    transport.add_response("DELETE", "/idle_jobs/1", _response(200, {"deleted": True}))

    assert transport.get("/nodes").data == []
    assert transport.post("/accounts").data["ok"] is True
    assert transport.put("/nodes/1").data["updated"] is True
    assert transport.patch("/nodes/1/prices").data["patched"] is True
    assert transport.delete("/idle_jobs/1").data["deleted"] is True
    assert transport.transport_stats() == {"mode": "mock", "responses": 5}
    assert transport.close() is None


def test_mock_transport_raises_sdk_error_for_error_response() -> None:
    transport = MockTransport()
    transport.add_response("GET", "/missing", _response(404, {"error": "missing"}))

    with pytest.raises(NotFoundError):
        transport.get("/missing")


def test_mock_transport_raises_configuration_error_for_missing_response() -> None:
    transport = MockTransport()

    with pytest.raises(ConfigurationError, match="No mock response registered for GET /unknown"):
        transport.get("/unknown")
