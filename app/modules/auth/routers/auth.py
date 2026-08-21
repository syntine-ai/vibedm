from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import CurrentUser, get_current_user
from app.modules.auth.repositories.auth import AuthRepository
from app.modules.auth.schemas.auth import AuthMeResponse, UserProfile
from app.modules.auth.services.auth import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def get_auth_service(session: Annotated[AsyncSession, Depends(get_session)]) -> AuthService:
    return AuthService(AuthRepository(session))


@router.post("/sync", response_model=UserProfile)
async def sync_auth_user(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserProfile:
    return await service.sync_user(user)


@router.get("/me", response_model=AuthMeResponse)
async def get_me(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthMeResponse:
    return await service.get_me(user)


@router.post("/logout")
async def logout(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> dict[str, bool]:
    return await service.logout(user)
