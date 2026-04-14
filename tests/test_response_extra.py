from __future__ import annotations

import httpx
import pytest

from octaspace.errors import NotFoundError
from octaspace.response import APIResponse


def test_response_invalid_json_and_invalid_retry_after() -> None:
    response = httpx.Response(
        200,
        content=b"{invalid",
        headers={"Content-Type": "application/json", "Retry-After": "invalid"},
    )
    wrapped = APIResponse.from_httpx(response)

    assert wrapped.data is None
    assert wrapped.retry_after is None


def test_response_raise_for_status_and_string_repr() -> None:
    ok = APIResponse.from_httpx(httpx.Response(204, content=b""))
    not_found = APIResponse.from_httpx(httpx.Response(404, json={"error": "missing"}))

    ok.raise_for_status()
    with pytest.raises(NotFoundError):
        not_found.raise_for_status()

    assert str(ok) == "<APIResponse [204]>"
