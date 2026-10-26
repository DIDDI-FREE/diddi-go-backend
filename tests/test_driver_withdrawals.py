import re
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app_base.core.database import async_session_factory
from app_base.main import app
from app_base.modules.payment.domain.entities import (
    DriverLedgerEntry,
    WalletEntryDirection,
    WalletEntryStatus,
    WalletEntryType,
)
from app_base.modules.payment.infra.repositories import SqlAlchemyPaymentRepository


class PayoutGateway:
    def __init__(self, status: str = "succeeded") -> None:
        self.status = status
        self.created: dict | None = None
        self.idempotency_key: str | None = None

    async def create_payout(self, payload, *, idempotency_key):
        self.created = payload
        self.idempotency_key = idempotency_key
        return {
            "id": str(uuid4()),
            **payload,
            "status": self.status,
            "failure_code": "provider_rejected" if self.status == "failed" else None,
        }


class SmsCapture:
    """Captures the transaction OTP without ever persisting a plaintext code."""

    def __init__(self) -> None:
        self.code: str | None = None

    async def send(self, *, recipient, message, idempotency_key):
        match = re.search(r"(\d{6})", message)
        assert match is not None
        self.code = match.group(1)

    async def close(self) -> None:
        return None


async def _verified_withdrawal_payload(client, driver: dict[str, str], quote_id: str, destination: dict) -> dict:
    sms = SmsCapture()
    app.state.sms_provider = sms
    verification = await client.post(
        "/v1/drivers/me/wallet/withdrawals/verification/request",
        json={"beneficiary_destination": destination},
        headers=driver,
    )
    assert verification.status_code == 200, verification.text
    assert sms.code is not None
    return {
        "quote_id": quote_id,
        "beneficiary_reference": "driver:test",
        "beneficiary_destination": destination,
        "verification_id": verification.json()["verification_id"],
        "verification_code": sms.code,
    }


async def _credit_wallet(driver_id: UUID, amount: int) -> None:
    async with async_session_factory() as session:
        repo = SqlAlchemyPaymentRepository(session)
        await repo.record_ledger_entry_once(
            DriverLedgerEntry(
                id=uuid4(),
                driver_id=driver_id,
                amount=Decimal(amount),
                currency="XOF",
                direction=WalletEntryDirection.CREDIT,
                entry_type=WalletEntryType.ADJUSTMENT,
                status=WalletEntryStatus.CONFIRMED,
                reference_type="withdrawal_test",
                reference_id=uuid4(),
                created_at=datetime.now(UTC),
            )
        )
        await session.commit()


@pytest.mark.asyncio
async def test_driver_withdrawal_succeeds_without_double_debit(client, driver) -> None:
    wallet = (await client.get("/v1/drivers/me/wallet", headers=driver)).json()
    driver_id = UUID(wallet["driver_id"])
    await _credit_wallet(driver_id, 5_000)
    gateway = PayoutGateway("succeeded")
    app.state.diddipay = gateway

    quote = await client.post(
        "/v1/drivers/me/wallet/withdrawals/quote",
        json={"amount": 5_000},
        headers=driver,
    )
    assert quote.status_code == 200, quote.text
    destination = {"type": "mobile_money", "phone": "+2250700000000", "network": "mtn"}
    response = await client.post(
        "/v1/drivers/me/wallet/withdrawals",
        json=await _verified_withdrawal_payload(client, driver, quote.json()["quote_id"], destination),
        headers=driver,
    )

    assert response.status_code == 201, response.text
    assert response.json()["status"] == "succeeded"
    assert response.json()["net_amount"] == 5_000
    assert gateway.created["amount"] == 5_000
    assert gateway.created["beneficiary_destination"] == destination
    assert response.json()["beneficiary_destination"] == gateway.created["beneficiary_destination"]
    wallet = (await client.get("/v1/drivers/me/wallet", headers=driver)).json()
    assert wallet["balance"] == 0


@pytest.mark.asyncio
async def test_failed_withdrawal_releases_reserved_balance(client, driver) -> None:
    wallet = (await client.get("/v1/drivers/me/wallet", headers=driver)).json()
    driver_id = UUID(wallet["driver_id"])
    await _credit_wallet(driver_id, 5_000)
    app.state.diddipay = PayoutGateway("failed")

    quote = await client.post(
        "/v1/drivers/me/wallet/withdrawals/quote",
        json={"amount": 2_000},
        headers=driver,
    )
    destination = {"type": "mobile_money", "phone": "+2250700000000", "network": "orange"}
    response = await client.post(
        "/v1/drivers/me/wallet/withdrawals",
        json=await _verified_withdrawal_payload(client, driver, quote.json()["quote_id"], destination),
        headers=driver,
    )

    assert response.status_code == 201, response.text
    assert response.json()["status"] == "released"
    wallet = (await client.get("/v1/drivers/me/wallet", headers=driver)).json()
    assert wallet["balance"] == 5_000


@pytest.mark.asyncio
async def test_withdrawal_quote_rejects_insufficient_balance(client, driver) -> None:
    response = await client.post(
        "/v1/drivers/me/wallet/withdrawals/quote",
        json={"amount": 2_000},
        headers=driver,
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "WITHDRAWAL_BALANCE_INSUFFICIENT"


@pytest.mark.asyncio
async def test_processing_withdrawal_exposes_available_and_reserved_balances(client, driver) -> None:
    wallet = (await client.get("/v1/drivers/me/wallet", headers=driver)).json()
    driver_id = UUID(wallet["driver_id"])
    await _credit_wallet(driver_id, 5_000)
    app.state.diddipay = PayoutGateway("processing")
    quote = await client.post(
        "/v1/drivers/me/wallet/withdrawals/quote",
        json={"amount": 2_000},
        headers=driver,
    )

    destination = {"type": "mobile_money", "phone": "+2250700000000", "network": "moov"}
    response = await client.post(
        "/v1/drivers/me/wallet/withdrawals",
        json=await _verified_withdrawal_payload(client, driver, quote.json()["quote_id"], destination),
        headers=driver,
    )
    wallet = (await client.get("/v1/drivers/me/wallet", headers=driver)).json()

    assert response.json()["status"] == "processing"
    assert wallet["balance"] == 3_000
    assert wallet["available_balance"] == 3_000
    assert wallet["reserved_balance"] == 2_000
    assert wallet["total_balance"] == 5_000


@pytest.mark.asyncio
async def test_replaying_consumed_quote_returns_same_withdrawal_without_double_debit(client, driver) -> None:
    wallet = (await client.get("/v1/drivers/me/wallet", headers=driver)).json()
    driver_id = UUID(wallet["driver_id"])
    await _credit_wallet(driver_id, 5_000)
    app.state.diddipay = PayoutGateway("succeeded")
    quote = await client.post(
        "/v1/drivers/me/wallet/withdrawals/quote",
        json={"amount": 2_000},
        headers=driver,
    )
    destination = {"type": "mobile_money", "phone": "+2250700000000", "network": "mtn"}
    payload = await _verified_withdrawal_payload(client, driver, quote.json()["quote_id"], destination)

    first = await client.post("/v1/drivers/me/wallet/withdrawals", json=payload, headers=driver)
    replay = await client.post("/v1/drivers/me/wallet/withdrawals", json=payload, headers=driver)
    wallet = (await client.get("/v1/drivers/me/wallet", headers=driver)).json()

    assert replay.status_code == 201
    assert replay.json()["id"] == first.json()["id"]
    assert replay.json()["beneficiary_destination"] == payload["beneficiary_destination"]
    assert wallet["balance"] == 3_000


@pytest.mark.asyncio
async def test_withdrawal_requires_a_valid_mobile_money_destination(client, driver) -> None:
    wallet = (await client.get("/v1/drivers/me/wallet", headers=driver)).json()
    await _credit_wallet(UUID(wallet["driver_id"]), 2_000)
    quote = await client.post(
        "/v1/drivers/me/wallet/withdrawals/quote",
        json={"amount": 2_000},
        headers=driver,
    )

    missing = await client.post(
        "/v1/drivers/me/wallet/withdrawals",
        json={"quote_id": quote.json()["quote_id"], "beneficiary_reference": "driver:test"},
        headers=driver,
    )
    invalid_phone = await client.post(
        "/v1/drivers/me/wallet/withdrawals",
        json={
            "quote_id": quote.json()["quote_id"],
            "beneficiary_reference": "driver:test",
            "beneficiary_destination": {
                "type": "mobile_money",
                "phone": "0700000000",
                "network": "mtn",
            },
        },
        headers=driver,
    )

    assert missing.status_code == 422
    assert invalid_phone.status_code == 422
