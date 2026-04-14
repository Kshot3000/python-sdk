from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Node:
    id: int
    ip: str
    state: str
    location: dict[str, Any]
    prices: dict[str, Any]
    system: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Node:
        return cls(
            id=int(data["id"]),
            ip=str(data["ip"]),
            state=str(data["state"]),
            location=dict(data.get("location", {})),
            prices=dict(data.get("prices", {})),
            system=dict(data.get("system", {})),
        )

    @property
    def online(self) -> bool:
        return self.state == "online"

    @property
    def offline(self) -> bool:
        return not self.online
