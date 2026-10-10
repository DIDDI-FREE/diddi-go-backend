"""Pydantic request/response schemas for the payment endpoints.

Shape matches the API contract (`DiddiGo_Contrat_API.md` §3):
  - `CashConfirmationRequest.amount_collected` is an integer (XOF has no
    sub-unit). The domain service handles Decimal conversion.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CashConfirmationRequest(BaseModel):
    amount_collected: int = Field(ge=0)


class PaymentPreparationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: str = Field(default="cash")
    customer_email: str | None = Field(default=None, min_length=3, max_length=255)
    customer_phone: str | None = Field(default=None, min_length=4, max_length=32)


class DriverTopupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: int = Field(gt=0)
    method: str = Field(default="diddipay")
    customer_email: str = Field(min_length=3, max_length=255)
    customer_phone: str | None = Field(default=None, min_length=4, max_length=32)


class DriverWithdrawalQuoteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: int = Field(gt=0)


class DriverWithdrawalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quote_id: UUID
    beneficiary_reference: str = Field(min_length=1, max_length=128)


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
