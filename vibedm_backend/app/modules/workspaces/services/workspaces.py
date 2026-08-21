from __future__ import annotations

from uuid import UUID

from app.core.errors import ApiError
from app.deps import CurrentUser, WorkspaceContext
from app.modules.workspaces.repositories.workspaces import WorkspaceRepository
from app.modules.workspaces.schemas.workspaces import (
    MemberInviteRequest,
    WorkspaceMemberResponse,
    WorkspaceResponse,
)


class WorkspaceService:
    def __init__(self, repository: WorkspaceRepository) -> None:
        self.repository = repository

    async def list_workspaces(self, user: CurrentUser) -> list[WorkspaceResponse]:
        return [WorkspaceResponse(**row) for row in await self.repository.list_for_user(user.id)]

    async def get_workspace(self, workspace: WorkspaceContext) -> WorkspaceResponse:
        row = await self.repository.get(workspace.id)
        if row is None:
            raise ApiError(
                status_code=404, code="workspace_not_found", message="Workspace not found"
            )
        return WorkspaceResponse(**row, role=workspace.role, active=True)

    async def update_workspace(self, workspace: WorkspaceContext, name: str) -> WorkspaceResponse:
        if not workspace.is_admin:
            raise ApiError(status_code=403, code="forbidden", message="Admin role required")
        row = await self.repository.update_name(workspace.id, name)
        if row is None:
            raise ApiError(
                status_code=404, code="workspace_not_found", message="Workspace not found"
            )
        return WorkspaceResponse(**row, role=workspace.role, active=True)

    async def activate_workspace(
        self, user: CurrentUser, workspace: WorkspaceContext
    ) -> dict[str, bool]:
        await self.repository.activate(user.id, workspace.id)
        return {"active": True}

    async def delete_workspace(self, workspace: WorkspaceContext) -> dict[str, bool]:
        if not workspace.is_owner:
            raise ApiError(status_code=403, code="forbidden", message="Owner role required")
        await self.repository.soft_delete(workspace.id)
        return {"deleted": True}

    async def list_members(self, workspace: WorkspaceContext) -> list[WorkspaceMemberResponse]:
        if not workspace.is_admin:
            raise ApiError(status_code=403, code="forbidden", message="Admin role required")
        return [
            WorkspaceMemberResponse(**row)
            for row in await self.repository.list_members(workspace.id)
        ]

    async def invite_member(
        self, workspace: WorkspaceContext, request: MemberInviteRequest
    ) -> dict[str, str]:
        if not workspace.is_admin:
            raise ApiError(status_code=403, code="forbidden", message="Admin role required")
        return {"status": "invited", "email": request.email, "role": request.role}

    async def update_member(
        self, workspace: WorkspaceContext, user_id: UUID, role: str
    ) -> WorkspaceMemberResponse:
        if not workspace.is_admin:
            raise ApiError(status_code=403, code="forbidden", message="Admin role required")
        row = await self.repository.update_member_role(workspace.id, user_id, role)
        if row is None:
            raise ApiError(status_code=404, code="member_not_found", message="Member not found")
        return WorkspaceMemberResponse(**row)

    async def remove_member(self, workspace: WorkspaceContext, user_id: UUID) -> dict[str, bool]:
        if not workspace.is_admin:
            raise ApiError(status_code=403, code="forbidden", message="Admin role required")
        await self.repository.remove_member(workspace.id, user_id)
        return {"removed": True}
