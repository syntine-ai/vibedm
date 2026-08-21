from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class WorkspaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_user(self, user_id: UUID) -> list[dict]:
        result = await self.session.execute(
            text(
                """
                select w.id, w.owner_id, w.name, w.avatar_url, wm.role::text as role,
                       coalesce(s.plan_id, 'free') as plan, ic.ig_username, wm.active
                from public.workspace_members wm
                join public.workspaces w on w.id = wm.workspace_id and w.deleted_at is null
                left join public.subscriptions s on s.workspace_id = w.id and s.status <> 'canceled'
                left join public.instagram_connections ic on ic.workspace_id = w.id
                where wm.user_id = :user_id
                order by wm.active desc, w.created_at desc
                """
            ),
            {"user_id": user_id},
        )
        return [dict(row) for row in result.mappings().all()]

    async def get(self, workspace_id: UUID) -> dict | None:
        result = await self.session.execute(
            text(
                """
                select w.id, w.owner_id, w.name, w.avatar_url,
                       coalesce(s.plan_id, 'free') as plan, ic.ig_username
                from public.workspaces w
                left join public.subscriptions s on s.workspace_id = w.id and s.status <> 'canceled'
                left join public.instagram_connections ic on ic.workspace_id = w.id
                where w.id = :workspace_id and w.deleted_at is null
                """
            ),
            {"workspace_id": workspace_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def update_name(self, workspace_id: UUID, name: str) -> dict | None:
        result = await self.session.execute(
            text(
                """
                update public.workspaces set name = :name, updated_at = now()
                where id = :workspace_id and deleted_at is null
                returning id, owner_id, name, avatar_url
                """
            ),
            {"workspace_id": workspace_id, "name": name},
        )
        await self.session.commit()
        row = result.mappings().first()
        return dict(row) if row else None

    async def activate(self, user_id: UUID, workspace_id: UUID) -> None:
        await self.session.execute(
            text("update public.workspace_members set active = false where user_id = :user_id"),
            {"user_id": user_id},
        )
        await self.session.execute(
            text(
                """
                update public.workspace_members set active = true
                where user_id = :user_id and workspace_id = :workspace_id
                """
            ),
            {"user_id": user_id, "workspace_id": workspace_id},
        )
        await self.session.commit()

    async def soft_delete(self, workspace_id: UUID) -> None:
        await self.session.execute(
            text("update public.workspaces set deleted_at = now() where id = :workspace_id"),
            {"workspace_id": workspace_id},
        )
        await self.session.commit()

    async def list_members(self, workspace_id: UUID) -> list[dict]:
        result = await self.session.execute(
            text(
                """
                select wm.workspace_id, wm.user_id, u.email, wm.role::text as role, wm.active
                from public.workspace_members wm
                left join public.users u on u.id = wm.user_id
                where wm.workspace_id = :workspace_id
                order by wm.created_at asc
                """
            ),
            {"workspace_id": workspace_id},
        )
        return [dict(row) for row in result.mappings().all()]

    async def update_member_role(self, workspace_id: UUID, user_id: UUID, role: str) -> dict | None:
        result = await self.session.execute(
            text(
                """
                update public.workspace_members set role = :role
                where workspace_id = :workspace_id and user_id = :user_id
                returning workspace_id, user_id, role::text as role, active
                """
            ),
            {"workspace_id": workspace_id, "user_id": user_id, "role": role},
        )
        await self.session.commit()
        row = result.mappings().first()
        return dict(row) if row else None

    async def remove_member(self, workspace_id: UUID, user_id: UUID) -> None:
        await self.session.execute(
            text(
                """
                delete from public.workspace_members
                where workspace_id = :workspace_id and user_id = :user_id
                """
            ),
            {"workspace_id": workspace_id, "user_id": user_id},
        )
        await self.session.commit()
