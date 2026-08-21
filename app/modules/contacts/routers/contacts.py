from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import WorkspaceContext, get_workspace_context
from app.modules.contacts.repositories.contacts import ContactRepository
from app.modules.contacts.schemas.contacts import (
    ContactCreateRequest,
    ContactResponse,
    ContactUpdateRequest,
)
from app.modules.contacts.services.contacts import ContactService

router = APIRouter(prefix="/api/v1/contacts", tags=["contacts"])


def get_contact_service(session: Annotated[AsyncSession, Depends(get_session)]) -> ContactService:
    return ContactService(ContactRepository(session))


@router.get("", response_model=list[ContactResponse])
async def list_contacts(
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[ContactService, Depends(get_contact_service)],
    q: str | None = None,
    source_automation_id: UUID | None = None,
    tag: str | None = None,
) -> list[ContactResponse]:
    return await service.list_contacts(workspace, q, source_automation_id, tag)


@router.get("/export.csv")
async def export_contacts(
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[ContactService, Depends(get_contact_service)],
) -> Response:
    contacts = await service.list_contacts(workspace, None, None, None)
    return Response(
        content=service.to_csv(contacts),
        media_type="text/csv",
        headers={"content-disposition": 'attachment; filename="contacts.csv"'},
    )


@router.post("/import")
async def import_contacts(file: UploadFile) -> dict[str, object]:
    await file.read()
    return {"imported": 0, "skipped": 0, "errors": []}


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: UUID,
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[ContactService, Depends(get_contact_service)],
) -> ContactResponse:
    return await service.get_contact(workspace, contact_id)


@router.post("", response_model=ContactResponse, status_code=201)
async def create_contact(
    request: ContactCreateRequest,
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[ContactService, Depends(get_contact_service)],
) -> ContactResponse:
    return await service.create_contact(workspace, request)


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: UUID,
    request: ContactUpdateRequest,
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[ContactService, Depends(get_contact_service)],
) -> ContactResponse:
    return await service.update_contact(workspace, contact_id, request)


@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: UUID,
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[ContactService, Depends(get_contact_service)],
) -> dict[str, bool]:
    return await service.delete_contact(workspace, contact_id)
