from __future__ import annotations

import httpx

from octaspace.response import APIResponse


def test_json_response_wrapper() -> None:
    response = httpx.Response(
        200,
        json={"id": 1, "name": "node"},
        headers={"X-Request-Id": "req-123"},
    )
    wrapped = APIResponse.from_httpx(response)

    assert wrapped.is_success is True
    assert wrapped.is_error is False
    assert wrapped.request_id == "req-123"
    assert wrapped.data == {"id": 1, "name": "node"}
    assert wrapped.body == b'{"id":1,"name":"node"}'


def test_binary_response_wrapper() -> None:
    response = httpx.Response(
        200,
        content=b"binary-data",
        headers={"Content-Type": "application/octet-stream"},
    )
    wrapped = APIResponse.from_httpx(response)

    assert wrapped.data is None
    assert wrapped.body == b"binary-data"


def test_retry_after_parsing() -> None:
    response = httpx.Response(429, json={}, headers={"Retry-After": "30"})
    wrapped = APIResponse.from_httpx(response)

    assert wrapped.retry_after == 30
