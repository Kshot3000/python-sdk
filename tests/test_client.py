from __future__ import annotations

import octaspace
from octaspace import OctaSpaceClient
from octaspace._transport.mock_transport import MockTransport
from octaspace.resources import (
    AccountsResource,
    AppsResource,
    IdleJobsResource,
    NetworkResource,
    NodesResource,
    ServicesResource,
    SessionsResource,
)


def test_client_initializes_resources() -> None:
    client = OctaSpaceClient()

    assert isinstance(client.accounts, AccountsResource)
    assert isinstance(client.nodes, NodesResource)
    assert isinstance(client.sessions, SessionsResource)
    assert isinstance(client.apps, AppsResource)
    assert isinstance(client.network, NetworkResource)
    assert isinstance(client.services, ServicesResource)
    assert isinstance(client.idle_jobs, IdleJobsResource)
    client.close()


def test_client_accepts_injected_transport() -> None:
    transport = MockTransport()
    client = OctaSpaceClient(transport=transport)

    assert client.transport_stats()["mode"] == "mock"


def test_shared_client_helpers() -> None:
    octaspace.configure(api_key="test_key")

    shared = octaspace.client()
    again = octaspace.client()
    one_off = octaspace.client(api_key="other")

    assert shared is again
    assert one_off is not shared

    octaspace.shutdown_shared_client()
