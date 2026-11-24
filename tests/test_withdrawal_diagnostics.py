import json
import logging
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app_base.core.errors import ApiError, api_error_handler, request_validation_error_handler
from app_base.core.settings import settings
from app_base.modules.payment.application.wallet_service import DriverWalletService
from app_base.modules.payment.presentation.schemas import DriverWithdrawalRequest

pytestmark = pytest.mark.unit


def test_withdrawal_validation_identifies_fields_without_logging_values(caplog):
    app = FastAPI()
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    called = []

    @app.middleware("http")
    async def context(request: Request, call_next):
        request.state.request_id = "qa-withdrawal-1"
        request.state.current_user = SimpleNamespace(id="qa-user")
        return await call_next(request)

    @app.post("/v1/drivers/me/wallet/withdrawals")
    async def withdraw(payload: DriverWithdrawalRequest):
        called.append(payload)
        return {}

    payload = {
        "quote_id": str(uuid4()), "beneficiary_reference": "private-beneficiary",
        "beneficiary_destination": {"phone": "+2250700000111", "network": "wave"},
        "verification_code": "987654-private-otp", "secret-extra-field": "private-extra-value",
    }
    with caplog.at_level(logging.WARNING):
        response = TestClient(app).post("/v1/drivers/me/wallet/withdrawals", json=payload)
    assert response.status_code == 422
    assert not called
    assert response.json()["error"]["request_id"] == "qa-withdrawal-1"
    assert response.headers["X-Request-ID"] == "qa-withdrawal-1"
    event = next(json.loads(r.message) for r in caplog.records if "withdrawal.request.validation_failed" in r.message)
    assert event["attributes"]["user_id"] == "qa-user"
    assert event["request_id"] == "qa-withdrawal-1"
    assert {"loc": ["body", "verification_id"], "type": "missing"} in event["attributes"]["violations"]
    assert {
        "loc": ["body", "verification_code"],
        "type": "string_pattern_mismatch",
    } in event["attributes"]["violations"]
    for secret in ["private-beneficiary", "+2250700000111", "987654", "secret-extra-field", "private-extra-value"]:
        assert secret not in caplog.text


async def test_custom_validation_message_and_context_are_not_logged(caplog):
    request = Request({"type": "http", "method": "POST", "path": "/v1/drivers/me/wallet/withdrawals",
                       "headers": [], "query_string": b""})
    error = RequestValidationError([{
        "loc": ("body", "private-key"), "type": "custom-private-error",
        "msg": "secret OTP 654321", "input": "654321", "ctx": {"secret": "654321"},
    }])
    with caplog.at_level(logging.WARNING):
        await request_validation_error_handler(request, error)
    assert "654321" not in caplog.text
    assert "private-key" not in caplog.text
    assert "custom-private-error" not in caplog.text


async def test_business_rejection_logs_code_not_otp_or_phone(caplog):
    request = Request({"type": "http", "method": "POST", "path": "/v1/drivers/me/wallet/withdrawals",
                       "headers": [], "query_string": b""})
    request.state.request_id = "qa-business-1"
    with caplog.at_level(logging.WARNING):
        await api_error_handler(request, ApiError(409, "QUOTE_EXPIRED", "private message", {"otp": "987654"}))
    assert '"error_code":"QUOTE_EXPIRED"' in caplog.text
    assert "private message" not in caplog.text
    assert "987654" not in caplog.text


async def test_minimum_message_uses_server_configuration(monkeypatch):
    monkeypatch.setattr(settings, "driver_withdrawal_min_amount_xof", 3500)
    service = DriverWalletService(
        payment_repo=SimpleNamespace(get_or_create_wallet=AsyncMock()),
        driver_repo=SimpleNamespace(find_by_user_id=AsyncMock(return_value=SimpleNamespace(id=uuid4()))),
    )
    with pytest.raises(ApiError) as failure:
        await service.quote_withdrawal(driver_user_id=uuid4(), amount=Decimal("1000"))
    assert failure.value.code == "INVALID_WITHDRAWAL_AMOUNT"
    assert "3500 XOF" in failure.value.message
    assert failure.value.details == {"minimum_amount": 3500, "currency": "XOF"}
    service.payment_repo.get_or_create_wallet.assert_not_awaited()
