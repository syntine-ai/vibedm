from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import WorkspaceContext, get_workspace_context
from app.modules.billing.repositories.billing import BillingRepository
from app.modules.billing.schemas.billing import (
    CheckoutRequest,
    CheckoutResponse,
    InvoiceResponse,
    PlanResponse,
    PortalResponse,
    SubscriptionResponse,
)
from app.modules.billing.services.billing import BillingService

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


def get_billing_service(session: Annotated[AsyncSession, Depends(get_session)]) -> BillingService:
    return BillingService(BillingRepository(session))


@router.get("/plans", response_model=list[PlanResponse])
async def plans(
    service: Annotated[BillingService, Depends(get_billing_service)],
) -> list[PlanResponse]:
    return await service.list_plans()


@router.get("/subscription", response_model=SubscriptionResponse)
async def subscription(
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[BillingService, Depends(get_billing_service)],
) -> SubscriptionResponse:
    return await service.subscription(workspace)


@router.post("/checkout", response_model=CheckoutResponse)
async def checkout(
    request: CheckoutRequest,
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[BillingService, Depends(get_billing_service)],
) -> CheckoutResponse:
    return await service.checkout(workspace, request)


@router.post("/portal", response_model=PortalResponse)
async def portal(
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[BillingService, Depends(get_billing_service)],
) -> PortalResponse:
    return await service.portal(workspace)


@router.post("/cancel")
async def cancel(
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[BillingService, Depends(get_billing_service)],
) -> dict[str, bool]:
    return await service.cancel(workspace)


@router.get("/invoices", response_model=list[InvoiceResponse])
async def invoices(
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[BillingService, Depends(get_billing_service)],
) -> list[InvoiceResponse]:
    return await service.invoices(workspace)


@router.get("/invoices/{invoice_id}.pdf")
async def invoice_pdf(
    invoice_id: UUID,
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[BillingService, Depends(get_billing_service)],
) -> RedirectResponse:
    return RedirectResponse(await service.invoice_pdf(workspace, invoice_id))
