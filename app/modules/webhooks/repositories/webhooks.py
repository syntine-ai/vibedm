from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class WebhookRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_event(self, provider: str, external_id: str, payload: dict) -> bool:
        try:
            await self.session.execute(
                text(
                    """
                    insert into public.webhook_events (provider, external_id, payload)
                    values (:provider, :external_id, :payload)
                    """
                ),
                {"provider": provider, "external_id": external_id, "payload": payload},
            )
            await self.session.commit()
            return True
        except IntegrityError:
            await self.session.rollback()
            return False
