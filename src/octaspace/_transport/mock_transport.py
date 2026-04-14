from __future__ import annotations

from typing import Any

from ..errors import ConfigurationError, raise_for_response
from ..response import APIResponse


class MockTransport:
    def __init__(self) -> None:
        self._responses: dict[tuple[str, str], APIResponse] = {}

    def add_response(self, method: str, path: str, response: APIResponse) -> None:
        self._responses[(method.upper(), path)] = response

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        del params, body, headers
        try:
            response = self._responses[(method.upper(), path)]
        except KeyError as exc:
            raise ConfigurationError(
                f"No mock response registered for {method.upper()} {path}"
            ) from exc
        if response.is_error:
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
        return {"mode": "mock", "responses": len(self._responses)}
