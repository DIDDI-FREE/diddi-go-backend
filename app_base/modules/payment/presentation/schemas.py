"""Pydantic request/response schemas for the payment endpoints.

Shape matches the API contract (`DiddiGo_Contrat_API.md` §3):
  - `CashConfirmationRequest.amount_collected` is an integer (XOF has no
    sub-unit). The domain service handles Decimal conversion.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CashConfirmationRequest(BaseModel):
    amount_collected: int = Field(ge=0)


class PaymentPreparationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: Literal["cash", "mobile_money"] = "cash"
    mobile_money_network: Literal["orange", "wave", "mtn"] | None = None
    customer_email: str | None = Field(default=None, min_length=3, max_length=255)
    customer_phone: str | None = Field(default=None, min_length=4, max_length=32)

    @model_validator(mode="after")
    def validate_network(self) -> PaymentPreparationRequest:
        if self.method == "mobile_money" and self.mobile_money_network is None:
            raise ValueError("mobile_money_network is required for mobile_money")
        if self.method == "cash" and self.mobile_money_network is not None:
            raise ValueError("mobile_money_network is only valid for mobile_money")
        return self


class PassengerDebtResponse(BaseModel):
    id: UUID
    ride_id: UUID
    amount: int
    currency: str
    status: Literal["open", "mobile_money_pending", "cash_pending_confirmation", "settled"]
    reason: Literal["mobile_money_failed", "mobile_money_expired"]
    created_at: datetime | None = None
    updated_at: datetime | None = None
    settled_at: datetime | None = None


class PassengerDebtListResponse(BaseModel):
    data: list[PassengerDebtResponse]
    pagination: dict[str, int]


class PaymentNextActionResponse(BaseModel):
    """Action fournisseur que le client doit réaliser, si nécessaire."""

    type: str | None = None
    url: str | None = None


class PassengerDebtPaymentResponse(BaseModel):
    """Projection typée de la tentative DiddiPay créée pour une dette."""

    ride_id: UUID
    status: Literal["pending", "requires_action", "processing", "succeeded", "failed", "cancelled"]
    method: Literal["mobile_money"]
    amount: int
    currency: str
    provider: Literal["diddipay"]
    provider_status: str | None = Field(...)
    payment_intent_id: UUID | None = Field(...)
    business_reference: str | None = Field(...)
    next_action: PaymentNextActionResponse | None = Field(...)
    mobile_money_network: Literal["orange", "wave", "mtn"]
    expires_at: datetime | None = Field(...)


class PassengerDebtPaymentPreparationResponse(BaseModel):
    debt: PassengerDebtResponse
    payment: PassengerDebtPaymentResponse


class DriverTopupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: int = Field(gt=0)
    method: str = Field(default="diddipay")
    customer_email: str = Field(min_length=3, max_length=255)
    customer_phone: str | None = Field(default=None, min_length=4, max_length=32)


class DriverWithdrawalQuoteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: int = Field(gt=0)


class MobileMoneyBeneficiaryDestination(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["mobile_money"] = "mobile_money"
    phone: str = Field(pattern=r"^\+[1-9]\d{7,14}$", max_length=16)
    network: str = Field(min_length=1, max_length=32)


class DriverWithdrawalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quote_id: UUID
    beneficiary_reference: str = Field(min_length=1, max_length=128)
    beneficiary_destination: MobileMoneyBeneficiaryDestination


class DriverWithdrawalQuoteResponse(BaseModel):
    quote_id: UUID
    amount: int
    fees: int
    net_amount: int
    currency: str
    expires_at: datetime


class DriverWithdrawalResponse(BaseModel):
    id: UUID
    driver_id: UUID
    quote_id: UUID
    amount: int
    fees: int
    net_amount: int
    currency: str
    beneficiary_reference: str
    beneficiary_destination: MobileMoneyBeneficiaryDestination | None = None
    status: str
    payout_id: UUID | None = None
    business_reference: str | None = None
    provider_status: str | None = None
    failure_code: str | None = None
    failure_message: str | None = None
    created_at: datetime | None = None
    reserved_at: datetime | None = None
    succeeded_at: datetime | None = None
    released_at: datetime | None = None
