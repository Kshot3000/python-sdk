from __future__ import annotations

import json

import httpx

from octaspace import OctaSpaceClient
from octaspace._transport.mock_transport import MockTransport
from octaspace.response import APIResponse


def make_response(status_code: int, payload: object) -> APIResponse:
    return APIResponse.from_httpx(httpx.Response(status_code, json=payload))


def dump(label: str, payload: object) -> None:
    print(f"{label}: {json.dumps(payload, ensure_ascii=False)}")


def main() -> None:
    transport = MockTransport()
    transport.add_response("GET", "/network", make_response(200, {"power": 1234, "nodes": 2}))
    transport.add_response(
        "GET",
        "/accounts",
        make_response(200, {"account_uuid": "acc-1", "email": "user@example.com"}),
    )
    transport.add_response(
        "GET",
        "/accounts/balance",
        make_response(200, {"balance": 123.45, "currency": "OCTA"}),
    )
    transport.add_response(
        "GET",
        "/nodes",
        make_response(200, [{"id": 1, "state": "online"}, {"id": 2, "state": "offline"}]),
    )
    transport.add_response(
        "GET",
        "/services/sess-abc-123/info",
        make_response(200, {"uuid": "sess-abc-123", "status": "running"}),
    )
    transport.add_response(
        "POST",
        "/services/sess-abc-123/stop",
        make_response(200, {"uuid": "sess-abc-123", "status": "stopped"}),
    )

    with OctaSpaceClient(transport=transport) as client:
        dump("transport_stats", client.transport_stats())
        dump("network", client.network.info().data)
        dump("profile", client.accounts.profile().data)
        dump("balance", client.accounts.balance().data)
        dump("nodes", client.nodes.list().data)
        dump("session_info", client.services.session("sess-abc-123").info().data)
        dump("session_stop", client.services.session("sess-abc-123").stop(score=5).data)


if __name__ == "__main__":
    main()
