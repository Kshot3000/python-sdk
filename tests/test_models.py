from __future__ import annotations

from octaspace.models import Account, Balance, Node, Session


def test_account_and_balance_models() -> None:
    account = Account.from_dict(
        {
            "account_uuid": "acc-1",
            "email": "user@example.com",
            "avatar": "https://example.com/avatar.png",
            "balance": 12.5,
        }
    )
    balance_from_amount = Balance.from_dict({"amount": 3.5, "currency": "USD"})
    balance_from_balance = Balance.from_dict({"balance": 7})

    assert account.account_uuid == "acc-1"
    assert account.balance == 12.5
    assert balance_from_amount.currency == "USD"
    assert balance_from_balance.amount == 7.0
    assert balance_from_balance.currency == "OCTA"


def test_node_model_and_properties() -> None:
    online_node = Node.from_dict(
        {
            "id": 1,
            "ip": "1.2.3.4",
            "state": "online",
            "location": {"country": "UA"},
            "prices": {"gpu_hour": 0.5},
            "system": {"gpu": "A100"},
        }
    )
    offline_node = Node.from_dict({"id": 2, "ip": "5.6.7.8", "state": "offline"})

    assert online_node.online is True
    assert online_node.offline is False
    assert offline_node.online is False
    assert offline_node.offline is True
    assert offline_node.location == {}


def test_session_model() -> None:
    with_node = Session.from_dict(
        {
            "uuid": "sess-1",
            "service": "mr",
            "app_name": "Example App",
            "node_id": 5,
            "urls": ["https://app.example.com"],
            "prices": {"gpu_hour": 0.5},
            "node_hw": {"gpu": "A100"},
        }
    )
    without_node = Session.from_dict({"uuid": "sess-2"})

    assert with_node.node_id == 5
    assert with_node.urls == ["https://app.example.com"]
    assert without_node.node_id is None
    assert without_node.urls == []
