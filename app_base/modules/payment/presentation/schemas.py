"""Pydantic request/response schemas for the payment endpoints.

Shape matches the API contract (`DiddiGo_Contrat_API.md` §3):
  - `CashConfirmationRequest.amount_collected` is an integer (XOF has no
    sub-unit). The domain service handles Decimal conversion.
"""

from pydantic import BaseModel, Field


class CashConfirmationRequest(BaseModel):
    amount_collected: int = Field(ge=0)


class PaymentPreparationRequest(BaseModel):
    method: str = Field(default="cash")
    customer_email: str | None = Field(default=None, min_length=3, max_length=255)
    customer_phone: str | None = Field(default=None, min_length=4, max_length=32)
    callback_url: str | None = Field(default=None, min_length=1, max_length=1000)


class DriverTopupRequest(BaseModel):
    amount: int = Field(gt=0)
    method: str = Field(default="diddipay")
    customer_email: str = Field(min_length=3, max_length=255)
    customer_phone: str | None = Field(default=None, min_length=4, max_length=32)
    callback_url: str | None = Field(default=None, min_length=1, max_length=1000)
