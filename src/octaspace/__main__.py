from __future__ import annotations

import json

from . import OctaSpaceClient
from .config import ClientConfig
from .response import APIResponse


def smoke() -> None:
    config = ClientConfig.from_env()
    with OctaSpaceClient(config=config) as client:
        payload: dict[str, object] = {
            "network": _response_payload(client.network.info()),
        }
        if config.api_key:
            payload["account_balance"] = _response_payload(client.accounts.balance())
        print(json.dumps(payload, indent=2, ensure_ascii=False))


def _response_payload(response: APIResponse) -> object:
    return response.data if response.data is not None else response.body.decode("utf-8")


if __name__ == "__main__":  # pragma: no cover
    smoke()
