from __future__ import annotations

import httpx

from octaspace._transport.mock_transport import MockTransport
from octaspace.resources.base import Resource
from octaspace.response import APIResponse


def _json_response(payload: object) -> APIResponse:
    return APIResponse.from_httpx(httpx.Response(200, json=payload))


def test_resource_delegates_http_verbs_and_encode() -> None:
    transport = MockTransport()
    resource = Resource(transport)
    transport.add_response("PUT", "/put", _json_response({"put": True}))
    transport.add_response("DELETE", "/delete", _json_response({"delete": True}))

    assert resource.put("/put").data["put"] is True
    assert resource.delete("/delete").data["delete"] is True
    assert resource.encode("uuid with spaces/and/slashes") == "uuid%20with%20spaces%2Fand%2Fslashes"
