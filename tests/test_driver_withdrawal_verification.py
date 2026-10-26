from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app_base.modules.payment.application import wallet_service as wallet_service_module
from app_base.modules.payment.application.wallet_service import DriverWalletService


class _DriverRepository:
    def __init__(self, driver_id):
        self.driver_id = driver_id

    async def find_by_user_id(self, user_id):
        return SimpleNamespace(id=self.driver_id)


class _PaymentRepository:
    def __init__(self) -> None:
        self.saved = None
        self.commits = 0

    async def find_latest_withdrawal_verification(self, driver_id):
        return None

    async def save_withdrawal_verification(self, verification):
        self.saved = verification
        return verification

    async def commit(self):
        self.commits += 1


class _SmsProvider:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def send(self, **kwargs):
        self.calls.append(kwargs)

    async def close(self) -> None:
        return None


@pytest.mark.asyncio
async def test_withdrawal_otp_is_sent_to_profile_phone_and_binds_destination(monkeypatch) -> None:
    driver_id = uuid4()
    payment_repo = _PaymentRepository()
    sms = _SmsProvider()
    service = DriverWalletService(
        payment_repo=payment_repo,
        driver_repo=_DriverRepository(driver_id),
        sms=sms,
    )
    monkeypatch.setattr(wallet_service_module, "randbelow", lambda _: 123456)
    destination = {"type": "mobile_money", "phone": "+2250700000000", "network": "wave"}

    result = await service.request_withdrawal_verification(
        driver_user_id=uuid4(),
        profile_phone="+2250102030405",
        beneficiary_destination=destination,
    )

    assert payment_repo.saved.driver_id == driver_id
    assert payment_repo.saved.beneficiary_destination == destination
    assert payment_repo.saved.recipient_phone == "+2250102030405"
    assert payment_repo.saved.code_hash != "123456"
    assert payment_repo.saved.created_at is not None
    assert payment_repo.saved.created_at <= datetime.now(UTC)
    assert payment_repo.commits == 1
    assert sms.calls[0]["recipient"] == "+2250102030405"
    assert "123456" in sms.calls[0]["message"]
    assert result["recipient_phone_masked"].endswith("0405")
