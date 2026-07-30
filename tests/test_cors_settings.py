from fastapi.middleware.cors import CORSMiddleware
import pytest

from app_base.core.settings import Settings
from app_base.main import app

pytestmark = pytest.mark.unit


def test_cors_origins_accept_comma_separated_environment_value():
    settings = Settings(
        _env_file=None,
        cors_origins="https://go-staging.diddifree.com, http://localhost:5173",
    )

    assert settings.cors_origin_list == ["https://go-staging.diddifree.com", "http://localhost:5173"]


def test_cors_localhost_regex_is_enabled_by_default():
    settings = Settings(_env_file=None)

    assert settings.cors_origin_regex == r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"


def test_fastapi_registers_cors_middleware():
    assert any(middleware.cls is CORSMiddleware for middleware in app.user_middleware)
