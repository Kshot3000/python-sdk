from __future__ import annotations

import json
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

import octaspace
from octaspace import OctaSpaceClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> Any:
    return json.loads((FIXTURES_DIR / name).read_text())


@pytest.fixture(autouse=True)
def reset_global_state() -> Generator[None, None, None]:
    octaspace.reset_configuration()
    yield
    octaspace.reset_configuration()


@pytest.fixture
def client() -> Generator[OctaSpaceClient, None, None]:
    with OctaSpaceClient(api_key="test_key", max_retries=0) as instance:
        yield instance
