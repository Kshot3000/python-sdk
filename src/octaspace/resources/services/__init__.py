from __future__ import annotations

from ..._transport.base import BaseTransport
from ..base import Resource
from .machine_rental import MachineRentalResource
from .render import RenderResource
from .session_proxy import SessionProxy
from .vpn import VpnResource


class ServicesResource(Resource):
    def __init__(self, transport: BaseTransport) -> None:
        super().__init__(transport)
        self.mr = MachineRentalResource(transport)
        self.vpn = VpnResource(transport)
        self.render = RenderResource(transport)

    def session(self, uuid: str) -> SessionProxy:
        return SessionProxy(self._transport, uuid)


__all__ = [
    "MachineRentalResource",
    "RenderResource",
    "ServicesResource",
    "SessionProxy",
    "VpnResource",
]
