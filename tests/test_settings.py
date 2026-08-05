from __future__ import annotations

import pytest

from app_base.core.settings import Settings

pytestmark = pytest.mark.unit


def test_app_env_alias_sets_runtime_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("ENVIRONMENT", raising=False)

    assert Settings().environment == "production"


def test_environment_keeps_backward_compatibility(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "debug")
    monkeypatch.delenv("APP_ENV", raising=False)

    assert Settings().environment == "debug"
