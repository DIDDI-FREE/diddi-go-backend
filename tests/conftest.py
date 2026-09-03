"""Pytest fixtures for the DiddiGo test suite.

Strategy:
  * Tests run against the real Postgres + PostGIS from docker-compose
    (port 15433 by default) using a dedicated `diddi_go_test` database, so PostGIS
    geography columns and CHECK/UNIQUE constraints are exercised for real.
    SQLite cannot host `GEOGRAPHY(POINT, 4326)`, so an in-memory DB is not
    an option here.
  * The schema is created once per session by running Alembic against the
    test database, then dropped at the end.
  * `client` yields an httpx.AsyncClient bound to the ASGI app in-process
    (no network), with the app's DB engine pointed at the test database.
  * `otp_code` captures the plaintext OTP that `AuthService.request_otp`
    logs, so tests can complete the verify step without an SMS provider.
"""

from __future__ import annotations

import logging
import os
import re
import uuid
from collections.abc import AsyncIterator, Iterator
from types import SimpleNamespace

import pytest

# The app reads settings at import time, so the test DB URL must be in the
# environment before any `app_base.*` module is imported.
TEST_DB_NAME = "diddi_go_test"
TEST_POSTGRES_PORT = os.environ.get("TEST_POSTGRES_PORT", os.environ.get("POSTGRES_PORT", "15433"))
ADMIN_DSN = f"postgresql://postgres:postgres@localhost:{TEST_POSTGRES_PORT}/postgres"
TEST_DSN_SYNC = f"postgresql://postgres:postgres@localhost:{TEST_POSTGRES_PORT}/{TEST_DB_NAME}"
TEST_DSN_ASYNC = f"postgresql+asyncpg://postgres:postgres@localhost:{TEST_POSTGRES_PORT}/{TEST_DB_NAME}"

os.environ["DATABASE_URL"] = TEST_DSN_ASYNC
os.environ.setdefault("REDIS_URL", f"redis://localhost:{os.environ.get('REDIS_PORT', '16380')}/0")
os.environ.setdefault("JWT_SECRET", "test-secret-at-least-32-characters-long!!")
# Rate limit off by default so back-to-back OTP requests in tests don't 429.
os.environ.setdefault("OTP_RATE_LIMIT_SECONDS", "0")
# Point DiddiMap at a closed port so the unreachable-service path is taken
# immediately (connection refused) instead of burning the full HTTP timeout
# on every pricing call. Tests that need DiddiMap success paths use a stub
# transport; production code must fail loudly if DiddiMap is unavailable.
os.environ.setdefault("DIDDIMAP_BASE_URL", "http://127.0.0.1:9")


class FakeDiddiMap:
    async def estimate(self, origin, destination, profile="palh_vtc"):
        from app_base.modules.ride.infra.routing_client import RouteEstimateResult

        return RouteEstimateResult(distance_km=11.876, duration_seconds=983)

    async def geocode(self, query, bias=None, limit=None):
        from app_base.shared_kernel.types import GeoPoint

        return [
            SimpleNamespace(label=f"{query}, Abidjan", point=GeoPoint(lat=5.3204, lng=-4.0161)),
        ][: limit or 1]

    async def start_trace(
        self,
        *,
        start,
        end,
        planned_distance_km=None,
        planned_duration_seconds=None,
        profile="palh_vtc",
    ):
        return "test-map-trace-1"

    async def append_trace_positions(self, trace_id, points):
        return None

    async def finish_trace(self, trace_id, *, finished_at):
        return None

    async def analyze_trace(self, trace_id):
        from decimal import Decimal

        return SimpleNamespace(actual_distance_km=Decimal("12.345"), actual_duration_seconds=1200)


def _is_unit_only_session(request: pytest.FixtureRequest) -> bool:
    return bool(request.session.items) and all(item.get_closest_marker("unit") for item in request.session.items)


def _recreate_test_database() -> None:
    """Drop + create `diddi_go_test`, install extensions and schemas."""
    import psycopg

    with psycopg.connect(ADMIN_DSN, autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = %s AND pid <> pg_backend_pid()",
            (TEST_DB_NAME,),
        )
        cur.execute(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"')
        cur.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')

    with psycopg.connect(TEST_DSN_SYNC, autocommit=True) as conn, conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS postgis")
        cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        cur.execute("CREATE SCHEMA IF NOT EXISTS auth")
        cur.execute("CREATE SCHEMA IF NOT EXISTS ride")
        cur.execute("CREATE SCHEMA IF NOT EXISTS payment")


def _run_migrations() -> None:
    from alembic.config import Config

    from alembic import command

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg = Config(os.path.join(root, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(root, "alembic"))
    cfg.set_main_option("sqlalchemy.url", TEST_DSN_ASYNC)
    command.upgrade(cfg, "head")


@pytest.fixture(scope="session", autouse=True)
def database(request: pytest.FixtureRequest) -> Iterator[None]:
    if _is_unit_only_session(request):
        yield
        return

    _recreate_test_database()
    _run_migrations()
    yield


@pytest.fixture(autouse=True)
async def clean_redis(request: pytest.FixtureRequest) -> AsyncIterator[None]:
    """Wipe matching state between tests.

    Driver positions, availability markers and in-flight offers all live in
    Redis with second-to-minute TTLs. Without this, a driver who went online
    in one test is still a matching candidate in the next, making results
    depend on execution order.
    """
    if request.node.get_closest_marker("unit"):
        yield
        return

    from app_base.core.redis import create_redis_pool
    from app_base.core.settings import settings

    redis = create_redis_pool(settings.redis_url)
    await redis.flushdb()
    try:
        yield
    finally:
        await redis.flushdb()
        await redis.aclose()


@pytest.fixture
async def client(database) -> AsyncIterator[httpx.AsyncClient]:  # noqa: F821
    import httpx

    from app_base.core.database import engine
    from app_base.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        # Lifespan doesn't run under ASGITransport, so mount the resources
        # the routes expect on app.state manually — mirroring
        # `app_base.core.lifespan.lifespan`.
        from app_base.core.redis import create_redis_pool
        from app_base.core.settings import settings
        from app_base.modules.ride.infra.driver_location import RedisDriverLocationService

        app.state.redis = create_redis_pool(settings.redis_url)
        app.state.diddimap = FakeDiddiMap()
        app.state.driver_locations = RedisDriverLocationService(redis=app.state.redis)
        try:
            yield c
        finally:
            await app.state.redis.aclose()
            # pytest-asyncio gives each test its own event loop, but `engine`
            # is module-level and pools asyncpg connections bound to the loop
            # that opened them. Reusing those in the next test raises
            # `AttributeError: 'NoneType' object has no attribute 'send'` on
            # the Windows proactor loop, so drop the pool between tests.
            await engine.dispose()


AUTH_LOGGER = "app_base.modules.auth.application.services"


class OtpCapture(logging.Handler):
    """Log handler that records the plaintext OTP `AuthService.request_otp`
    emits, so tests can complete the verify step without an SMS provider.

    Implemented as its own handler rather than via pytest's `caplog` because
    caplog only captures records emitted inside the test function body — the
    `passenger` / `driver` fixtures request OTPs during setup, which caplog
    does not see.
    """

    _PATTERN = re.compile(r"is (\d{6})\.")

    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.codes: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        match = self._PATTERN.search(record.getMessage())
        if match:
            self.codes.append(match.group(1))

    def latest(self) -> str:
        if not self.codes:
            raise AssertionError("No OTP code was logged — did request_otp run?")
        return self.codes[-1]


@pytest.fixture
def otp_code() -> Iterator[OtpCapture]:
    handler = OtpCapture()
    logger = logging.getLogger(AUTH_LOGGER)
    previous_level = logger.level
    logger.setLevel(logging.WARNING)
    logger.addHandler(handler)
    try:
        yield handler
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)


@pytest.fixture
def phone_factory():
    """Unique phone numbers so tests never collide on the UNIQUE constraint."""
    def _make(prefix: str = "+22507") -> str:
        return f"{prefix}{uuid.uuid4().int % 10_000_000:07d}"
    return _make


@pytest.fixture
async def passenger_factory(client, otp_code, phone_factory):
    """Build additional passengers — for tests that need more than one, e.g.
    checking that a busy driver is unavailable to a second rider."""
    from tests.test_auth_flow import register_and_login

    async def _make() -> dict[str, str]:
        token = await register_and_login(
            client, otp_code, phone_factory("+22507"), role="passenger",
        )
        return {"Authorization": f"Bearer {token}"}

    return _make


@pytest.fixture
async def passenger_headers(passenger_factory) -> dict[str, str]:
    """Authorization header for a freshly registered, verified passenger."""
    return await passenger_factory()


@pytest.fixture
async def driver_headers(client, otp_code, phone_factory) -> dict[str, str]:
    """Authorization header for a freshly registered, verified driver.

    Auth only — no driver profile or vehicle, so this driver cannot yet be
    matched. Use `online_driver` for one that can take rides.
    """
    from tests.test_auth_flow import register_and_login

    token = await register_and_login(client, otp_code, phone_factory("+22508"), role="driver")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def admin_headers(client, otp_code, phone_factory) -> dict[str, str]:
    """Authorization header for an admin who can review driver KYC."""
    from tests.test_auth_flow import register_and_login

    token = await register_and_login(client, otp_code, phone_factory("+22506"), role="admin")
    return {"Authorization": f"Bearer {token}"}


# Default pickup used across ride tests; drivers go online here so they fall
# inside the matching radius.
ABIDJAN_PICKUP = {"lat": 5.3599, "lng": -4.0083}


@pytest.fixture
async def driver_factory(client, otp_code, phone_factory, admin_headers):
    """Build fully onboarded drivers sitting in the matching pool.

    Each call registers a driver, creates their profile and vehicle, and puts
    them online at `location` — the complete prerequisite chain for the
    matching engine to consider them.
    """
    from tests.test_auth_flow import register_and_login

    async def _make(location: dict[str, float] | None = None) -> dict[str, str]:
        token = await register_and_login(client, otp_code, phone_factory("+22508"), role="driver")
        headers = {"Authorization": f"Bearer {token}"}

        r = await client.post(
            "/v1/drivers/profile",
            json={
                "license_number": f"CI-{uuid.uuid4().hex[:8].upper()}",
                **full_driver_kyc_documents(),
            },
            headers=headers,
        )
        assert r.status_code == 201, r.text
        driver_id = r.json()["id"]

        r = await client.post(
            f"/v1/drivers/{driver_id}/kyc/approve",
            json={"notes": "test fixture approval"},
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text

        r = await client.post(
            "/v1/drivers/vehicle",
            json={
                "plate_number": f"CI-{uuid.uuid4().hex[:6].upper()}",
                "make": "Toyota",
                "model": "Yaris",
                "color": "gris",
                "category": "standard",
            },
            headers=headers,
        )
        assert r.status_code == 201, r.text

        r = await client.post("/v1/drivers/online", json=location or ABIDJAN_PICKUP, headers=headers)
        assert r.status_code == 200, r.text
        return headers

    return _make


def full_driver_kyc_documents() -> dict[str, str]:
    """Complete KYC payload required before an admin can approve a driver."""
    return {
        "license_document_file_id": str(uuid.uuid4()),
        "license_back_document_file_id": str(uuid.uuid4()),
        "national_id_document_file_id": str(uuid.uuid4()),
        "national_id_back_document_file_id": str(uuid.uuid4()),
        "selfie_document_file_id": str(uuid.uuid4()),
    }


@pytest.fixture
async def online_driver(driver_factory) -> dict[str, str]:
    """A single onboarded driver, online at the default pickup point."""
    return await driver_factory()


# Short aliases used throughout the ride and matching tests.
@pytest.fixture
def passenger(passenger_headers) -> dict[str, str]:
    return passenger_headers


@pytest.fixture
def driver(online_driver) -> dict[str, str]:
    """An onboarded driver in the matching pool — rides created in a test are
    offered to them."""
    return online_driver
