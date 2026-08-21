from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class WorkspaceResponse(BaseModel):
    id: UUID
    name: str
    owner_id: UUID | None = None
    avatar_url: str | None = None
    role: str | None = None
    ig_username: str | None = None
    plan: str = "free"
    active: bool = False


class WorkspaceUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class MemberInviteRequest(BaseModel):
    email: str
    role: str = "member"


class MemberUpdateRequest(BaseModel):
    role: str


class WorkspaceMemberResponse(BaseModel):
    workspace_id: UUID
    user_id: UUID
    email: str | None = None
    role: str
    active: bool
