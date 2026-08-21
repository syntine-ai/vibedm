from __future__ import annotations

import hmac
import json
from hashlib import sha256
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import Settings
from app.core.errors import ApiError
from app.modules.webhooks.services.webhooks import WebhookService
from app.modules.webhooks.repositories.webhooks import WebhookRepository


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


@patch("app.modules.webhooks.services.webhooks.WebhookRepository", autospec=True)
async def test_handle_instagram_dm_trigger_success(MockRepoClass) -> None:
    mock_repo = MockRepoClass.return_value
    mock_repo.record_event = AsyncMock(return_value=True)
    mock_repo.find_workspace_by_ig_user = AsyncMock(return_value="11111111-1111-1111-1111-111111111111")
    mock_repo.list_active_automations = AsyncMock(
        return_value=[
            {
                "id": "22222222-2222-2222-2222-222222222222",
                "trigger_type": "dm",
                "trigger_config": {"keywords": ["giveaway", "free"], "match": "any"},
            }
        ]
    )
    mock_repo.upsert_contact = AsyncMock(return_value="33333333-3333-3333-3333-333333333333")
    mock_repo.find_contact_by_ig_user = AsyncMock(return_value=None)
    mock_repo.create_automation_run = AsyncMock(return_value="44444444-4444-4444-4444-444444444444")
    mock_repo.enqueue_automation_job = AsyncMock()

    service = WebhookService(repository=mock_repo, settings=Settings(instagram_webhook_secret=""))

    dm_payload = {
        "object": "instagram",
        "entry": [
            {
                "id": "ig-page-id",
                "messaging": [
                    {
                        "sender": {"id": "sender-123"},
                        "recipient": {"id": "ig-page-id"},
                        "message": {"text": "Send me that Free guide!"},
                    }
                ],
            }
        ],
    }

    body = json.dumps(dm_payload).encode()
    res = await service.handle_instagram(body, signature=None)

    assert res == {"received": True, "duplicate": False}
    mock_repo.upsert_contact.assert_called_once_with(
        workspace_id="11111111-1111-1111-1111-111111111111",
        ig_user_id="sender-123",
        ig_username=None,
        source_automation_id="22222222-2222-2222-2222-222222222222",
    )
    mock_repo.create_automation_run.assert_called_once()
    mock_repo.enqueue_automation_job.assert_called_once_with(
        workspace_id="11111111-1111-1111-1111-111111111111",
        automation_run_id="44444444-4444-4444-4444-444444444444",
    )


@patch("app.modules.webhooks.services.webhooks.WebhookRepository", autospec=True)
async def test_handle_instagram_comment_trigger_success(MockRepoClass) -> None:
    mock_repo = MockRepoClass.return_value
    mock_repo.record_event = AsyncMock(return_value=True)
    mock_repo.find_workspace_by_ig_user = AsyncMock(return_value="11111111-1111-1111-1111-111111111111")
    mock_repo.list_active_automations = AsyncMock(
        return_value=[
            {
                "id": "22222222-2222-2222-2222-222222222222",
                "trigger_type": "comment_post",
                "trigger_config": {"post_id": "media-999", "keywords": ["price", "cost"], "match": "any"},
            }
        ]
    )
    mock_repo.upsert_contact = AsyncMock(return_value="33333333-3333-3333-3333-333333333333")
    mock_repo.create_automation_run = AsyncMock(return_value="44444444-4444-4444-4444-444444444444")
    mock_repo.enqueue_automation_job = AsyncMock()

    service = WebhookService(repository=mock_repo, settings=Settings(instagram_webhook_secret=""))

    comment_payload = {
        "object": "instagram",
        "entry": [
            {
                "id": "ig-page-id",
                "changes": [
                    {
                        "field": "comments",
                        "value": {
                            "id": "comment-12345",
                            "text": "What is the price?",
                            "media": {"id": "media-999"},
                            "from": {"id": "sender-123", "username": "buyer_bob"},
                        },
                    }
                ],
            }
        ],
    }

    body = json.dumps(comment_payload).encode()
    res = await service.handle_instagram(body, signature=None)

    assert res == {"received": True, "duplicate": False}
    mock_repo.upsert_contact.assert_called_once_with(
        workspace_id="11111111-1111-1111-1111-111111111111",
        ig_user_id="sender-123",
        ig_username="buyer_bob",
        source_automation_id="22222222-2222-2222-2222-222222222222",
    )
    mock_repo.enqueue_automation_job.assert_called_once_with(
        workspace_id="11111111-1111-1111-1111-111111111111",
        automation_run_id="44444444-4444-4444-4444-444444444444",
    )
