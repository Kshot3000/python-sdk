from __future__ import annotations

from typing import Any

from ..response import APIResponse
from .base import Resource


class AppsResource(Resource):
    def list(self, **params: Any) -> APIResponse:
        return self.get("/apps", params=params or None)
