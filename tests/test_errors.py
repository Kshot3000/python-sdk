from __future__ import annotations

import httpx
import pytest

from octaspace.errors import (
    APIPermissionError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
    from_response,
)
from octaspace.response import APIResponse


@pytest.mark.parametrize(
    ("status_code", "expected"),
    [
        (401, AuthenticationError),
        (403, APIPermissionError),
        (404, NotFoundError),
        (422, ValidationError),
        (429, RateLimitError),
        (500, ServerError),
    ],
)
def test_error_mapping(status_code: int, expected: type[Exception]) -> None:
    response = APIResponse.from_httpx(httpx.Response(status_code, json={"error": "boom"}))
    error = from_response(response)

    assert isinstance(error, expected)
    assert str(error) == "boom"


def test_rate_limit_error_includes_retry_after() -> None:
    response = APIResponse.from_httpx(
        httpx.Response(
            429,
            json={"error": "slow down"},
            headers={"Retry-After": "12"},
        )
    )
    error = from_response(response)

    assert isinstance(error, RateLimitError)
    assert error.retry_after == 12
