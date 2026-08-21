from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.core.errors import ApiError
from app.db import get_session
from app.security import decode_supabase_jwt, parse_uuid_claim

bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    id: UUID
    email: str
    claims: dict[str, Any]


class WorkspaceContext(BaseModel):
    id: UUID
    role: str = "member"

    @property
    def is_admin(self) -> bool:
        return self.role in {"owner", "admin"}

    @property
    def is_owner(self) -> bool:
        return self.role == "owner"


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CurrentUser:
    if credentials is None:
        raise ApiError(status_code=401, code="unauthorized", message="Missing bearer token")

    payload = decode_supabase_jwt(credentials.credentials, settings)
    user_id = parse_uuid_claim(payload.get("sub"), "sub")
    return CurrentUser(id=user_id, email=str(payload.get("email") or ""), claims=payload)


async def get_workspace_id(
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> UUID:
    if not x_workspace_id:
        raise ApiError(
            status_code=400,
            code="workspace_required",
            message="X-Workspace-Id header is required",
        )
    try:
        return UUID(x_workspace_id)
    except ValueError as exc:
        raise ApiError(
            status_code=400,
            code="invalid_workspace",
            message="X-Workspace-Id must be a UUID",
        ) from exc


async def get_workspace_context(
    workspace_id: Annotated[UUID, Depends(get_workspace_id)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WorkspaceContext:
    result = await session.execute(
        text(
            """
            select role::text as role
            from public.workspace_members
            where workspace_id = :workspace_id and user_id = :user_id
            """
        ),
        {"workspace_id": workspace_id, "user_id": user.id},
    )
    row = result.mappings().first()
    if row is None:
        raise ApiError(
            status_code=403,
            code="workspace_forbidden",
            message="User is not a member of this workspace",
        )
    return WorkspaceContext(id=workspace_id, role=row["role"])
