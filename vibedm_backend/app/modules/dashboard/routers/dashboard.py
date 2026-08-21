from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import WorkspaceContext, get_workspace_context
from app.modules.dashboard.repositories.dashboard import DashboardRepository
from app.modules.dashboard.schemas.dashboard import (
    ActivityResponse,
    DashboardStatsResponse,
    UsageResponse,
)
from app.modules.dashboard.services.dashboard import DashboardService

router = APIRouter(tags=["dashboard"])
dashboard_router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])
usage_router = APIRouter(prefix="/api/v1", tags=["dashboard"])


def get_dashboard_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DashboardService:
    return DashboardService(DashboardRepository(session))


@dashboard_router.get("/stats", response_model=DashboardStatsResponse)
async def stats(
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> DashboardStatsResponse:
    return await service.stats(workspace)


@dashboard_router.get("/recent-activity", response_model=list[ActivityResponse])
async def recent_activity(
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> list[ActivityResponse]:
    return await service.recent_activity(workspace)


@usage_router.get("/usage", response_model=UsageResponse)
async def usage(
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> UsageResponse:
    return await service.usage(workspace)


router.include_router(dashboard_router)
router.include_router(usage_router)
