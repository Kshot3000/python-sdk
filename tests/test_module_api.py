from __future__ import annotations

import octaspace


def test_configuration_and_configure_close_existing_shared_client(monkeypatch) -> None:
    assert octaspace.configuration().api_key is None

    shared = octaspace.client()
    closed: list[str] = []
    monkeypatch.setattr(shared, "close", lambda: closed.append("closed"))

    config = octaspace.configure(api_key="new-key")

    assert config.api_key == "new-key"
    assert octaspace.configuration().api_key == "new-key"
    assert closed == ["closed"]


def test_reset_configuration_closes_shared_client(monkeypatch) -> None:
    shared = octaspace.client()
    closed: list[str] = []
    monkeypatch.setattr(shared, "close", lambda: closed.append("reset"))

    config = octaspace.reset_configuration()

    assert closed == ["reset"]
    assert config.api_key is None
    assert octaspace.configuration().api_key is None


def test_client_with_overrides_does_not_reuse_shared_instance() -> None:
    octaspace.configure(api_key="shared-key")

    shared = octaspace.client()
    one_off = octaspace.client(base_url="https://alt.octa.space")

    assert one_off is not shared
    assert one_off.config.base_url == "https://alt.octa.space"
    assert octaspace.configuration().base_url == "https://api.octa.space"


def test_shutdown_shared_client_closes_existing_instance(monkeypatch) -> None:
    shared = octaspace.client()
    closed: list[str] = []
    monkeypatch.setattr(shared, "close", lambda: closed.append("shutdown"))

    octaspace.shutdown_shared_client()

    assert closed == ["shutdown"]
