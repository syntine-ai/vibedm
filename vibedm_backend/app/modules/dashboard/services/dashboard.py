from __future__ import annotations

from app.deps import WorkspaceContext
from app.modules.dashboard.repositories.dashboard import DashboardRepository
from app.modules.dashboard.schemas.dashboard import (
    ActivityResponse,
    DashboardStatsResponse,
    UsageResponse,
)


class DashboardService:
    def __init__(self, repository: DashboardRepository) -> None:
        self.repository = repository

    async def usage(self, workspace: WorkspaceContext) -> UsageResponse:
        usage = await self.repository.usage(workspace.id)
        return UsageResponse(
            dm_count=usage["dm_count"],
            dm_limit=1000,
            contact_count=usage["contact_count"],
            contact_limit=1000,
        )

    async def stats(self, workspace: WorkspaceContext) -> DashboardStatsResponse:
        usage = await self.repository.usage(workspace.id)
        active_automations = await self.repository.active_automation_count(workspace.id)
        return DashboardStatsResponse(
            dms_sent=usage["dm_count"],
            active_automations=active_automations,
            contacts_captured=usage["contact_count"],
            revenue_paise=0,
        )

    async def recent_activity(self, workspace: WorkspaceContext) -> list[ActivityResponse]:
        return [
            ActivityResponse(**row) for row in await self.repository.recent_activity(workspace.id)
        ]
