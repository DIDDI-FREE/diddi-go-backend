from uuid import uuid4

import pytest

from app_base.core.identity import identity_mode_enabled, identity_payload_to_user_model
from app_base.core.settings import settings

pytestmark = pytest.mark.unit


def test_identity_base_url_derives_staging_jwks_and_profile_urls(monkeypatch):
    monkeypatch.setattr(settings, "identity_base_url", "https://auth-staging.diddifree.com/")
    monkeypatch.setattr(settings, "identity_jwks_url", None)
    monkeypatch.setattr(settings, "identity_profile_url", None)

    assert settings.effective_identity_jwks_url == "https://auth-staging.diddifree.com/.well-known/jwks.json"
    assert settings.effective_identity_profile_url == "https://auth-staging.diddifree.com/identity/v1/users/me"
    assert identity_mode_enabled() is True


def test_identity_explicit_urls_override_base_url(monkeypatch):
    monkeypatch.setattr(settings, "identity_base_url", "https://auth-staging.diddifree.com")
    monkeypatch.setattr(settings, "identity_jwks_url", "https://auth.example.test/custom-jwks")
    monkeypatch.setattr(settings, "identity_profile_url", "https://auth.example.test/me")

    assert settings.effective_identity_jwks_url == "https://auth.example.test/custom-jwks"
    assert settings.effective_identity_profile_url == "https://auth.example.test/me"


def test_identity_mode_is_disabled_without_jwks_or_base_url(monkeypatch):
    monkeypatch.setattr(settings, "identity_base_url", None)
    monkeypatch.setattr(settings, "identity_jwks_url", None)

    assert identity_mode_enabled() is False


def test_identity_payload_maps_diddifree_user_role_to_passenger():
    user_id = uuid4()

    user = identity_payload_to_user_model(
        {"sub": str(user_id), "role": "user", "status": "active"},
        {"phone": "+237699000000", "full_name": "Diddi Passenger"},
    )

    assert user.id == user_id
    assert user.role == "passenger"
    assert user.status == "active"
    assert user.phone == "+237699000000"
    assert user.full_name == "Diddi Passenger"


def test_identity_payload_keeps_requested_role_if_identity_still_sends_it():
    user_id = uuid4()

    user = identity_payload_to_user_model(
        {"sub": str(user_id), "role": "user", "status": "active"},
        {"phone": "+237699000000", "requested_role": "driver"},
    )

    assert user.requested_role == "driver"


def test_identity_payload_keeps_legacy_diddigo_service_roles_during_migration():
    driver_id = uuid4()

    user = identity_payload_to_user_model(
        {"sub": str(driver_id), "role": "driver", "status": "active"},
        {"phone": "+237699111111", "full_name": "Diddi Driver"},
    )

    assert user.id == driver_id
    assert user.role == "driver"
    assert user.status == "active"
