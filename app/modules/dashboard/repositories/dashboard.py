from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class DashboardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def usage(self, workspace_id: UUID) -> dict:
        result = await self.session.execute(
            text(
                """
                select dm_count, contact_count
                from public.usage_counters
                where workspace_id = :workspace_id
                order by period_start desc
                limit 1
                """
            ),
            {"workspace_id": workspace_id},
        )
        row = result.mappings().first()
        return dict(row) if row else {"dm_count": 0, "contact_count": 0}

    async def active_automation_count(self, workspace_id: UUID) -> int:
        result = await self.session.execute(
            text(
                """
                select count(*) as count
                from public.automations
                where workspace_id = :workspace_id and status = 'active' and deleted_at is null
                """
            ),
            {"workspace_id": workspace_id},
        )
        return int(result.mappings().one()["count"])

    async def recent_activity(self, workspace_id: UUID) -> list[dict]:
        result = await self.session.execute(
            text(
                """
                select id::text, 'automation_run' as type, created_at, status::text as label
                from public.automation_runs
                where workspace_id = :workspace_id
                union all
                select id::text, 'contact' as type, created_at,
                       coalesce(ig_username::text, name, 'contact') as label
                from public.contacts
                where workspace_id = :workspace_id
                order by created_at desc
                limit 25
                """
            ),
            {"workspace_id": workspace_id},
        )
        return [dict(row) for row in result.mappings().all()]
