from __future__ import annotations

import hmac
from hashlib import sha256

import pytest

from app.config import Settings
from app.core.errors import ApiError
from app.modules.webhooks.services.webhooks import WebhookService


class FakeWebhookRepository:
    def __init__(self) -> None:
        self.events: set[tuple[str, str]] = set()

    async def record_event(self, provider: str, external_id: str, payload: dict) -> bool:
        key = (provider, external_id)
        if key in self.events:
            return False
        self.events.add(key)
        return True


def stripe_signature(body: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode(), body, sha256).hexdigest()
    return f"t=1,v1={digest}"


async def test_invalid_stripe_signature_is_rejected() -> None:
    service = WebhookService(
        repository=FakeWebhookRepository(),
        settings=Settings(stripe_webhook_secret="stripe-secret"),
    )

    with pytest.raises(ApiError) as exc:
        await service.handle_stripe(body=b'{"id":"evt_1"}', signature="bad")

    assert exc.value.status_code == 401
    assert exc.value.code == "invalid_signature"


async def test_duplicate_stripe_event_is_idempotent() -> None:
    body = b'{"id":"evt_1","type":"checkout.session.completed"}'
    service = WebhookService(
        repository=FakeWebhookRepository(),
        settings=Settings(stripe_webhook_secret="stripe-secret"),
    )
    signature = stripe_signature(body, "stripe-secret")

    first = await service.handle_stripe(body=body, signature=signature)
    second = await service.handle_stripe(body=body, signature=signature)

    assert first == {"received": True, "duplicate": False}
    assert second == {"received": True, "duplicate": True}
