from __future__ import annotations

import pytest

from octaspace.config import ClientConfig


def test_config_user_agent_and_urls_fallback() -> None:
    custom = ClientConfig(user_agent="custom-agent")
    default = ClientConfig()

    assert custom.resolved_user_agent == "custom-agent"
    assert custom.urls == ["https://api.octa.space"]
    assert default.resolved_user_agent.startswith("octaspace-python/")


def test_config_with_overrides_invalid_key() -> None:
    with pytest.raises(ValueError):
        ClientConfig().with_overrides(nope=True)


def test_build_limits_without_keep_alive() -> None:
    limits = ClientConfig(keep_alive=False).build_limits()

    assert limits.max_keepalive_connections == 0
    assert limits.keepalive_expiry is None


def test_config_rejects_invalid_numeric_values() -> None:
    with pytest.raises(ValueError, match="max_retries must be >= 0"):
        ClientConfig(max_retries=-1)

    with pytest.raises(ValueError, match="max_connections must be > 0"):
        ClientConfig(max_connections=0)

    with pytest.raises(ValueError, match="pool_timeout must be > 0"):
        ClientConfig(pool_timeout=0.0)

    with pytest.raises(ValueError, match="retry_interval must be >= 0"):
        ClientConfig(retry_interval=-0.1)


def test_config_rejects_blank_base_url() -> None:
    with pytest.raises(ValueError, match="base_url must be a non-empty string"):
        ClientConfig(base_url="   ")


def test_config_rejects_empty_base_urls() -> None:
    with pytest.raises(ValueError, match="base_urls must contain at least one non-empty URL"):
        ClientConfig(base_urls=[])

    with pytest.raises(ValueError, match="base_urls must contain at least one non-empty URL"):
        ClientConfig(base_urls=["", "   "])
