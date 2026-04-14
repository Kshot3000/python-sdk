from __future__ import annotations

import time
from typing import Any

import httpx

from ..config import ClientConfig
from ..errors import APIConnectionError, APITimeoutError, raise_for_response
from ..hooks import HookDispatcher
from ..response import APIResponse
from .retry import compute_backoff, is_retryable_response
from .rotator import UrlRotator


class HttpxTransport:
    def __init__(self, config: ClientConfig, client: httpx.Client | None = None) -> None:
        self._config = config
        self._hooks = HookDispatcher(config.on_request, config.on_response, config.logger)
        self._rotator = UrlRotator(config.urls) if len(config.urls) > 1 else None
        self._client = client or httpx.Client(
            timeout=config.build_timeout(),
            limits=config.build_limits(),
            verify=config.ssl_verify,
            event_hooks=self._hooks.event_hooks(),
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        normalized_method = method.upper()
        normalized_path = path if path.startswith("/") else f"/{path}"
        response: APIResponse | None = None
        attempts = self._config.max_retries + 1
        for attempt in range(attempts):
            response = self._send_with_failover(
                normalized_method,
                normalized_path,
                params=params,
                body=body,
                headers=headers,
            )
            if (
                is_retryable_response(normalized_method, response.status_code)
                and attempt < attempts - 1
            ):
                delay = compute_backoff(
                    attempt=attempt,
                    retry_interval=self._config.retry_interval,
                    backoff_factor=self._config.backoff_factor,
                    retry_after=response.retry_after,
                )
                time.sleep(delay)
                continue
            break

        assert response is not None
        if response.is_error:
            raise_for_response(response)
        return response

    def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        return self.request("GET", path, params=params, headers=headers)

    def post(
        self,
        path: str,
        *,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        return self.request("POST", path, body=body, headers=headers)

    def put(
        self,
        path: str,
        *,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        return self.request("PUT", path, body=body, headers=headers)

    def patch(
        self,
        path: str,
        *,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        return self.request("PATCH", path, body=body, headers=headers)

    def delete(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        return self.request("DELETE", path, params=params, headers=headers)

    def close(self) -> None:
        self._client.close()

    def transport_stats(self) -> dict[str, Any]:
        stats: dict[str, Any] = {
            "mode": "persistent" if self._config.keep_alive else "standard",
            "limits": {
                "max_keepalive_connections": self._config.pool_size
                if self._config.keep_alive
                else 0,
                "max_connections": self._config.max_connections,
                "keepalive_expiry": (
                    self._config.idle_timeout if self._config.keep_alive else None
                ),
            },
        }
        if self._rotator is not None:
            stats["rotator"] = self._rotator.stats()
        else:
            stats["url"] = self._config.urls[0]
        return stats

    def _send_with_failover(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        ordered_urls = self._ordered_urls()
        last_error: Exception | None = None
        for base_url in ordered_urls:
            try:
                response = self._send_to_url(
                    base_url,
                    method,
                    path,
                    params=params,
                    body=body,
                    headers=headers,
                )
            except (APIConnectionError, APITimeoutError) as exc:
                last_error = exc
                if self._rotator is not None:
                    self._rotator.mark_failed(base_url)
                continue

            if self._rotator is not None:
                self._rotator.mark_success(base_url)
            return response

        if last_error is not None:
            raise last_error
        raise APIConnectionError("All API endpoints unavailable")

    def _send_to_url(
        self,
        base_url: str,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        request_headers = self._default_headers(headers)
        url = self._build_url(base_url, path)
        try:
            response = self._client.request(
                method,
                url,
                params=params,
                json=body,
                headers=request_headers,
            )
        except httpx.TimeoutException as exc:
            raise APITimeoutError(str(exc)) from exc
        except httpx.NetworkError as exc:
            raise APIConnectionError(str(exc)) from exc
        return self._hooks.response_wrapper(response)

    def _ordered_urls(self) -> list[str]:
        if self._rotator is None:
            return [self._config.urls[0]]
        primary = self._rotator.next_url()
        available = self._rotator.available_urls()
        remainder = [url for url in available if url != primary]
        return [primary, *remainder]

    def _default_headers(self, headers: dict[str, str] | None = None) -> dict[str, str]:
        merged = {
            "Accept": "application/json",
            "User-Agent": self._config.resolved_user_agent,
        }
        if self._config.api_key:
            merged["Authorization"] = self._config.api_key
        if not self._config.keep_alive:
            merged["Connection"] = "close"
        if headers:
            merged.update(headers)
        return merged

    @staticmethod
    def _build_url(base_url: str, path: str) -> str:
        return f"{base_url.rstrip('/')}/{path.lstrip('/')}"
