from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

BillingCycle = Literal["monthly", "yearly"]


class PlanResponse(BaseModel):
    id: str
    tier: str
    display_name: str
    monthly_paise: int
    yearly_paise: int
    features: list[str]
    is_popular: bool = False


class SubscriptionResponse(BaseModel):
    id: UUID | None = None
    workspace_id: UUID
    plan_id: str
    cycle: str
    status: str
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool = False
    provider: str | None = None


class CheckoutRequest(BaseModel):
    plan_id: str
    cycle: BillingCycle = "monthly"


class CheckoutResponse(BaseModel):
    activated: bool = False
    checkout_url: str | None = None


class PortalResponse(BaseModel):
    portal_url: str


class InvoiceResponse(BaseModel):
    id: UUID
    amount_paise: int
    currency: str
    status: str
    hosted_invoice_url: str | None = None
    pdf_url: str | None = None
    issued_at: datetime
