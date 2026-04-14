from __future__ import annotations

from conftest import load_fixture


def test_nodes_list_and_find(client, respx_mock) -> None:
    respx_mock.get("https://api.octa.space/nodes").respond(json=load_fixture("nodes/index.json"))
    respx_mock.get("https://api.octa.space/nodes/1").respond(json=load_fixture("nodes/show.json"))

    listing = client.nodes.list()
    node = client.nodes.find(1)

    assert len(listing.data) == 2
    assert node.data["state"] == "online"


def test_nodes_mutations_and_downloads(client, respx_mock) -> None:
    respx_mock.get("https://api.octa.space/nodes/1/reboot").respond(json={})
    respx_mock.patch("https://api.octa.space/nodes/1/prices").respond(json={})
    respx_mock.get("https://api.octa.space/nodes/1/ident").respond(
        content=b"node-ident",
        headers={"Content-Type": "application/octet-stream"},
    )
    respx_mock.get("https://api.octa.space/nodes/1/logs").respond(
        content=b"node-logs",
        headers={"Content-Type": "application/octet-stream"},
    )

    assert client.nodes.reboot(1).is_success is True
    assert client.nodes.update_prices(1, gpu_hour=0.5).is_success is True
    assert client.nodes.download_ident(1).body == b"node-ident"
    assert client.nodes.download_logs(1).body == b"node-logs"
