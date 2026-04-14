from __future__ import annotations

import httpx
import pytest

from octaspace._transport.httpx_transport import HttpxTransport
from octaspace.config import ClientConfig
from octaspace.errors import APIConnectionError, APITimeoutError, RateLimitError


def test_transport_sends_auth_header(respx_mock) -> None:
    route = respx_mock.get("https://api.octa.space/nodes").respond(json=[])
    transport = HttpxTransport(ClientConfig(api_key="test_key", max_retries=0))

    response = transport.get("/nodes")

    assert response.is_success is True
    assert route.calls.last.request.headers["Authorization"] == "test_key"
    transport.close()


def test_transport_retries_on_server_error(monkeypatch, respx_mock) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("octaspace._transport.httpx_transport.time.sleep", sleeps.append)
    route = respx_mock.get("https://api.octa.space/nodes")
    route.side_effect = [
        httpx.Response(500, json={"error": "boom"}),
        httpx.Response(200, json=[]),
    ]
    transport = HttpxTransport(ClientConfig(max_retries=1))

    response = transport.get("/nodes")

    assert response.is_success is True
    assert len(sleeps) == 1
    assert len(route.calls) == 2
    transport.close()


def test_transport_honors_retry_after(monkeypatch, respx_mock) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("octaspace._transport.httpx_transport.time.sleep", sleeps.append)
    route = respx_mock.get("https://api.octa.space/nodes")
    route.side_effect = [
        httpx.Response(429, json={"error": "slow down"}, headers={"Retry-After": "7"}),
        httpx.Response(429, json={"error": "slow down"}, headers={"Retry-After": "7"}),
    ]
    transport = HttpxTransport(ClientConfig(max_retries=1))

    with pytest.raises(RateLimitError):
        transport.get("/nodes")

    assert sleeps == [7.0]
    assert len(route.calls) == 2
    transport.close()


def test_transport_fails_over_on_connection_error(respx_mock) -> None:
    respx_mock.get("https://bad.octa.space/nodes").mock(side_effect=httpx.ConnectError("boom"))
    respx_mock.get("https://api.octa.space/nodes").respond(json=[])
    transport = HttpxTransport(
        ClientConfig(base_urls=["https://bad.octa.space", "https://api.octa.space"], max_retries=0)
    )

    response = transport.get("/nodes")

    assert response.is_success is True
    assert transport.transport_stats()["rotator"]["total"] == 2
    transport.close()


def test_transport_raises_when_all_urls_fail(respx_mock) -> None:
    respx_mock.get("https://bad1.octa.space/nodes").mock(side_effect=httpx.ConnectError("boom"))
    respx_mock.get("https://bad2.octa.space/nodes").mock(side_effect=httpx.ReadTimeout("slow"))
    transport = HttpxTransport(
        ClientConfig(
            base_urls=["https://bad1.octa.space", "https://bad2.octa.space"], max_retries=0
        )
    )

    with pytest.raises((APIConnectionError, APITimeoutError)):
        transport.get("/nodes")

    transport.close()
