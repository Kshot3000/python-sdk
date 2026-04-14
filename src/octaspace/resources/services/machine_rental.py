from __future__ import annotations

from collections.abc import Sequence
from typing import Any, TypedDict

from ...response import APIResponse
from ..base import Resource


class _MachineRentalRequiredPayload(TypedDict):
    node_id: int
    disk_size: int
    image: str


class MachineRentalCreatePayload(_MachineRentalRequiredPayload, total=False):
    app: str
    envs: dict[str, str]
    ports: list[int]
    http_ports: list[int]
    start_command: str
    entrypoint: str


class MachineRentalResource(Resource):
    def list(self, **params: Any) -> APIResponse:
        return self.get("/services/mr", params=params or None)

    def create(
        self,
        *,
        node_id: int,
        disk_size: int,
        image: str,
        app: str = "",
        envs: dict[str, str] | None = None,
        ports: Sequence[int] | None = None,
        http_ports: Sequence[int] | None = None,
        start_command: str = "",
        entrypoint: str = "",
    ) -> APIResponse:
        payload: MachineRentalCreatePayload = {
            "node_id": node_id,
            "disk_size": disk_size,
            "image": image,
            "app": app,
            "envs": dict(envs or {}),
            "ports": list(ports or []),
            "http_ports": list(http_ports or []),
            "start_command": start_command,
            "entrypoint": entrypoint,
        }
        # The OctaSpace API expects MR creation as a single-item array with id=0.
        # This mirrors the Ruby gem and the live payload preset used by the JS SDK.
        item = {"id": 0, **payload}
        return self.post("/services/mr", body=[item])
