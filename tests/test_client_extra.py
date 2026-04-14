from __future__ import annotations

import pytest

from octaspace import OctaSpaceClient
from octaspace._transport.mock_transport import MockTransport
from octaspace.config import ClientConfig
from octaspace.errors import ConfigurationError


def test_client_config_property_and_shutdown(monkeypatch) -> None:
    transport = MockTransport()
    client = OctaSpaceClient(api_key="test-key", transport=transport)
    closed: list[str] = []
    monkeypatch.setattr(transport, "close", lambda: closed.append("closed"))

    assert client.config.api_key == "test-key"
    client.shutdown()

    assert closed == ["closed"]


def test_client_rejects_unknown_override() -> None:
    with pytest.raises(ConfigurationError):
        OctaSpaceClient(unknown_option=True)


def test_client_does_not_mutate_passed_config() -> None:
    config = ClientConfig(api_key="config-key")
    client = OctaSpaceClient(api_key="override-key", config=config, transport=MockTransport())

    assert config.api_key == "config-key"
    assert client.config.api_key == "override-key"
