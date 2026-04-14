from __future__ import annotations

from typing import Any

from ..response import APIResponse
from .base import Resource


class NodesResource(Resource):
    def list(self, **params: Any) -> APIResponse:
        return self.get("/nodes", params=params or None)

    def find(self, node_id: int | str) -> APIResponse:
        return self.get(f"/nodes/{self.encode(node_id)}")

    def download_ident(self, node_id: int | str) -> APIResponse:
        return self.get(f"/nodes/{self.encode(node_id)}/ident")

    def download_logs(self, node_id: int | str) -> APIResponse:
        return self.get(f"/nodes/{self.encode(node_id)}/logs")

    def update_prices(self, node_id: int | str, **prices: Any) -> APIResponse:
        return self.patch(f"/nodes/{self.encode(node_id)}/prices", body=prices)

    def reboot(self, node_id: int | str) -> APIResponse:
        return self.get(f"/nodes/{self.encode(node_id)}/reboot")
