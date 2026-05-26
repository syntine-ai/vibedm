from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.core.errors import ApiError
from app.db import get_session
from app.modules.webhooks.repositories.webhooks import WebhookRepository
from app.modules.webhooks.services.webhooks import WebhookService

router = APIRouter(prefix="/api/public/webhooks", tags=["webhooks"])


def get_webhook_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> WebhookService:
    return WebhookService(WebhookRepository(session), settings)


@router.get("/instagram")
async def verify_instagram(
    settings: Annotated[Settings, Depends(get_settings)],
    mode: Annotated[str | None, Query(alias="hub.mode")] = None,
    token: Annotated[str | None, Query(alias="hub.verify_token")] = None,
    challenge: Annotated[str | None, Query(alias="hub.challenge")] = None,
) -> PlainTextResponse:
    if mode == "subscribe" and token == settings.instagram_verify_token and challenge:
        return PlainTextResponse(content=challenge)
    raise ApiError(
        status_code=403, code="verification_failed", message="Webhook verification failed"
    )


@router.post("/instagram")
async def instagram_webhook(
    request: Request,
    service: Annotated[WebhookService, Depends(get_webhook_service)],
    signature: Annotated[str | None, Header(alias="X-Hub-Signature-256")] = None,
) -> dict[str, bool]:
    return await service.handle_instagram(await request.body(), signature)


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    service: Annotated[WebhookService, Depends(get_webhook_service)],
    signature: Annotated[str | None, Header(alias="Stripe-Signature")] = None,
) -> dict[str, bool]:
    return await service.handle_stripe(await request.body(), signature)


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    service: Annotated[WebhookService, Depends(get_webhook_service)],
    signature: Annotated[str | None, Header(alias="X-Razorpay-Signature")] = None,
) -> dict[str, bool]:
    return await service.handle_razorpay(await request.body(), signature)
