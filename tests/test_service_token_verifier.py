from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app_base.core.errors import ApiError
from app_base.core.identity import IdentityTokenVerifier


class FakeJwkClient:
    def __init__(self, public_key) -> None:
        self.public_key = public_key

    def get_signing_key_from_jwt(self, _token):
        return type("SigningKey", (), {"key": self.public_key})()


@pytest.fixture
def service_verifier() -> tuple[IdentityTokenVerifier, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    verifier = IdentityTokenVerifier("https://identity.test/.well-known/jwks.json", "diddifree-id")
    verifier._client = FakeJwkClient(private_key.public_key())
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": "service:pilotage",
            "role": "service",
            "status": "active",
            "token_type": "service",
            "client_id": "pilotage-staging-diddigo",
            "aud": "diddigo",
            "scope": "ride-summary:read",
            "iss": "diddifree-id",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "test-key"},
    )
    return verifier, token


def test_service_token_claims_are_accepted(service_verifier) -> None:
    verifier, token = service_verifier

    claims = verifier.decode_service_token(
        token,
        audience="diddigo",
        required_scopes={"ride-summary:read"},
        client_id="pilotage-staging-diddigo",
        expected_subject="service:pilotage",
    )

    assert claims["status"] == "active"


@pytest.mark.parametrize(
    ("audience", "required_scope", "expected_subject", "error_code"),
    [
        ("diddifree-id", "ride-summary:read", "service:pilotage", "SERVICE_TOKEN_INVALID"),
        ("diddigo", "profile:read", "service:pilotage", "SERVICE_SCOPE_INVALID"),
        ("diddigo", "ride-summary:read", "service:other", "SERVICE_SUBJECT_INVALID"),
    ],
)
def test_service_token_rejects_wrong_permissions(
    service_verifier,
    audience: str,
    required_scope: str,
    expected_subject: str,
    error_code: str,
) -> None:
    verifier, token = service_verifier

    with pytest.raises(ApiError) as error:
        verifier.decode_service_token(
            token,
            audience=audience,
            required_scopes={required_scope},
            client_id="pilotage-staging-diddigo",
            expected_subject=expected_subject,
        )

    assert error.value.code == error_code
