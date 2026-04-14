from __future__ import annotations

from typing import Any, Protocol

from ..response import APIResponse


class BaseTransport(Protocol):
    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse: ...

    def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse: ...

    def post(
        self,
        path: str,
        *,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse: ...

    def put(
        self,
        path: str,
        *,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse: ...

    def patch(
        self,
        path: str,
        *,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse: ...

    def delete(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse: ...

    def close(self) -> None: ...

    def transport_stats(self) -> dict[str, Any]: ...
