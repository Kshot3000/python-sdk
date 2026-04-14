from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock


@dataclass(frozen=True, slots=True)
class MockScenario:
    value: str
    label: str
    description: str


MOCK_SCENARIOS: tuple[MockScenario, ...] = (
    MockScenario(
        value="real",
        label="Real API",
        description="Use the actual OctaSpace API.",
    ),
    MockScenario(
        value="fixtures",
        label="Fixtures",
        description="Deterministic fixture-backed responses for local browser QA.",
    ),
    MockScenario(
        value="401",
        label="401 Unauthorized",
        description="Simulates invalid or missing API key.",
    ),
    MockScenario(
        value="403",
        label="403 Forbidden",
        description="Simulates insufficient permissions.",
    ),
    MockScenario(
        value="404",
        label="404 Not Found",
        description="Simulates a missing resource.",
    ),
    MockScenario(
        value="429",
        label="429 Rate Limited",
        description="Simulates rate limiting with Retry-After: 60.",
    ),
    MockScenario(
        value="500",
        label="500 Server Error",
        description="Simulates an internal server error.",
    ),
    MockScenario(
        value="slow",
        label="Slow (3s)",
        description="Adds a 3-second delay before returning fixture responses.",
    ),
    MockScenario(
        value="timeout",
        label="Timeout",
        description="Raises a timeout error without contacting the API.",
    ),
    MockScenario(
        value="network-error",
        label="Network Error",
        description="Simulates a connection failure.",
    ),
)


def _safe_scenario(value: str | None) -> str:
    candidate = (value or "").strip()
    known = {entry.value for entry in MOCK_SCENARIOS}
    return candidate if candidate in known else "real"


@dataclass(frozen=True, slots=True)
class PlaygroundSettings:
    api_key: str = ""
    base_url: str = "https://api.octa.space"
    mock_scenario: str = "real"
    sample_node_id: str = "1"
    sample_job_id: str = "42"
    sample_session_uuid: str = "sess-abc-123"

    @property
    def api_key_present(self) -> bool:
        return bool(self.api_key.strip())

    @property
    def is_mock_active(self) -> bool:
        return self.mock_scenario != "real"

    @property
    def auth_available(self) -> bool:
        return self.is_mock_active or self.api_key_present

    @property
    def selected_scenario(self) -> MockScenario:
        return next(
            (entry for entry in MOCK_SCENARIOS if entry.value == self.mock_scenario),
            MOCK_SCENARIOS[0],
        )

    @property
    def transport_label(self) -> str:
        if self.is_mock_active:
            return self.selected_scenario.label
        return "Real API"

    @property
    def transport_description(self) -> str:
        if self.is_mock_active:
            return self.selected_scenario.description
        return "Uses the real API through the Python httpx transport."

    @property
    def masked_api_key(self) -> str:
        key = self.api_key.strip()
        if not key:
            return ""
        if len(key) <= 8:
            return "*" * len(key)
        return f"{key[:4]}{'*' * max(len(key) - 8, 4)}{key[-4:]}"

    @classmethod
    def from_form(
        cls,
        form: Mapping[str, str],
        current: PlaygroundSettings | None = None,
    ) -> PlaygroundSettings:
        existing = current or cls()
        return cls(
            api_key=form.get("api_key", existing.api_key),
            base_url=form.get("base_url", existing.base_url).strip() or existing.base_url,
            mock_scenario=_safe_scenario(form.get("mock_scenario", existing.mock_scenario)),
            sample_node_id=existing.sample_node_id,
            sample_job_id=existing.sample_job_id,
            sample_session_uuid=existing.sample_session_uuid,
        )


@dataclass(frozen=True, slots=True)
class RequestLogEntry:
    timestamp: str
    label: str
    method: str
    path: str
    status: str
    duration_ms: int
    error: str | None = None


class PlaygroundState:
    _MAX_LOG_ENTRIES = 100

    def __init__(self) -> None:
        self._lock = Lock()
        self._settings = PlaygroundSettings()
        self._request_log: deque[RequestLogEntry] = deque(maxlen=self._MAX_LOG_ENTRIES)

    def snapshot_settings(self) -> PlaygroundSettings:
        with self._lock:
            return self._settings

    def update_settings(self, form: Mapping[str, str]) -> PlaygroundSettings:
        with self._lock:
            self._settings = PlaygroundSettings.from_form(form, self._settings)
            return self._settings

    def reset_settings(self) -> None:
        with self._lock:
            self._settings = PlaygroundSettings()

    def request_log(self) -> list[RequestLogEntry]:
        with self._lock:
            return list(self._request_log)  # snapshot in insertion order (newest first)

    def append_request(
        self,
        *,
        label: str,
        method: str,
        path: str,
        status: str,
        duration_ms: int,
        error: str | None = None,
    ) -> None:
        entry = RequestLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            label=label,
            method=method,
            path=path,
            status=status,
            duration_ms=duration_ms,
            error=error,
        )
        with self._lock:
            self._request_log.appendleft(entry)  # O(1), deque handles maxlen cap

    def clear_request_log(self) -> None:
        with self._lock:
            self._request_log.clear()
