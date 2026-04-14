from __future__ import annotations

from typing import Any

from ..._transport.base import BaseTransport
from ...response import APIResponse
from ..base import Resource


class SessionProxy(Resource):
    def __init__(self, transport: BaseTransport, uuid: str) -> None:
        super().__init__(transport)
        self._uuid = self.encode(uuid)

    def info(self) -> APIResponse:
        return self.get(f"/services/{self._uuid}/info")

    def logs(self) -> APIResponse:
        return self.get(f"/services/{self._uuid}/logs")

    def stop(self, **params: Any) -> APIResponse:
        return self.post(
            f"/services/{self._uuid}/stop",
            body=params or None,
        )
