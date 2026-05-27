from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db import get_session
from app.deps import CurrentUser, WorkspaceContext, get_current_user, get_workspace_context
from app.modules.instagram.repositories.instagram import InstagramRepository
from app.modules.instagram.schemas.instagram import (
    InstagramWorkspaceResponse,
    OAuthCallbackRequest,
    OAuthStartResponse,
)
from app.modules.instagram.services.instagram import InstagramService

router = APIRouter(tags=["instagram"])
instagram_router = APIRouter(prefix="/api/v1/instagram", tags=["instagram"])
workspace_router = APIRouter(prefix="/api/v1/workspaces", tags=["instagram"])


def get_instagram_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> InstagramService:
    return InstagramService(InstagramRepository(session), settings)


@instagram_router.get("/oauth/start", response_model=OAuthStartResponse)
async def start_oauth(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[InstagramService, Depends(get_instagram_service)],
) -> OAuthStartResponse:
    return await service.start_oauth(user)


@instagram_router.post("/oauth/callback", response_model=InstagramWorkspaceResponse)
async def oauth_callback(
    request: OAuthCallbackRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[InstagramService, Depends(get_instagram_service)],
) -> InstagramWorkspaceResponse:
    return await service.complete_oauth(user, request.code, request.state)


@workspace_router.post("/connect-instagram", response_model=InstagramWorkspaceResponse)
async def connect_instagram_from_workspace(
    request: OAuthCallbackRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[InstagramService, Depends(get_instagram_service)],
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
) -> InstagramWorkspaceResponse:
    workspace_id = None
    if x_workspace_id:
        try:
            workspace_id = UUID(x_workspace_id)
        except ValueError:
            pass
    return await service.complete_oauth(user, request.code, request.state, workspace_id=workspace_id)


@instagram_router.delete("/connection")
async def disconnect_instagram(
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[InstagramService, Depends(get_instagram_service)],
) -> dict[str, bool]:
    return await service.disconnect(workspace)


@instagram_router.get("/media")
async def get_instagram_media(
    workspace: Annotated[WorkspaceContext, Depends(get_workspace_context)],
    service: Annotated[InstagramService, Depends(get_instagram_service)],
    limit: int = 10,
    after: str | None = None,
) -> dict:
    return await service.get_media(workspace.id, limit=limit, after=after)



router.include_router(instagram_router)
router.include_router(workspace_router)
