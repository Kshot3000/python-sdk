from __future__ import annotations

from typing import Any

from .__about__ import __version__
from .client import OctaSpaceClient
from .config import ClientConfig
from .errors import (
    APIConnectionError,
    APIError,
    APIPermissionError,
    APITimeoutError,
    AuthenticationError,
    BadGatewayError,
    ConfigurationError,
    GatewayTimeoutError,
    NetworkError,
    NotFoundError,
    OctaSpaceError,
    RateLimitError,
    ServerError,
    ServiceUnavailableError,
    ValidationError,
)

_configuration = ClientConfig()
_shared_client: OctaSpaceClient | None = None


def configuration() -> ClientConfig:
    return _configuration


def configure(**overrides: Any) -> ClientConfig:
    global _configuration, _shared_client
    _configuration = _configuration.with_overrides(**overrides)
    if _shared_client is not None:
        _shared_client.close()
        _shared_client = None
    return _configuration


def reset_configuration() -> ClientConfig:
    global _configuration, _shared_client
    if _shared_client is not None:
        _shared_client.close()
    _shared_client = None
    _configuration = ClientConfig()
    return _configuration


def client(api_key: str | None = None, **overrides: Any) -> OctaSpaceClient:
    global _shared_client
    if api_key is None and not overrides:
        if _shared_client is None:
            _shared_client = OctaSpaceClient(config=_configuration)
        return _shared_client
    local_config = _configuration.with_overrides(**overrides) if overrides else _configuration
    return OctaSpaceClient(api_key=api_key, config=local_config)


def shutdown_shared_client() -> None:
    global _shared_client
    if _shared_client is not None:
        _shared_client.close()
        _shared_client = None


__all__ = [
    "APIConnectionError",
    "APIError",
    "APIPermissionError",
    "APITimeoutError",
    "AuthenticationError",
    "BadGatewayError",
    "ClientConfig",
    "ConfigurationError",
    "GatewayTimeoutError",
    "NetworkError",
    "NotFoundError",
    "OctaSpaceClient",
    "OctaSpaceError",
    "RateLimitError",
    "ServerError",
    "ServiceUnavailableError",
    "ValidationError",
    "__version__",
    "client",
    "configuration",
    "configure",
    "reset_configuration",
    "shutdown_shared_client",
]
