from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class InstagramRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_connection_by_ig_user(self, ig_user_id: str) -> dict | None:
        result = await self.session.execute(
            text(
                """
                select workspace_id, ig_user_id, ig_username
                from public.instagram_connections
                where ig_user_id = :ig_user_id
                """
            ),
            {"ig_user_id": ig_user_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def create_workspace_with_connection(
        self,
        *,
        owner_id: UUID,
        name: str,
        ig_user_id: str,
        ig_username: str,
        access_token: str,
        scopes: list[str],
        connection_type: str = "instagram_direct",
    ) -> dict:
        workspace_result = await self.session.execute(
            text(
                """
                insert into public.workspaces (owner_id, name)
                values (:owner_id, :name)
                returning id, owner_id, name, avatar_url
                """
            ),
            {"owner_id": owner_id, "name": name},
        )
        workspace = dict(workspace_result.mappings().one())
        await self.session.execute(
            text(
                """
                insert into public.instagram_connections
                  (workspace_id, ig_user_id, ig_username, access_token_enc, scopes, connection_type)
                values
                  (:workspace_id, :ig_user_id, :ig_username, :access_token_enc, :scopes, :connection_type)
                """
            ),
            {
                "workspace_id": workspace["id"],
                "ig_user_id": ig_user_id,
                "ig_username": ig_username,
                "access_token_enc": access_token.encode("utf-8"),
                "scopes": scopes,
                "connection_type": connection_type,
            },
        )
        await self.session.commit()
        return workspace | {
            "ig_username": ig_username,
            "ig_user_id": ig_user_id,
            "connection_type": connection_type,
            "plan": "free",
            "active": True,
        }

    async def disconnect(self, workspace_id: UUID) -> None:
        await self.session.execute(
            text("delete from public.instagram_connections where workspace_id = :workspace_id"),
            {"workspace_id": workspace_id},
        )
        await self.session.commit()

    async def update_connection(
        self,
        *,
        workspace_id: UUID,
        access_token: str,
        scopes: list[str],
        ig_username: str | None = None,
        connection_type: str | None = None,
    ) -> None:
        await self.session.execute(
            text(
                """
                update public.instagram_connections
                set access_token_enc = :access_token_enc,
                    scopes = :scopes,
                    ig_username = coalesce(:ig_username, ig_username),
                    connection_type = coalesce(:connection_type, connection_type),
                    updated_at = now()
                where workspace_id = :workspace_id
                """
            ),
            {
                "workspace_id": workspace_id,
                "access_token_enc": access_token.encode("utf-8"),
                "scopes": scopes,
                "ig_username": ig_username,
                "connection_type": connection_type,
            },
        )
        await self.session.commit()

    async def get_workspace_detail(self, workspace_id: UUID) -> dict | None:
        result = await self.session.execute(
            text(
                """
                select id, owner_id, name, avatar_url
                from public.workspaces
                where id = :workspace_id
                """
            ),
            {"workspace_id": workspace_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def delete_connection_by_ig_user(self, ig_user_id: str) -> None:
        await self.session.execute(
            text("delete from public.instagram_connections where ig_user_id = :ig_user_id"),
            {"ig_user_id": ig_user_id},
        )
        await self.session.commit()

    async def create_connection_for_workspace(
        self,
        *,
        workspace_id: UUID,
        ig_user_id: str,
        ig_username: str,
        access_token: str,
        scopes: list[str],
        connection_type: str = "instagram_direct",
    ) -> None:
        await self.session.execute(
            text(
                """
                insert into public.instagram_connections
                  (workspace_id, ig_user_id, ig_username, access_token_enc, scopes, connection_type)
                values
                  (:workspace_id, :ig_user_id, :ig_username, :access_token_enc, :scopes, :connection_type)
                """
            ),
            {
                "workspace_id": workspace_id,
                "ig_user_id": ig_user_id,
                "ig_username": ig_username,
                "access_token_enc": access_token.encode("utf-8"),
                "scopes": scopes,
                "connection_type": connection_type,
            },
        )
        await self.session.commit()

    async def get_connection(self, workspace_id: UUID) -> dict | None:
        result = await self.session.execute(
            text(
                """
                select workspace_id, ig_user_id, ig_username, access_token_enc, scopes, connection_type
                from public.instagram_connections
                where workspace_id = :workspace_id
                """
            ),
            {"workspace_id": workspace_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None


