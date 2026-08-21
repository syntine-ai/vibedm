from __future__ import annotations

import csv
import io
from uuid import UUID

from app.core.errors import ApiError
from app.deps import WorkspaceContext
from app.modules.contacts.repositories.contacts import ContactRepository
from app.modules.contacts.schemas.contacts import (
    ContactCreateRequest,
    ContactResponse,
    ContactUpdateRequest,
)


class ContactService:
    def __init__(self, repository: ContactRepository) -> None:
        self.repository = repository

    async def list_contacts(
        self,
        workspace: WorkspaceContext,
        q: str | None,
        source_automation_id: UUID | None,
        tag: str | None,
    ) -> list[ContactResponse]:
        rows = await self.repository.list(
            workspace_id=workspace.id, q=q, source_automation_id=source_automation_id, tag=tag
        )
        return [ContactResponse(**row) for row in rows]

    async def get_contact(self, workspace: WorkspaceContext, contact_id: UUID) -> ContactResponse:
        row = await self.repository.get(workspace_id=workspace.id, contact_id=contact_id)
        if row is None:
            raise ApiError(status_code=404, code="contact_not_found", message="Contact not found")
        return ContactResponse(**row)

    async def create_contact(
        self, workspace: WorkspaceContext, request: ContactCreateRequest
    ) -> ContactResponse:
        if not workspace.is_admin:
            raise ApiError(status_code=403, code="forbidden", message="Admin role required")
        row = await self.repository.create(
            workspace_id=workspace.id,
            data=request.model_dump(),
        )
        return ContactResponse(**row)

    async def update_contact(
        self, workspace: WorkspaceContext, contact_id: UUID, request: ContactUpdateRequest
    ) -> ContactResponse:
        if not workspace.is_admin:
            raise ApiError(status_code=403, code="forbidden", message="Admin role required")
        row = await self.repository.update(
            workspace_id=workspace.id,
            contact_id=contact_id,
            data=request.model_dump(exclude_unset=True),
        )
        if row is None:
            raise ApiError(status_code=404, code="contact_not_found", message="Contact not found")
        return ContactResponse(**row)

    async def delete_contact(
        self, workspace: WorkspaceContext, contact_id: UUID
    ) -> dict[str, bool]:
        if not workspace.is_admin:
            raise ApiError(status_code=403, code="forbidden", message="Admin role required")
        await self.repository.delete(workspace_id=workspace.id, contact_id=contact_id)
        return {"deleted": True}

    @staticmethod
    def to_csv(contacts: list[ContactResponse]) -> str:
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["id", "ig_username", "name", "email", "phone", "tags", "notes"],
        )
        writer.writeheader()
        for contact in contacts:
            writer.writerow(
                {
                    "id": str(contact.id),
                    "ig_username": contact.ig_username or "",
                    "name": contact.name or "",
                    "email": contact.email or "",
                    "phone": contact.phone or "",
                    "tags": ",".join(contact.tags),
                    "notes": contact.notes or "",
                }
            )
        return output.getvalue()
