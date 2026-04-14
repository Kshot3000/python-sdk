from __future__ import annotations

from ..response import APIResponse
from .base import Resource


class NetworkResource(Resource):
    def info(self) -> APIResponse:
        return self.get("/network")
