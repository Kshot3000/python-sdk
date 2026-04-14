from __future__ import annotations

import json

import httpx

from octaspace.__main__ import smoke
from octaspace.config import ClientConfig
from octaspace.response import APIResponse


class _FakeNetwork:
    def __init__(self, response) -> None:
        self._response = response

    def info(self):
        return self._response


class _FakeAccounts:
    def __init__(self, response) -> None:
        self._response = response

    def balance(self):
        return self._response


class _FakeClient:
    def __init__(self, *, config, network_response, balance_response=None) -> None:
        self.config = config
        self.network = _FakeNetwork(network_response)
        self.accounts = _FakeAccounts(balance_response or network_response)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        del exc_type, exc, tb


def test_smoke_prints_json_payload(monkeypatch, capsys) -> None:
    config = ClientConfig()
    response = APIResponse.from_httpx(httpx.Response(200, json={"ok": True}))

    monkeypatch.setattr("octaspace.__main__.ClientConfig.from_env", lambda: config)
    monkeypatch.setattr(
        "octaspace.__main__.OctaSpaceClient",
        lambda config: _FakeClient(config=config, network_response=response),
    )

    smoke()

    assert json.loads(capsys.readouterr().out) == {"network": {"ok": True}}


def test_smoke_prints_text_when_response_is_not_json(monkeypatch, capsys) -> None:
    response = APIResponse.from_httpx(
        httpx.Response(200, content=b"plain-text", headers={"Content-Type": "text/plain"})
    )
    monkeypatch.setattr("octaspace.__main__.ClientConfig.from_env", lambda: ClientConfig())
    monkeypatch.setattr(
        "octaspace.__main__.OctaSpaceClient",
        lambda config: _FakeClient(config=config, network_response=response),
    )

    smoke()

    assert json.loads(capsys.readouterr().out) == {"network": "plain-text"}


def test_smoke_includes_account_balance_when_api_key_is_present(monkeypatch, capsys) -> None:
    config = ClientConfig(api_key="env-key")
    network_response = APIResponse.from_httpx(httpx.Response(200, json={"ok": True}))
    balance_response = APIResponse.from_httpx(httpx.Response(200, json={"balance": 42}))

    monkeypatch.setattr("octaspace.__main__.ClientConfig.from_env", lambda: config)
    monkeypatch.setattr(
        "octaspace.__main__.OctaSpaceClient",
        lambda config: _FakeClient(
            config=config,
            network_response=network_response,
            balance_response=balance_response,
        ),
    )

    smoke()

    assert json.loads(capsys.readouterr().out) == {
        "network": {"ok": True},
        "account_balance": {"balance": 42},
    }
