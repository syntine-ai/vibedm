from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import CurrentUser, WorkspaceContext, get_current_user, get_workspace_context
from app.modules.automations.repositories.automations import AutomationRepository
from app.modules.automations.schemas.automations import (
    AutomationCreateRequest,
    AutomationDetail,
    AutomationRunResponse,
    AutomationSummary,
    AutomationUpdateRequest,
    TestTriggerRequest,
)
from app.modules.automations.services.automations import AutomationService

router = APIRouter(prefix="/api/v1/automations", tags=["automations"])


def get_automation_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AutomationService:
    return AutomationService(AutomationRepository(session))


@router.get("", response_model=list[AutomationSummary])
async def list_automations(
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[AutomationService, Depends(get_automation_service)],
    status: str | None = None,
    trigger_type: str | None = None,
    q: str | None = None,
) -> list[AutomationSummary]:
    return await service.list_automations(workspace, status, trigger_type, q)


@router.post("", response_model=AutomationDetail, status_code=201)
async def create_automation(
    request: AutomationCreateRequest,
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[AutomationService, Depends(get_automation_service)],
) -> AutomationDetail:
    return await service.create(workspace, user, request)


@router.get("/{automation_id}", response_model=AutomationDetail)
async def get_automation(
    automation_id: UUID,
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[AutomationService, Depends(get_automation_service)],
) -> AutomationDetail:
    return await service.get(workspace, automation_id)


@router.patch("/{automation_id}", response_model=AutomationDetail)
async def update_automation(
    automation_id: UUID,
    request: AutomationUpdateRequest,
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[AutomationService, Depends(get_automation_service)],
) -> AutomationDetail:
    return await service.update(workspace, automation_id, request)


@router.post("/{automation_id}/activate", response_model=AutomationDetail)
async def activate_automation(
    automation_id: UUID,
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[AutomationService, Depends(get_automation_service)],
) -> AutomationDetail:
    return await service.activate(workspace, automation_id)


@router.post("/{automation_id}/deactivate", response_model=AutomationDetail)
async def deactivate_automation(
    automation_id: UUID,
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[AutomationService, Depends(get_automation_service)],
) -> AutomationDetail:
    return await service.deactivate(workspace, automation_id)


@router.delete("/{automation_id}", status_code=204)
async def delete_automation(
    automation_id: UUID,
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[AutomationService, Depends(get_automation_service)],
) -> Response:
    await service.delete(workspace, automation_id)
    return Response(status_code=204)


@router.post("/{automation_id}/test-trigger", response_model=AutomationRunResponse)
async def test_trigger(
    automation_id: UUID,
    request: TestTriggerRequest,
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[AutomationService, Depends(get_automation_service)],
) -> AutomationRunResponse:
    return await service.test_trigger(workspace, automation_id, request)


@router.get("/{automation_id}/runs", response_model=list[AutomationRunResponse])
async def list_runs(
    automation_id: UUID,
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[AutomationService, Depends(get_automation_service)],
) -> list[AutomationRunResponse]:
    return await service.list_runs(workspace, automation_id)
