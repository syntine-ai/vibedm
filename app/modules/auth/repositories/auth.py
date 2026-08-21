from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import CurrentUser


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_user(self, user: CurrentUser) -> dict:
        result = await self.session.execute(
            text(
                """
                insert into public.users (id, email, first_name, last_name, phone, avatar_url)
                values (:id, :email, :first_name, :last_name, :phone, :avatar_url)
                on conflict (id) do update set
                  email = excluded.email,
                  updated_at = now()
                returning id, email, first_name, last_name, phone, avatar_url
                """
            ),
            {
                "id": user.id,
                "email": user.email,
                "first_name": user.claims.get("first_name"),
                "last_name": user.claims.get("last_name"),
                "phone": user.claims.get("phone"),
                "avatar_url": user.claims.get("avatar_url"),
            },
        )
        await self.session.commit()
        return dict(result.mappings().one())

    async def get_user(self, user_id: UUID) -> dict | None:
        result = await self.session.execute(
            text(
                """
                select id, email, first_name, last_name, phone, avatar_url
                from public.users
                where id = :user_id
                """
            ),
            {"user_id": user_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def list_workspaces(self, user_id: UUID) -> list[dict]:
        result = await self.session.execute(
            text(
                """
                select
                  w.id,
                  w.name,
                  wm.role::text as role,
                  ic.ig_username,
                  s.plan_id as plan,
                  wm.active
                from public.workspace_members wm
                join public.workspaces w on w.id = wm.workspace_id and w.deleted_at is null
                left join public.instagram_connections ic on ic.workspace_id = w.id
                left join public.subscriptions s on s.workspace_id = w.id and s.status <> 'canceled'
                where wm.user_id = :user_id
                order by wm.active desc, w.created_at desc
                """
            ),
            {"user_id": user_id},
        )
        return [dict(row) for row in result.mappings().all()]
