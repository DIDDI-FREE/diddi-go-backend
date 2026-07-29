"""Pydantic request/response schemas for the payment endpoints.

Shape matches the API contract (`DiddiGo_Contrat_API.md` §3):
  - `CashConfirmationRequest.amount_collected` is an integer (XOF has no
    sub-unit). The domain service handles Decimal conversion.
"""

from pydantic import BaseModel, Field


class CashConfirmationRequest(BaseModel):
    amount_collected: int = Field(ge=0)
