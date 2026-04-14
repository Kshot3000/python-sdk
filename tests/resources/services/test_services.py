from __future__ import annotations

from conftest import load_fixture


def test_services_resources(client, respx_mock) -> None:
    mr_route = respx_mock.post("https://api.octa.space/services/mr").respond(
        status_code=201,
        json={"uuid": "new-sess", "status": "starting"},
    )
    respx_mock.get("https://api.octa.space/services/mr").respond(
        json=load_fixture("services/mr/index.json")
    )
    respx_mock.get("https://api.octa.space/services/vpn").respond(
        json=load_fixture("services/vpn/index.json")
    )
    respx_mock.post("https://api.octa.space/services/vpn").respond(
        status_code=201,
        json={"uuid": "new-vpn"},
    )
    respx_mock.get("https://api.octa.space/services/render").respond(json=[])
    respx_mock.post("https://api.octa.space/services/render").respond(
        status_code=201,
        json={"uuid": "new-render"},
    )
    respx_mock.get("https://api.octa.space/services/sess-abc-123/info").respond(
        json=load_fixture("services/session/info.json")
    )
    respx_mock.get("https://api.octa.space/services/sess-abc-123/logs").respond(
        json=load_fixture("services/session/logs.json")
    )
    respx_mock.post("https://api.octa.space/services/sess-abc-123/stop").respond(
        json={"status": "stopped"},
    )

    assert client.services.mr.list().data[0]["uuid"] == "mr-sess-111"
    assert client.services.vpn.list().data[0]["uuid"] == "vpn-sess-222"
    assert client.services.render.list().data == []
    assert (
        client.services.mr.create(
            node_id=1,
            disk_size=10,
            image="ubuntu:24.04",
            app="app-123",
        ).status_code
        == 201
    )
    assert mr_route.calls.last.request.read().decode("utf-8") == (
        '[{"id":0,"node_id":1,"disk_size":10,"image":"ubuntu:24.04","app":"app-123",'
        '"envs":{},"ports":[],"http_ports":[],"start_command":"","entrypoint":""}]'
    )
    assert client.services.vpn.create(node_id=1, subkind="wg").status_code == 201
    assert client.services.render.create(node_id=1, disk_size=100).status_code == 201
    assert client.services.session("sess-abc-123").info().data["status"] == "running"
    assert client.services.session("sess-abc-123").logs().data[0] == "line1"
    assert client.services.session("sess-abc-123").stop(score=5).data["status"] == "stopped"


def test_machine_rental_create_defaults_optional_fields(client, respx_mock) -> None:
    mr_route = respx_mock.post("https://api.octa.space/services/mr").respond(
        status_code=201,
        json={"uuid": "new-sess", "status": "starting"},
    )

    client.services.mr.create(
        node_id=1,
        disk_size=10,
        image="ubuntu:24.04",
    )

    assert mr_route.calls.last.request.read().decode("utf-8") == (
        '[{"id":0,"node_id":1,"disk_size":10,"image":"ubuntu:24.04","app":"",'
        '"envs":{},"ports":[],"http_ports":[],"start_command":"","entrypoint":""}]'
    )


def test_session_proxy_url_encodes_uuid(client, respx_mock) -> None:
    respx_mock.get("https://api.octa.space/services/sess%2Fencoded/info").respond(
        json={"uuid": "sess/encoded", "status": "running"},
    )

    response = client.services.session("sess/encoded").info()

    assert response.data["uuid"] == "sess/encoded"
