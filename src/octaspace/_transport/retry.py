from __future__ import annotations

import random

RETRYABLE_STATUSES = {408, 429, 500, 502, 503, 504}
RETRYABLE_METHODS = {"GET", "HEAD", "OPTIONS", "PUT", "DELETE"}


def is_retryable_response(method: str, status_code: int) -> bool:
    return method.upper() in RETRYABLE_METHODS and status_code in RETRYABLE_STATUSES


def compute_backoff(
    *,
    attempt: int,
    retry_interval: float,
    backoff_factor: float,
    retry_after: int | None = None,
    jitter: float = 0.1,
) -> float:
    if retry_after is not None:
        return max(float(retry_after), 0.0)
    return retry_interval * (backoff_factor**attempt) + random.uniform(0.0, jitter)
