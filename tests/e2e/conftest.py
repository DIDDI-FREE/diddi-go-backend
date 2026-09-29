"""Fixtures for the dispatch E2E suite.

The whole module is skipped (not failed) when the credentials it needs are
absent, so `pytest` (which already excludes `-m e2e`) and any accidental
`pytest -m e2e` on an unconfigured machine both stay green/clean.
"""

from __future__ import annotations

import pytest

from tests.e2e.config import CONFIG
from tests.e2e.helpers import E2EClient


@pytest.fixture(scope="session", autouse=True)
def _require_credentials() -> None:
    missing = CONFIG.missing_prerequisites()
    if missing:
        pytest.skip(
            "dispatch E2E needs staging credentials; missing: " + ", ".join(missing),
            allow_module_level=True,
        )


@pytest.fixture
def client() -> E2EClient:
    return E2EClient()


@pytest.fixture
async def dispatch_config_guard(client: E2EClient):
    """Snapshot the live dispatch config, yield the client, and always restore
    the original config afterwards — so a test that shortens the search budget
    or wave size never leaves staging altered."""
    original = await client.get_config()
    try:
        yield client
    finally:
        await client.put_config(original)
