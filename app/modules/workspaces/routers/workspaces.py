from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import CurrentUser, WorkspaceContext, get_current_user, get_workspace_context
from app.modules.workspaces.repositories.workspaces import WorkspaceRepository
from app.modules.workspaces.schemas.workspaces import (
    MemberInviteRequest,
    MemberUpdateRequest,
    WorkspaceMemberResponse,
    WorkspaceResponse,
    WorkspaceUpdateRequest,
)
from app.modules.workspaces.services.workspaces import WorkspaceService

router = APIRouter(prefix="/api/v1/workspaces", tags=["workspaces"])


def get_workspace_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WorkspaceService:
    return WorkspaceService(WorkspaceRepository(session))


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
) -> list[WorkspaceResponse]:
    return await service.list_workspaces(user)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
) -> WorkspaceResponse:
    return await service.get_workspace(workspace)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    request: WorkspaceUpdateRequest,
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
) -> WorkspaceResponse:
    return await service.update_workspace(workspace, request.name)


@router.post("/{workspace_id}/activate")
async def activate_workspace(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
) -> dict[str, bool]:
    return await service.activate_workspace(user, workspace)


@router.delete("/{workspace_id}", status_code=204)
async def delete_workspace(
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
) -> Response:
    await service.delete_workspace(workspace)
    return Response(status_code=204)


@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberResponse])
async def list_members(
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
) -> list[WorkspaceMemberResponse]:
    return await service.list_members(workspace)


@router.post("/{workspace_id}/members")
async def invite_member(
    request: MemberInviteRequest,
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
) -> dict[str, str]:
    return await service.invite_member(workspace, request)


@router.patch("/{workspace_id}/members/{user_id}", response_model=WorkspaceMemberResponse)
async def update_member(
    user_id: UUID,
    request: MemberUpdateRequest,
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
) -> WorkspaceMemberResponse:
    return await service.update_member(workspace, user_id, request.role)


@router.delete("/{workspace_id}/members/{user_id}", status_code=204)
async def remove_member(
    user_id: UUID,
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
) -> Response:
    await service.remove_member(workspace, user_id)
    return Response(status_code=204)
