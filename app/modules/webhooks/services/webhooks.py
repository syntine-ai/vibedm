from __future__ import annotations

import json

from app.config import Settings
from app.core.errors import ApiError
from app.modules.webhooks.repositories.webhooks import WebhookRepository
from app.security import verify_hmac_hex, verify_stripe_signature


class WebhookService:
    def __init__(self, repository: WebhookRepository, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings

    async def handle_instagram(self, body: bytes, signature: str | None) -> dict[str, bool]:
        if self.settings.instagram_webhook_secret:
            expected = signature or ""
            if expected.startswith("sha256="):
                expected = expected.removeprefix("sha256=")
            if not verify_hmac_hex(body, expected, self.settings.instagram_webhook_secret):
                raise ApiError(
                    status_code=401, code="invalid_signature", message="Invalid signature"
                )
        payload = self._json_payload(body)
        external_id = str(payload.get("id") or payload.get("entry", [{}])[0].get("id") or "unknown")
        inserted = await self.repository.record_event("instagram", external_id, payload)
        return {"received": True, "duplicate": not inserted}

    async def handle_stripe(self, body: bytes, signature: str | None) -> dict[str, bool]:
        if not signature or not verify_stripe_signature(
            body, signature, self.settings.stripe_webhook_secret
        ):
            raise ApiError(status_code=401, code="invalid_signature", message="Invalid signature")
        payload = self._json_payload(body)
        external_id = str(payload.get("id") or "unknown")
        inserted = await self.repository.record_event("stripe", external_id, payload)
        return {"received": True, "duplicate": not inserted}

    async def handle_razorpay(self, body: bytes, signature: str | None) -> dict[str, bool]:
        if not signature or not verify_hmac_hex(
            body, signature, self.settings.razorpay_webhook_secret
        ):
            raise ApiError(status_code=401, code="invalid_signature", message="Invalid signature")
        payload = self._json_payload(body)
        external_id = str(payload.get("event") or payload.get("id") or "unknown")
        inserted = await self.repository.record_event("razorpay", external_id, payload)
        return {"received": True, "duplicate": not inserted}

    @staticmethod
    def _json_payload(body: bytes) -> dict:
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            raise ApiError(
                status_code=400, code="invalid_json", message="Invalid JSON body"
            ) from exc
        if not isinstance(payload, dict):
            raise ApiError(
                status_code=400, code="invalid_json", message="JSON body must be an object"
            )
        return payload
