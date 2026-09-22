"""FastAPI dependencies (dependency injection).

Central place for all `Depends`-injected services and resources. Routers
import from here rather than constructing repos or service instances inline.

Design:
  - `session_dep` yields an AsyncSession, committed if no exception
  - `get_redis` returns the shared pool from `app.state.redis`
  - `get_diddimap` returns the DiddiMap HTTP client from `app.state.diddimap`
  - Per-repo factories take the session and return a concrete repository
    satisfying the matching `Protocol` from the corresponding `domain/interfaces`
  - Per-service factories wire repositories together:
      ride_service = RideService(ride_repo, diddimap, pricing_rule_repo)
      payment_service = PaymentService(payment_repo, ride_repo)

Routers declare e.g.:
    `ride_svc: RideService = Depends(ride_service)`
and FastAPI resolves each layer automatically.
"""

# NOTE: deliberately no `from __future__ import annotations`. FastAPI reads
# the runtime annotations of dependency functions; under PEP 563 the `Request`
# parameters below arrive as the string "Request", which FastAPI cannot
# recognise as the ASGI request and instead treats as a required query
# parameter — producing `422 missing query.request` on every dependent route.

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app_base.core.database import get_session
from app_base.core.redis import get_redis  # noqa: F401 — re-exported
from app_base.core.s2s_command_store import S2SCommandStore
from app_base.core.settings import settings
from app_base.modules.auth.application.services import AuthService
from app_base.modules.auth.infra.repositories import (
    SqlAlchemyOTPRepository,
    SqlAlchemyUserRepository,
)
from app_base.modules.notification.application import DeviceService, PushNotificationService
from app_base.modules.notification.infra.fcm import build_push_gateway
from app_base.modules.notification.infra.repositories import SqlAlchemyUserDeviceRepository
from app_base.modules.partner.application.services import PartnerService
from app_base.modules.partner.infra.repositories import SqlAlchemyPartnerRepository
from app_base.modules.payment.application.return_contexts import PaymentReturnContextStore
from app_base.modules.payment.application.services import PaymentService
from app_base.modules.payment.application.wallet_service import DriverWalletService
from app_base.modules.payment.infra.diddipay_client import DiddiPayClient
from app_base.modules.payment.infra.repositories import SqlAlchemyPaymentRepository
from app_base.modules.ride.application.driver_provisioning_service import DriverProvisioningService
from app_base.modules.ride.application.driver_service import DriverService
from app_base.modules.ride.application.emergency_contact_service import EmergencyContactService
from app_base.modules.ride.application.emergency_notifications import EmergencyNotificationService
from app_base.modules.ride.application.matching_service import MatchingService
from app_base.modules.ride.application.scoring_service import ScoringService
from app_base.modules.ride.application.services import RideService
from app_base.modules.ride.application.summary_service import RideSummaryService
from app_base.modules.ride.infra.driver_location import RedisDriverLocationService
from app_base.modules.ride.infra.identity_capability_client import IdentityCapabilityClient
from app_base.modules.ride.infra.offer_store import RedisOfferStore
from app_base.modules.ride.infra.repositories import (
    SqlAlchemyDriverProfileRepository,
    SqlAlchemyEmergencyContactRepository,
    SqlAlchemyPricingRuleRepository,
    SqlAlchemyRideRepository,
    SqlAlchemyVehicleRepository,
)
from app_base.modules.ride.infra.routing_client import DiddiMapRoutingClient
from app_base.modules.ride.infra.summary_repository import SqlAlchemyRideSummaryRepository

# --- sessions & resources --------------------------------------------------

# `get_session` is already an async-generator dependency that commits on
# success and rolls back on error. Re-export it directly rather than wrapping
# it in another generator: an `async for` wrapper is abandoned mid-iteration
# when FastAPI closes the outer dependency, so the inner generator's code
# after `yield` — the commit — never runs, and every write is silently lost.
session_dep = get_session


def get_diddimap(request: Request) -> DiddiMapRoutingClient:
    """FastAPI dependency — returns the DiddiMap HTTP client mounted on
    app.state by the lifespan."""
    client: DiddiMapRoutingClient | None = getattr(request.app.state, "diddimap", None)
    if client is None:
        raise RuntimeError("DiddiMap client not initialized — lifespan may not have run.")
    return client


def get_driver_locations(request: Request) -> RedisDriverLocationService:
    """FastAPI dependency — Redis GEO driver location service from app.state."""
    service: RedisDriverLocationService | None = getattr(
        request.app.state, "driver_locations", None,
    )
    if service is None:
        raise RuntimeError("Driver location service not initialized — lifespan may not have run.")
    return service


async def kyc_command_store(redis: Redis = Depends(get_redis)) -> S2SCommandStore:
    return S2SCommandStore(
        redis,
        namespace="kyc-command",
        ttl_seconds=settings.kyc_command_idempotency_ttl_seconds,
    )


async def driver_provisioning_command_store(redis: Redis = Depends(get_redis)) -> S2SCommandStore:
    return S2SCommandStore(
        redis,
        namespace="driver-provision",
        ttl_seconds=settings.driver_provisioning_idempotency_ttl_seconds,
    )


_unconfigured_identity_capabilities = IdentityCapabilityClient(
    base_url=None,
    client_id=None,
    client_secret=None,
)


def get_identity_capabilities(request: Request) -> IdentityCapabilityClient:
    client: IdentityCapabilityClient | None = getattr(request.app.state, "identity_capabilities", None)
    return client or _unconfigured_identity_capabilities


# --- repositories ----------------------------------------------------------

async def user_repo(session: AsyncSession = Depends(session_dep)) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)


async def otp_repo(session: AsyncSession = Depends(session_dep)) -> SqlAlchemyOTPRepository:
    return SqlAlchemyOTPRepository(session)


async def ride_repo(session: AsyncSession = Depends(session_dep)) -> SqlAlchemyRideRepository:
    return SqlAlchemyRideRepository(session)


async def ride_summary_service(session: AsyncSession = Depends(session_dep)) -> RideSummaryService:
    return RideSummaryService(SqlAlchemyRideSummaryRepository(session))


async def driver_profile_repo(
    session: AsyncSession = Depends(session_dep),
) -> SqlAlchemyDriverProfileRepository:
    return SqlAlchemyDriverProfileRepository(session)


async def vehicle_repo(session: AsyncSession = Depends(session_dep)) -> SqlAlchemyVehicleRepository:
    return SqlAlchemyVehicleRepository(session)


async def pricing_rule_repo(
    session: AsyncSession = Depends(session_dep),
) -> SqlAlchemyPricingRuleRepository:
    return SqlAlchemyPricingRuleRepository(session)


async def payment_repo(session: AsyncSession = Depends(session_dep)) -> SqlAlchemyPaymentRepository:
    return SqlAlchemyPaymentRepository(session)


async def user_device_repo(session: AsyncSession = Depends(session_dep)) -> SqlAlchemyUserDeviceRepository:
    return SqlAlchemyUserDeviceRepository(session)


async def partner_repo(session: AsyncSession = Depends(session_dep)) -> SqlAlchemyPartnerRepository:
    return SqlAlchemyPartnerRepository(session)


async def emergency_contact_repo(
    session: AsyncSession = Depends(session_dep),
) -> SqlAlchemyEmergencyContactRepository:
    return SqlAlchemyEmergencyContactRepository(session)


# --- services --------------------------------------------------------------

async def auth_service(
    user_repo_dep: SqlAlchemyUserRepository = Depends(user_repo),
    otp_repo_dep: SqlAlchemyOTPRepository = Depends(otp_repo),
) -> AuthService:
    return AuthService(user_repo=user_repo_dep, otp_repo=otp_repo_dep)


async def ride_service(
    ride_repo_dep: SqlAlchemyRideRepository = Depends(ride_repo),
    pricing_rule_repo_dep: SqlAlchemyPricingRuleRepository = Depends(pricing_rule_repo),
    diddimap: DiddiMapRoutingClient = Depends(get_diddimap),
    driver_repo_dep: SqlAlchemyDriverProfileRepository = Depends(driver_profile_repo),
    vehicle_repo_dep: SqlAlchemyVehicleRepository = Depends(vehicle_repo),
    user_repo_dep: SqlAlchemyUserRepository = Depends(user_repo),
    emergency_contact_repo_dep: SqlAlchemyEmergencyContactRepository = Depends(emergency_contact_repo),
) -> RideService:
    return RideService(
        ride_repo=ride_repo_dep,
        routing=diddimap,
        pricing_rules=pricing_rule_repo_dep,
        driver_repo=driver_repo_dep,
        vehicle_repo=vehicle_repo_dep,
        user_repo=user_repo_dep,
        emergency_contact_repo=emergency_contact_repo_dep,
        emergency_notifications=EmergencyNotificationService(),
    )


async def payment_service(
    payment_repo_dep: SqlAlchemyPaymentRepository = Depends(payment_repo),
    ride_repo_dep: SqlAlchemyRideRepository = Depends(ride_repo),
    redis: Redis = Depends(get_redis),
) -> PaymentService:
    return PaymentService(
        payment_repo=payment_repo_dep,
        ride_repo=ride_repo_dep,
        diddipay=DiddiPayClient(),
        return_contexts=PaymentReturnContextStore(
            redis, ttl_seconds=settings.payment_return_context_ttl_seconds,
        ),
    )


async def driver_wallet_service(
    payment_repo_dep: SqlAlchemyPaymentRepository = Depends(payment_repo),
    driver_repo_dep: SqlAlchemyDriverProfileRepository = Depends(driver_profile_repo),
    redis: Redis = Depends(get_redis),
) -> DriverWalletService:
    return DriverWalletService(
        payment_repo=payment_repo_dep,
        driver_repo=driver_repo_dep,
        diddipay=DiddiPayClient(),
        return_contexts=PaymentReturnContextStore(
            redis, ttl_seconds=settings.payment_return_context_ttl_seconds,
        ),
    )


async def payment_return_context_store(redis: Redis = Depends(get_redis)) -> PaymentReturnContextStore:
    return PaymentReturnContextStore(redis, ttl_seconds=settings.payment_return_context_ttl_seconds)


async def driver_service(
    driver_repo_dep: SqlAlchemyDriverProfileRepository = Depends(driver_profile_repo),
    vehicle_repo_dep: SqlAlchemyVehicleRepository = Depends(vehicle_repo),
    capability_publisher: IdentityCapabilityClient = Depends(get_identity_capabilities),
) -> DriverService:
    return DriverService(
        driver_repo=driver_repo_dep,
        vehicle_repo=vehicle_repo_dep,
        capability_publisher=capability_publisher,
    )


async def driver_provisioning_service(
    users: SqlAlchemyUserRepository = Depends(user_repo),
    drivers: DriverService = Depends(driver_service),
) -> DriverProvisioningService:
    return DriverProvisioningService(users=users, drivers=drivers)


async def scoring_service(
    ride_repo_dep: SqlAlchemyRideRepository = Depends(ride_repo),
    driver_repo_dep: SqlAlchemyDriverProfileRepository = Depends(driver_profile_repo),
) -> ScoringService:
    return ScoringService(ride_repo=ride_repo_dep, driver_repo=driver_repo_dep)


async def emergency_contact_service(
    emergency_contact_repo_dep: SqlAlchemyEmergencyContactRepository = Depends(emergency_contact_repo),
) -> EmergencyContactService:
    return EmergencyContactService(contacts=emergency_contact_repo_dep)


async def device_service(
    user_device_repo_dep: SqlAlchemyUserDeviceRepository = Depends(user_device_repo),
) -> DeviceService:
    return DeviceService(devices=user_device_repo_dep)


async def push_notification_service(
    user_device_repo_dep: SqlAlchemyUserDeviceRepository = Depends(user_device_repo),
) -> PushNotificationService:
    return PushNotificationService(devices=user_device_repo_dep, gateway=build_push_gateway())


async def partner_service(
    partner_repo_dep: SqlAlchemyPartnerRepository = Depends(partner_repo),
    vehicle_repo_dep: SqlAlchemyVehicleRepository = Depends(vehicle_repo),
    driver_repo_dep: SqlAlchemyDriverProfileRepository = Depends(driver_profile_repo),
) -> PartnerService:
    return PartnerService(
        partner_repo=partner_repo_dep,
        vehicle_repo=vehicle_repo_dep,
        driver_repo=driver_repo_dep,
    )


def get_offer_store(redis: Redis = Depends(get_redis)) -> RedisOfferStore:
    return RedisOfferStore(redis=redis)


async def matching_service(
    ride_repo_dep: SqlAlchemyRideRepository = Depends(ride_repo),
    driver_repo_dep: SqlAlchemyDriverProfileRepository = Depends(driver_profile_repo),
    vehicle_repo_dep: SqlAlchemyVehicleRepository = Depends(vehicle_repo),
    payment_repo_dep: SqlAlchemyPaymentRepository = Depends(payment_repo),
    partner_service_dep: PartnerService = Depends(partner_service),
    locations: RedisDriverLocationService = Depends(get_driver_locations),
    offers: RedisOfferStore = Depends(get_offer_store),
) -> MatchingService:
    return MatchingService(
        ride_repo=ride_repo_dep,
        driver_repo=driver_repo_dep,
        vehicle_repo=vehicle_repo_dep,
        partner_service=partner_service_dep,
        locations=locations,
        offers=offers,
        payment_repo=payment_repo_dep,
    )


__all__ = [
    "Depends",
    "Redis",
    "get_diddimap",
    "get_driver_locations",
    "get_offer_store",
    "get_redis",
    "session_dep",
    "auth_service",
    "ride_service",
    "payment_service",
    "driver_wallet_service",
    "driver_service",
    "scoring_service",
    "device_service",
    "push_notification_service",
    "matching_service",
    "user_repo",
    "otp_repo",
    "ride_repo",
    "driver_profile_repo",
    "vehicle_repo",
    "pricing_rule_repo",
    "payment_repo",
    "user_device_repo",
    "partner_repo",
    "emergency_contact_repo",
    "partner_service",
    "emergency_contact_service",
]
