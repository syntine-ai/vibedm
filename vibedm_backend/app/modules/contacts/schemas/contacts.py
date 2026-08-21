from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class ContactCreateRequest(BaseModel):
    ig_user_id: str | None = None
    ig_username: str | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    source_automation_id: UUID | None = None
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None


class ContactUpdateRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    notes: str | None = None
    tags: list[str] | None = None


class ContactResponse(ContactCreateRequest):
    id: UUID
    workspace_id: UUID
