from __future__ import annotations

from conftest import load_fixture


def test_misc_resources(client, respx_mock) -> None:
    respx_mock.get("https://api.octa.space/sessions").respond(
        json=load_fixture("sessions/index.json")
    )
    respx_mock.get("https://api.octa.space/apps").respond(json=load_fixture("apps/index.json"))
    respx_mock.get("https://api.octa.space/network").respond(json=load_fixture("network/info.json"))
    respx_mock.get("https://api.octa.space/idle_jobs/69/42").respond(
        json=load_fixture("idle_jobs/show.json")
    )
    respx_mock.get("https://api.octa.space/idle_jobs/69/42/logs").respond(
        json=load_fixture("idle_jobs/logs.json")
    )

    assert client.sessions.list().data[0]["uuid"] == "sess-1"
    assert client.apps.list().data[0]["uuid"] == "app-1"
    assert client.network.info().data["power"] == 1234
    assert client.idle_jobs.find(node_id=69, job_id=42).data["status"] == "running"
    assert client.idle_jobs.logs(node_id=69, job_id=42).data[0] == "job line 1"
