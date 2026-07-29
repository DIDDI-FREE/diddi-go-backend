from fastapi import FastAPI

from app_base.core.errors import ApiError, api_error_handler
from app_base.core.lifespan import lifespan
from app_base.core.settings import settings
from app_base.modules.auth.presentation.router import router as auth_router
from app_base.modules.payment.presentation.router import router as payment_router
from app_base.modules.ride.presentation.driver_router import router as driver_router
from app_base.modules.ride.presentation.router import router as ride_router
from app_base.modules.ride.presentation.websocket import router as ride_ws_router

app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_exception_handler(ApiError, api_error_handler)

app.include_router(auth_router, prefix="/v1")
app.include_router(ride_router, prefix="/v1")
app.include_router(driver_router, prefix="/v1")
app.include_router(payment_router, prefix="/v1")
app.include_router(ride_ws_router, prefix="/v1")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}
