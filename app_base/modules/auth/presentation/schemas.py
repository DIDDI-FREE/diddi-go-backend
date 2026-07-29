"""Pydantic request/response schemas for the auth endpoints.

Shape matches the API contract (`DiddiGo_Contrat_API.md` §1):
  - `RegisterRequest.role` defaults to `"passenger"` if omitted
  - `RegisterRequest.full_name` is optional — a passenger can register
    with just a phone number and add their name later
"""

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    phone: str
    full_name: str | None = None
    role: str = Field(default="passenger")


class OTPRequest(BaseModel):
    phone: str


class OTPVerifyRequest(BaseModel):
    phone: str
    code: str


class RefreshRequest(BaseModel):
    refresh_token: str
