from __future__ import annotations

import httpx

from octaspace.config import ClientConfig


def test_urls_prefers_base_urls() -> None:
    config = ClientConfig(
        base_url="https://api.octa.space",
        base_urls=["https://a.octa.space", "https://b.octa.space"],
    )

    assert config.urls == ["https://a.octa.space", "https://b.octa.space"]


def test_build_timeout_and_limits() -> None:
    config = ClientConfig(keep_alive=True, pool_size=7, max_connections=14, idle_timeout=42.0)
    timeout = config.build_timeout()
    limits = config.build_limits()

    assert isinstance(timeout, httpx.Timeout)
    assert isinstance(limits, httpx.Limits)
    assert limits.max_keepalive_connections == 7
    assert limits.max_connections == 14
    assert limits.keepalive_expiry == 42.0


def test_from_env(monkeypatch) -> None:
    monkeypatch.setenv("OCTA_API_KEY", "env-key")
    monkeypatch.setenv("OCTA_BASE_URLS", "https://a.octa.space,https://b.octa.space")
    monkeypatch.setenv("OCTA_KEEP_ALIVE", "true")
    monkeypatch.setenv("OCTA_POOL_SIZE", "9")

    config = ClientConfig.from_env()

    assert config.api_key == "env-key"
    assert config.base_urls == ["https://a.octa.space", "https://b.octa.space"]
    assert config.keep_alive is True
    assert config.pool_size == 9
