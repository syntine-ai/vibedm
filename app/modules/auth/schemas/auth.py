from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class UserProfile(BaseModel):
    id: UUID
    email: str
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    avatar_url: str | None = None


class WorkspaceSummary(BaseModel):
    id: UUID
    name: str
    role: str
    ig_username: str | None = None
    plan: str = "free"
    active: bool = False


class AuthMeResponse(BaseModel):
    user: UserProfile
    workspaces: list[WorkspaceSummary]
