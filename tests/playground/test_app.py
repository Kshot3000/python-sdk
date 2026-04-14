from __future__ import annotations

from fastapi.testclient import TestClient
from playground.app import create_app
from playground.state import PlaygroundState


def build_client(*, mock_scenario: str = "fixtures", api_key: str = "") -> TestClient:
    state = PlaygroundState()
    state.update_settings({"mock_scenario": mock_scenario, "api_key": api_key})
    app = create_app(state)
    return TestClient(app)


def csrf_token(client: TestClient) -> str:
    return str(client.app.state.csrf_token)


def test_sidebar_matches_ruby_dummy_navigation() -> None:
    with build_client() as client:
        response = client.get("/playground/dashboard")

    assert response.status_code == 200
    for label in (
        "Dashboard",
        "Network",
        "Apps",
        "Nodes",
        "Sessions",
        "Services",
        "Idle Jobs",
        "Diagnostics",
    ):
        assert label in response.text
    assert 'href="/playground/account"' not in response.text
    assert "Request Log" in response.text
    assert ">Requests<" not in response.text


def test_dashboard_locks_account_panels_without_api_key() -> None:
    with build_client() as client:
        response = client.get("/playground/dashboard")

    assert response.status_code == 200
    assert "octa_client.network.info" in response.text
    assert "Enter an API key in the sidebar to load this resource" in response.text
    assert "user@example.com" not in response.text


def test_account_page_renders_fixture_data_with_api_key() -> None:
    with build_client(api_key="test-token-1234") as client:
        response = client.get("/playground/account")

    assert response.status_code == 200
    assert "user@example.com" in response.text
    assert "123.45" in response.text


def test_apps_page_contains_table_and_diagnostics_link() -> None:
    with build_client() as client:
        response = client.get("/playground/apps")

    assert response.status_code == 200
    assert "Use in MR Create" in response.text
    assert "octa_client.apps.list" in response.text


def test_nodes_page_can_open_detail_panel() -> None:
    with build_client() as client:
        response = client.get("/playground/nodes?selected_id=1")

    assert response.status_code == 200
    assert "Node #1" in response.text
    assert "Close detail" in response.text


def test_sessions_page_has_tabs_and_stop_modal() -> None:
    with build_client() as client:
        response = client.get("/playground/sessions?tab=current&stop_uuid=sess-abc-123")

    assert response.status_code == 200
    assert "Current" in response.text
    assert "Recent" in response.text
    assert "Stop session?" in response.text


def test_services_page_has_expected_tabs_and_notice() -> None:
    with build_client() as client:
        response = client.get("/playground/services")

    assert response.status_code == 200
    assert "Machine Rental" in response.text
    assert "Render" in response.text
    assert "VPN" in response.text
    assert "use Diagnostics for manual request inspection" in response.text


def test_idle_jobs_page_renders_form_and_results() -> None:
    with build_client() as client:
        response = client.get("/playground/idle-jobs?node_id=1&job_id=42")

    assert response.status_code == 200
    assert "Load Job" in response.text
    assert "octa_client.idle_jobs.find" in response.text
    assert "octa_client.idle_jobs.logs" in response.text


def test_diagnostics_run_and_request_log_clear() -> None:
    with build_client() as client:
        token = csrf_token(client)
        response = client.post(
            "/playground/diagnostics/run",
            data={
                "csrf_token": token,
                "call": "idle_jobs.find",
                "payload_json": '{"node_id": 1, "job_id": 42}',
            },
        )
        cleared = client.post(
            "/playground/request-log",
            data={"csrf_token": token},
            headers={"referer": "http://testserver/playground/diagnostics"},
            follow_redirects=True,
        )

    assert response.status_code == 200
    assert "octa_client.idle_jobs.find(node_id:, job_id:)" in response.text
    assert "Success" in response.text
    assert "No requests yet" in cleared.text


def test_diagnostics_invalid_json_is_reported_inline() -> None:
    with build_client() as client:
        token = csrf_token(client)
        response = client.post(
            "/playground/diagnostics/run",
            data={
                "csrf_token": token,
                "call": "services.session.stop",
                "payload_json": "{bad json",
            },
        )

    assert response.status_code == 200
    assert "PayloadError" in response.text


def test_smoke_suite_renders_report() -> None:
    with build_client(api_key="test-token-1234") as client:
        response = client.post(
            "/playground/diagnostics/smoke",
            data={"csrf_token": csrf_token(client)},
        )

    assert response.status_code == 200
    assert "SDK Smoke" in response.text
    assert "octa_client.network.info" in response.text


def test_playground_post_routes_require_csrf_token() -> None:
    with build_client() as client:
        response = client.post(
            "/playground/diagnostics/run",
            data={"call": "network.info", "payload_json": ""},
        )

    assert response.status_code == 403
