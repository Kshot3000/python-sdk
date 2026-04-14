from __future__ import annotations

import time

from octaspace._transport.rotator import UrlRotator


def test_rotator_round_robin_and_failure_recovery() -> None:
    rotator = UrlRotator(["https://a.octa.space", "https://b.octa.space"], failure_cooldown=0.01)
    first = rotator.next_url()
    second = rotator.next_url()

    assert {first, second} == {"https://a.octa.space", "https://b.octa.space"}

    rotator.mark_failed(first)
    assert rotator.next_url() == second

    time.sleep(0.02)
    assert first in rotator.available_urls()


def test_rotator_stats_reset_and_fallback() -> None:
    rotator = UrlRotator(["https://only.octa.space"], failure_cooldown=1.0)

    assert rotator.failure_cooldown == 1.0
    rotator.mark_failed("https://only.octa.space")
    assert rotator.next_url() == "https://only.octa.space"
    assert rotator.stats()["failed"] == ["https://only.octa.space"]

    rotator.mark_success("https://only.octa.space")
    rotator.mark_failed("https://only.octa.space")
    rotator.reset()

    assert rotator.stats()["failed"] == []
