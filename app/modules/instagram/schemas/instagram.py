from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class OAuthStartResponse(BaseModel):
    url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    code: str
    state: str


class InstagramProfile(BaseModel):
    ig_user_id: str
    ig_username: str
    access_token: str
    token_expires_at: datetime | None = None
    scopes: list[str] = []


class InstagramWorkspaceResponse(BaseModel):
    workspace: dict
    redirect_to: str = "/dashboard"


class InstagramConnectionResponse(BaseModel):
    workspace_id: UUID
    ig_user_id: str
    ig_username: str
