from __future__ import annotations

from uuid import UUID

from app.core.errors import ApiError
from app.deps import WorkspaceContext
from app.modules.billing.repositories.billing import BillingRepository
from app.modules.billing.schemas.billing import (
    CheckoutRequest,
    CheckoutResponse,
    InvoiceResponse,
    PlanResponse,
    PortalResponse,
    SubscriptionResponse,
)


class StaticBillingProvider:
    async def create_checkout(self, plan_id: str, cycle: str, workspace_id: UUID) -> str:
        return f"https://billing.example/checkout/{plan_id}/{cycle}"

    async def create_portal(self, workspace_id: UUID) -> str:
        return f"https://billing.example/portal/{workspace_id}"


class BillingService:
    def __init__(
        self,
        repository: BillingRepository,
        provider: StaticBillingProvider | None = None,
    ) -> None:
        self.repository = repository
        self.provider = provider or StaticBillingProvider()

    @staticmethod
    def compute_yearly_paise(monthly_paise: int) -> int:
        return int(monthly_paise * 12 * 0.8)

    async def list_plans(self) -> list[PlanResponse]:
        plans: list[PlanResponse] = []
        for row in await self.repository.list_plans():
            yearly = row.get("yearly_paise")
            plans.append(
                PlanResponse(
                    **row,
                    yearly_paise=yearly
                    if yearly is not None
                    else self.compute_yearly_paise(row["monthly_paise"]),
                )
            )
        return plans

    async def subscription(self, workspace: WorkspaceContext) -> SubscriptionResponse:
        row = await self.repository.get_subscription(workspace.id)
        if row is None:
            return SubscriptionResponse(
                workspace_id=workspace.id, plan_id="free", cycle="monthly", status="active"
            )
        return SubscriptionResponse(**row)

    async def checkout(
        self, workspace: WorkspaceContext, request: CheckoutRequest
    ) -> CheckoutResponse:
        if not workspace.is_admin:
            raise ApiError(status_code=403, code="forbidden", message="Admin role required")
        if request.plan_id == "free":
            await self.repository.activate_free_plan(workspace.id, request.cycle)
            return CheckoutResponse(activated=True)
        checkout_url = await self.provider.create_checkout(
            request.plan_id, request.cycle, workspace.id
        )
        return CheckoutResponse(activated=False, checkout_url=checkout_url)

    async def portal(self, workspace: WorkspaceContext) -> PortalResponse:
        if not workspace.is_admin:
            raise ApiError(status_code=403, code="forbidden", message="Admin role required")
        return PortalResponse(portal_url=await self.provider.create_portal(workspace.id))

    async def cancel(self, workspace: WorkspaceContext) -> dict[str, bool]:
        if not workspace.is_admin:
            raise ApiError(status_code=403, code="forbidden", message="Admin role required")
        await self.repository.schedule_cancel(workspace.id)
        return {"cancel_at_period_end": True}

    async def invoices(self, workspace: WorkspaceContext) -> list[InvoiceResponse]:
        return [InvoiceResponse(**row) for row in await self.repository.list_invoices(workspace.id)]

    async def invoice_pdf(self, workspace: WorkspaceContext, invoice_id: UUID) -> str:
        row = await self.repository.get_invoice(workspace.id, invoice_id)
        if row is None:
            raise ApiError(status_code=404, code="invoice_not_found", message="Invoice not found")
        if not row.get("pdf_url"):
            raise ApiError(
                status_code=404, code="invoice_pdf_not_found", message="Invoice PDF not found"
            )
        return row["pdf_url"]
