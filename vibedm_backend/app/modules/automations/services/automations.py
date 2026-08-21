from __future__ import annotations

from uuid import UUID

from app.core.errors import ApiError
from app.deps import CurrentUser, WorkspaceContext
from app.modules.automations.repositories.automations import AutomationRepository
from app.modules.automations.schemas.automations import (
    AutomationCreateRequest,
    AutomationDetail,
    AutomationRunResponse,
    AutomationSummary,
    AutomationUpdateRequest,
    TestTriggerRequest,
)


def validate_activation(automation: AutomationDetail) -> None:
    missing: list[str] = []
    if automation.trigger_type is None:
        missing.append("trigger_type")

    if not automation.trigger_config:
        missing.append("trigger_config")
    elif automation.trigger_type == "comment_post":
        if not automation.trigger_config.get("post_id") or not automation.trigger_config.get(
            "keywords"
        ):
            missing.append("trigger_config")
    elif automation.trigger_type == "dm":
        if not automation.trigger_config.get("keywords"):
            missing.append("trigger_config")

    if not automation.steps:
        missing.append("steps")

    if missing:
        raise ApiError(
            status_code=422,
            code="automation_incomplete",
            message="Automation is incomplete",
            details={"missing": missing},
        )


class AutomationService:
    def __init__(self, repository: AutomationRepository) -> None:
        self.repository = repository

    async def list_automations(
        self,
        workspace: WorkspaceContext,
        status: str | None,
        trigger_type: str | None,
        q: str | None,
    ) -> list[AutomationSummary]:
        rows = await self.repository.list_automations(
            workspace_id=workspace.id, status=status, trigger_type=trigger_type, q=q
        )
        return [AutomationSummary(**row) for row in rows]

    async def create(
        self, workspace: WorkspaceContext, user: CurrentUser, request: AutomationCreateRequest
    ) -> AutomationDetail:
        if not workspace.is_admin:
            raise ApiError(status_code=403, code="forbidden", message="Admin role required")
        row = await self.repository.create(
            workspace_id=workspace.id,
            user_id=user.id,
            name=request.name,
            trigger_type=request.trigger_type,
        )
        return AutomationDetail(**row, steps=[])

    async def get(self, workspace: WorkspaceContext, automation_id: UUID) -> AutomationDetail:
        row = await self.repository.get_detail(
            workspace_id=workspace.id, automation_id=automation_id
        )
        if row is None:
            raise ApiError(
                status_code=404, code="automation_not_found", message="Automation not found"
            )
        return AutomationDetail(**row)

    async def update(
        self, workspace: WorkspaceContext, automation_id: UUID, request: AutomationUpdateRequest
    ) -> AutomationDetail:
        if not workspace.is_admin:
            raise ApiError(status_code=403, code="forbidden", message="Admin role required")
        row = await self.repository.replace(
            workspace_id=workspace.id,
            automation_id=automation_id,
            data=request.model_dump(exclude_unset=True),
        )
        if row is None:
            raise ApiError(
                status_code=404, code="automation_not_found", message="Automation not found"
            )
        return AutomationDetail(**row)

    async def activate(self, workspace: WorkspaceContext, automation_id: UUID) -> AutomationDetail:
        automation = await self.get(workspace, automation_id)
        validate_activation(automation)
        row = await self.repository.set_status(
            workspace_id=workspace.id, automation_id=automation_id, status="active"
        )
        if row is None:
            raise ApiError(
                status_code=404, code="automation_not_found", message="Automation not found"
            )
        return AutomationDetail(**row)

    async def deactivate(
        self, workspace: WorkspaceContext, automation_id: UUID
    ) -> AutomationDetail:
        row = await self.repository.set_status(
            workspace_id=workspace.id, automation_id=automation_id, status="inactive"
        )
        if row is None:
            raise ApiError(
                status_code=404, code="automation_not_found", message="Automation not found"
            )
        return AutomationDetail(**row)

    async def delete(self, workspace: WorkspaceContext, automation_id: UUID) -> dict[str, bool]:
        if not workspace.is_admin:
            raise ApiError(status_code=403, code="forbidden", message="Admin role required")
        await self.repository.delete(workspace_id=workspace.id, automation_id=automation_id)
        return {"deleted": True}

    async def test_trigger(
        self, workspace: WorkspaceContext, automation_id: UUID, request: TestTriggerRequest
    ) -> AutomationRunResponse:
        await self.get(workspace, automation_id)
        row = await self.repository.create_run(
            workspace_id=workspace.id, automation_id=automation_id, event=request.event
        )
        return AutomationRunResponse(**row)

    async def list_runs(
        self, workspace: WorkspaceContext, automation_id: UUID
    ) -> list[AutomationRunResponse]:
        rows = await self.repository.list_runs(
            workspace_id=workspace.id, automation_id=automation_id
        )
        return [AutomationRunResponse(**row) for row in rows]
