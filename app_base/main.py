from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from app_base.core.database import database_ready
from app_base.core.errors import (
    ApiError,
    api_error_handler,
    infrastructure_error_handler,
    unhandled_exception_handler,
)
from app_base.core.lifespan import lifespan
from app_base.core.metrics import render_prometheus
from app_base.core.observability import configure_observability
from app_base.core.request_logging import RequestLoggingMiddleware
from app_base.core.settings import settings
from app_base.modules.auth.presentation.router import router as auth_router
from app_base.modules.notification.presentation import router as notification_router
from app_base.modules.observability.presentation.router import router as observability_router
from app_base.modules.partner.presentation.router import admin_router as partner_admin_router
from app_base.modules.partner.presentation.router import router as partner_router
from app_base.modules.payment.presentation.router import admin_payment_router, admin_wallet_router, wallet_router
from app_base.modules.payment.presentation.router import internal_router as payment_internal_router
from app_base.modules.payment.presentation.router import return_router as payment_return_router
from app_base.modules.payment.presentation.router import router as payment_router
from app_base.modules.ride.presentation.capabilities_router import router as capabilities_router
from app_base.modules.ride.presentation.driver_internal_router import router as driver_internal_router
from app_base.modules.ride.presentation.driver_router import admin_vehicle_router
from app_base.modules.ride.presentation.driver_router import router as driver_router
from app_base.modules.ride.presentation.kyc_internal_router import router as kyc_internal_router
from app_base.modules.ride.presentation.router import places_router
from app_base.modules.ride.presentation.router import router as ride_router
from app_base.modules.ride.presentation.summary_router import router as ride_summary_router
from app_base.modules.ride.presentation.websocket import router as ride_ws_router

configure_observability(log_level=settings.log_level)

app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(ApiError, api_error_handler)
app.add_exception_handler(SQLAlchemyError, infrastructure_error_handler)
app.add_exception_handler(RedisError, infrastructure_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(auth_router, prefix="/v1")
app.include_router(notification_router, prefix="/v1")
app.include_router(observability_router, prefix="/v1")
app.include_router(capabilities_router, prefix="/v1")
app.include_router(places_router, prefix="/v1")
app.include_router(ride_router, prefix="/v1")
app.include_router(ride_summary_router)
app.include_router(driver_internal_router)
app.include_router(kyc_internal_router)
app.include_router(driver_router, prefix="/v1")
app.include_router(admin_vehicle_router, prefix="/v1")
app.include_router(payment_router, prefix="/v1")
app.include_router(wallet_router, prefix="/v1")
app.include_router(admin_wallet_router, prefix="/v1")
app.include_router(admin_payment_router, prefix="/v1")
app.include_router(partner_admin_router, prefix="/v1")
app.include_router(partner_router, prefix="/v1")
app.include_router(ride_ws_router, prefix="/v1")
app.include_router(payment_internal_router)
app.include_router(payment_return_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}


@app.get("/ready")
async def readiness(request: Request) -> Response:
    db_ok = await database_ready()
    redis_pool = getattr(request.app.state, "redis", None)
    try:
        redis_ok = redis_pool is not None and bool(await redis_pool.ping())
    except Exception:
        redis_ok = False
    payload = {
        "status": "ready" if db_ok and redis_ok else "not_ready",
        "app": settings.app_name,
        "components": {"database": "ok" if db_ok else "unavailable", "redis": "ok" if redis_ok else "unavailable"},
    }
    return JSONResponse(status_code=200 if db_ok and redis_ok else 503, content=payload)


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(render_prometheus(), media_type="text/plain; version=0.0.4; charset=utf-8")
