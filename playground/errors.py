from __future__ import annotations

from typing import Any

from octaspace.errors import APIError, OctaSpaceError


class PayloadError(Exception):
    """Raised when request payload JSON is invalid or missing required keys."""


def status_for_error(error: OctaSpaceError) -> str:
    if isinstance(error, APIError):
        return str(error.status_code)
    return "ERR"


def error_payload(error: Exception) -> dict[str, Any]:
    if isinstance(error, PayloadError):
        return {"class": type(error).__name__, "message": str(error)}
    if isinstance(error, APIError):
        payload: dict[str, Any] = {
            "class": type(error).__name__,
            "message": str(error),
            "status": error.status_code,
            "request_id": error.request_id,
        }
        if error.response.data is not None:
            payload["response"] = error.response.data
        retry_after = getattr(error, "retry_after", None)
        if retry_after is not None:
            payload["retry_after"] = retry_after
        return payload
    return {"class": type(error).__name__, "message": str(error)}
