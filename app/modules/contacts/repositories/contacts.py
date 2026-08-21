from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class ContactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(
        self,
        *,
        workspace_id: UUID,
        q: str | None,
        source_automation_id: UUID | None,
        tag: str | None,
    ) -> list[dict]:
        result = await self.session.execute(
            text(
                """
                select id, workspace_id, ig_user_id, ig_username::text as ig_username, name,
                       email::text as email, phone, source_automation_id, tags, notes
                from public.contacts
                where workspace_id = :workspace_id
                  and (
                    cast(:source_automation_id as uuid) is null
                    or source_automation_id = cast(:source_automation_id as uuid)
                  )
                  and (cast(:tag as text) is null or cast(:tag as text) = any(tags))
                  and (
                    cast(:q as text) is null or
                    coalesce(ig_username::text, '') ilike '%' || cast(:q as text) || '%' or
                    coalesce(name, '') ilike '%' || cast(:q as text) || '%' or
                    coalesce(email::text, '') ilike '%' || cast(:q as text) || '%' or
                    coalesce(phone, '') ilike '%' || cast(:q as text) || '%'
                  )
                order by created_at desc
                """
            ),
            {
                "workspace_id": workspace_id,
                "q": q,
                "source_automation_id": source_automation_id,
                "tag": tag,
            },
        )
        return [dict(row) for row in result.mappings().all()]

    async def get(self, *, workspace_id: UUID, contact_id: UUID) -> dict | None:
        result = await self.session.execute(
            text(
                """
                select id, workspace_id, ig_user_id, ig_username::text as ig_username, name,
                       email::text as email, phone, source_automation_id, tags, notes
                from public.contacts
                where workspace_id = :workspace_id and id = :contact_id
                """
            ),
            {"workspace_id": workspace_id, "contact_id": contact_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def create(self, *, workspace_id: UUID, data: dict) -> dict:
        result = await self.session.execute(
            text(
                """
                insert into public.contacts
                  (workspace_id, ig_user_id, ig_username, name, email, phone,
                   source_automation_id, tags, notes)
                values
                  (:workspace_id, :ig_user_id, :ig_username, :name, :email, :phone,
                   :source_automation_id, :tags, :notes)
                returning id, workspace_id, ig_user_id, ig_username::text as ig_username, name,
                          email::text as email, phone, source_automation_id, tags, notes
                """
            ),
            {"workspace_id": workspace_id, **data},
        )
        await self.session.commit()
        return dict(result.mappings().one())

    async def update(self, *, workspace_id: UUID, contact_id: UUID, data: dict) -> dict | None:
        existing = await self.get(workspace_id=workspace_id, contact_id=contact_id)
        if existing is None:
            return None
        merged = existing | data
        result = await self.session.execute(
            text(
                """
                update public.contacts
                set name = :name, email = :email, phone = :phone, notes = :notes,
                    tags = :tags, updated_at = now()
                where workspace_id = :workspace_id and id = :contact_id
                returning id, workspace_id, ig_user_id, ig_username::text as ig_username, name,
                          email::text as email, phone, source_automation_id, tags, notes
                """
            ),
            {"workspace_id": workspace_id, "contact_id": contact_id, **merged},
        )
        await self.session.commit()
        return dict(result.mappings().one())

    async def delete(self, *, workspace_id: UUID, contact_id: UUID) -> None:
        await self.session.execute(
            text(
                """
                delete from public.contacts
                where workspace_id = :workspace_id and id = :contact_id
                """
            ),
            {"workspace_id": workspace_id, "contact_id": contact_id},
        )
        await self.session.commit()
