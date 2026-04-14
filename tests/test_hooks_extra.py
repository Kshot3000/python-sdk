from __future__ import annotations

import httpx

from octaspace.hooks import HookDispatcher


class _Logger:
    def __init__(self) -> None:
        self.messages: list[tuple[str, tuple[object, ...]]] = []

    def debug(self, message: str, *args: object) -> None:
        self.messages.append((message, args))


def test_hook_dispatcher_logger_and_empty_event_hooks() -> None:
    empty = HookDispatcher()
    logger = _Logger()
    dispatcher = HookDispatcher(logger=logger)
    request = httpx.Request("GET", "https://api.octa.space/nodes?limit=10")

    assert empty.event_hooks() == {}

    dispatcher.event_hooks()["request"][0](request)

    assert logger.messages


def test_hook_dispatcher_response_wrapper_uses_cache() -> None:
    captured: list[int] = []
    dispatcher = HookDispatcher(on_response=lambda response: captured.append(response.status_code))
    response = httpx.Response(200, json={"ok": True})

    wrapped = dispatcher.response_wrapper(response)
    wrapped_again = dispatcher.response_wrapper(response)

    assert wrapped is wrapped_again
    assert captured == [200]
