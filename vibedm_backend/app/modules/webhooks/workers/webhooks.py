from __future__ import annotations


async def process_webhook_event(provider: str, external_id: str) -> dict[str, str]:
    return {"provider": provider, "external_id": external_id, "status": "scheduled"}
