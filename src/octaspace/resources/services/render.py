from __future__ import annotations

from typing import Any

from ...response import APIResponse
from ..base import Resource


class RenderResource(Resource):
    def list(self, **params: Any) -> APIResponse:
        return self.get("/services/render", params=params or None)

    def create(self, **attrs: Any) -> APIResponse:
        return self.post("/services/render", body=attrs)
