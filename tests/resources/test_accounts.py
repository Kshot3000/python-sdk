from __future__ import annotations

import pytest

from conftest import load_fixture
from octaspace import AuthenticationError, RateLimitError, ServerError


def test_accounts_profile(client, respx_mock) -> None:
    respx_mock.get("https://api.octa.space/accounts").respond(
        json=load_fixture("accounts/show.json")
    )

    response = client.accounts.profile()

    assert response.is_success is True
    assert response.data["email"] == "user@example.com"


def test_accounts_balance(client, respx_mock) -> None:
    respx_mock.get("https://api.octa.space/accounts/balance").respond(
        json=load_fixture("accounts/balance.json")
    )

    response = client.accounts.balance()

    assert response.data["balance"] == 123.45


def test_accounts_generate_wallet(client, respx_mock) -> None:
    respx_mock.post("https://api.octa.space/accounts").respond(
        status_code=201,
        json={"wallet": "0xabc123"},
    )

    response = client.accounts.generate_wallet()

    assert response.status_code == 201


@pytest.mark.parametrize(
    ("status_code", "expected"),
    [
        (401, AuthenticationError),
        (429, RateLimitError),
        (500, ServerError),
    ],
)
def test_accounts_errors(client, respx_mock, status_code, expected) -> None:
    respx_mock.get("https://api.octa.space/accounts").respond(
        status_code=status_code, json={"error": "boom"}
    )

    with pytest.raises(expected):
        client.accounts.profile()
