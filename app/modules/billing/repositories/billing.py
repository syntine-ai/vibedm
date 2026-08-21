from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class BillingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_plans(self) -> list[dict]:
        result = await self.session.execute(
            text(
                """
                select id, tier::text as tier, display_name, monthly_paise,
                       features, is_popular
                from public.plans
                order by sort_order asc
                """
            )
        )
        return [dict(row) for row in result.mappings().all()]

    async def get_subscription(self, workspace_id: UUID) -> dict | None:
        result = await self.session.execute(
            text(
                """
                select id, workspace_id, plan_id, cycle::text as cycle, status::text as status,
                       current_period_start, current_period_end, cancel_at_period_end, provider
                from public.subscriptions
                where workspace_id = :workspace_id and status <> 'canceled'
                order by created_at desc
                limit 1
                """
            ),
            {"workspace_id": workspace_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def activate_free_plan(self, workspace_id: UUID, cycle: str) -> None:
        await self.session.execute(
            text(
                """
                update public.subscriptions
                set plan_id = 'free', cycle = :cycle, status = 'active',
                    provider = null, updated_at = now()
                where workspace_id = :workspace_id and status <> 'canceled'
                """
            ),
            {"workspace_id": workspace_id, "cycle": cycle},
        )
        await self.session.commit()

    async def schedule_cancel(self, workspace_id: UUID) -> None:
        await self.session.execute(
            text(
                """
                update public.subscriptions
                set cancel_at_period_end = true, updated_at = now()
                where workspace_id = :workspace_id and status <> 'canceled'
                """
            ),
            {"workspace_id": workspace_id},
        )
        await self.session.commit()

    async def list_invoices(self, workspace_id: UUID) -> list[dict]:
        result = await self.session.execute(
            text(
                """
                select id, amount_paise, currency, status, hosted_invoice_url, pdf_url, issued_at
                from public.invoices
                where workspace_id = :workspace_id
                order by issued_at desc
                """
            ),
            {"workspace_id": workspace_id},
        )
        return [dict(row) for row in result.mappings().all()]

    async def get_invoice(self, workspace_id: UUID, invoice_id: UUID) -> dict | None:
        result = await self.session.execute(
            text(
                """
                select id, amount_paise, currency, status, hosted_invoice_url, pdf_url, issued_at
                from public.invoices
                where workspace_id = :workspace_id and id = :invoice_id
                """
            ),
            {"workspace_id": workspace_id, "invoice_id": invoice_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def apply_provider_subscription_update(self, payload: dict) -> None:
        workspace_id = payload.get("metadata", {}).get("workspace_id")
        if not workspace_id:
            return
        await self.session.execute(
            text(
                """
                update public.subscriptions
                set provider_subscription_id = :provider_subscription_id,
                    provider_customer_id = :provider_customer_id,
                    status = :status,
                    provider = :provider,
                    updated_at = now()
                where workspace_id = :workspace_id and status <> 'canceled'
                """
            ),
            {
                "workspace_id": workspace_id,
                "provider_subscription_id": payload.get("subscription"),
                "provider_customer_id": payload.get("customer"),
                "status": payload.get("status", "active"),
                "provider": payload.get("provider", "stripe"),
            },
        )
        await self.session.commit()
