from __future__ import annotations

from octaspace._transport.retry import compute_backoff, is_retryable_response


def test_retryable_statuses() -> None:
    assert is_retryable_response("GET", 500) is True
    assert is_retryable_response("POST", 500) is False
    assert is_retryable_response("DELETE", 429) is True


def test_retry_after_overrides_backoff() -> None:
    assert (
        compute_backoff(
            attempt=2,
            retry_interval=0.5,
            backoff_factor=2.0,
            retry_after=15,
        )
        == 15.0
    )
