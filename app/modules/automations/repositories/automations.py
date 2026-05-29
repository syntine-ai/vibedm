from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AutomationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_automations(
        self,
        *,
        workspace_id: UUID,
        status: str | None,
        trigger_type: str | None,
        q: str | None,
    ) -> list[dict]:
        result = await self.session.execute(
            text(
                """
                select id, name, status::text as status, trigger_type::text as trigger_type,
                       trigger_config
                from public.automations
                where workspace_id = :workspace_id
                  and deleted_at is null
                  and (cast(:status as text) is null or status::text = :status)
                  and (cast(:trigger_type as text) is null or trigger_type::text = :trigger_type)
                  and (cast(:q as text) is null or name ilike '%' || :q || '%')
                order by updated_at desc
                """
            ),
            {"workspace_id": workspace_id, "status": status, "trigger_type": trigger_type, "q": q},
        )
        return [dict(row) for row in result.mappings().all()]

    async def create(
        self, *, workspace_id: UUID, user_id: UUID, name: str, trigger_type: str | None
    ) -> dict:
        result = await self.session.execute(
            text(
                """
                insert into public.automations (workspace_id, created_by, name, trigger_type)
                values (:workspace_id, :user_id, :name, :trigger_type)
                returning id, name, status::text as status, trigger_type::text as trigger_type,
                          trigger_config
                """
            ),
            {
                "workspace_id": workspace_id,
                "user_id": user_id,
                "name": name,
                "trigger_type": trigger_type,
            },
        )
        await self.session.commit()
        return dict(result.mappings().one())

    async def get_detail(self, *, workspace_id: UUID, automation_id: UUID) -> dict | None:
        result = await self.session.execute(
            text(
                """
                select id, name, status::text as status, trigger_type::text as trigger_type,
                       trigger_config
                from public.automations
                where id = :automation_id and workspace_id = :workspace_id and deleted_at is null
                """
            ),
            {"workspace_id": workspace_id, "automation_id": automation_id},
        )
        automation = result.mappings().first()
        if automation is None:
            return None

        steps_result = await self.session.execute(
            text(
                """
                select id, step_order as "order", action_type::text as action_type, config
                from public.automation_steps
                where automation_id = :automation_id
                order by step_order asc
                """
            ),
            {"automation_id": automation_id},
        )
        return dict(automation) | {"steps": [dict(row) for row in steps_result.mappings().all()]}

    async def replace(self, *, workspace_id: UUID, automation_id: UUID, data: dict) -> dict | None:
        import json

        existing = await self.get_detail(workspace_id=workspace_id, automation_id=automation_id)
        if existing is None:
            return None

        trigger_config = data.get("trigger_config")
        if isinstance(trigger_config, (dict, list)):
            trigger_config = json.dumps(trigger_config)

        await self.session.execute(
            text(
                """
                update public.automations
                set name = coalesce(:name, name),
                    trigger_type = coalesce(:trigger_type, trigger_type),
                    trigger_config = coalesce(:trigger_config, trigger_config),
                    updated_at = now()
                where id = :automation_id and workspace_id = :workspace_id
                """
            ),
            {
                "workspace_id": workspace_id,
                "automation_id": automation_id,
                "name": data.get("name"),
                "trigger_type": data.get("trigger_type"),
                "trigger_config": trigger_config,
            },
        )
        if data.get("steps") is not None:
            await self.session.execute(
                text("delete from public.automation_steps where automation_id = :automation_id"),
                {"automation_id": automation_id},
            )
            for step in data["steps"]:
                step_order = step["order"] if isinstance(step, dict) else step.order
                action_type = step["action_type"] if isinstance(step, dict) else step.action_type
                config = step["config"] if isinstance(step, dict) else step.config
                if isinstance(config, (dict, list)):
                    config = json.dumps(config)
                await self.session.execute(
                    text(
                        """
                        insert into public.automation_steps
                          (automation_id, step_order, action_type, config)
                        values (:automation_id, :step_order, :action_type, :config)
                        """
                    ),
                    {
                        "automation_id": automation_id,
                        "step_order": step_order,
                        "action_type": action_type,
                        "config": config,
                    },
                )
        await self.session.commit()
        return await self.get_detail(workspace_id=workspace_id, automation_id=automation_id)

    async def set_status(
        self, *, workspace_id: UUID, automation_id: UUID, status: str
    ) -> dict | None:
        result = await self.session.execute(
            text(
                """
                update public.automations set status = :status, updated_at = now()
                where id = :automation_id and workspace_id = :workspace_id and deleted_at is null
                returning id
                """
            ),
            {"workspace_id": workspace_id, "automation_id": automation_id, "status": status},
        )
        await self.session.commit()
        if result.mappings().first() is None:
            return None
        return await self.get_detail(workspace_id=workspace_id, automation_id=automation_id)

    async def delete(self, *, workspace_id: UUID, automation_id: UUID) -> None:
        await self.session.execute(
            text(
                """
                update public.automations set deleted_at = now()
                where id = :automation_id and workspace_id = :workspace_id
                """
            ),
            {"workspace_id": workspace_id, "automation_id": automation_id},
        )
        await self.session.commit()

    async def create_run(self, *, workspace_id: UUID, automation_id: UUID, event: dict) -> dict:
        import json
        event_str = json.dumps(event) if isinstance(event, (dict, list)) else event
        result = await self.session.execute(
            text(
                """
                insert into public.automation_runs
                  (workspace_id, automation_id, status, trigger_event, step_trace)
                values (:workspace_id, :automation_id, 'queued', :event, '[]'::jsonb)
                returning id, automation_id, status::text as status, trigger_event, step_trace
                """
            ),
            {"workspace_id": workspace_id, "automation_id": automation_id, "event": event_str},
        )
        await self.session.commit()
        return dict(result.mappings().one())

    async def create_automation_run(
        self,
        workspace_id: UUID,
        automation_id: UUID,
        contact_id: UUID | None,
        trigger_event: dict,
    ) -> UUID:
        import json
        trigger_event_str = json.dumps(trigger_event) if isinstance(trigger_event, (dict, list)) else trigger_event
        result = await self.session.execute(
            text(
                """
                insert into public.automation_runs
                  (workspace_id, automation_id, contact_id, status, trigger_event, step_trace)
                values
                  (:workspace_id, :automation_id, :contact_id, 'queued', :trigger_event, '[]'::jsonb)
                returning id
                """
            ),
            {
                "workspace_id": workspace_id,
                "automation_id": automation_id,
                "contact_id": contact_id,
                "trigger_event": trigger_event_str,
            },
        )
        await self.session.commit()
        return result.scalar_one()

    async def list_runs(self, *, workspace_id: UUID, automation_id: UUID) -> list[dict]:
        result = await self.session.execute(
            text(
                """
                select id, automation_id, status::text as status, trigger_event, step_trace
                from public.automation_runs
                where workspace_id = :workspace_id and automation_id = :automation_id
                order by created_at desc
                """
            ),
            {"workspace_id": workspace_id, "automation_id": automation_id},
        )
        return [dict(row) for row in result.mappings().all()]

    async def get_run(self, run_id: UUID) -> dict | None:
        result = await self.session.execute(
            text(
                """
                select id, workspace_id, automation_id, contact_id, status::text as status,
                       trigger_event, step_trace
                from public.automation_runs
                where id = :run_id
                """
            ),
            {"run_id": run_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def get_workspace_token(self, workspace_id: UUID) -> str | None:
        result = await self.session.execute(
            text(
                """
                select access_token_enc
                from public.instagram_connections
                where workspace_id = :workspace_id
                """
            ),
            {"workspace_id": workspace_id},
        )
        row = result.mappings().first()
        if not row:
            return None
        return row["access_token_enc"].decode("utf-8")

    async def update_run(
        self,
        run_id: UUID,
        status: str,
        step_trace: list,
        error: str | None = None,
    ) -> None:
        import json
        await self.session.execute(
            text(
                """
                update public.automation_runs
                   set status = :status,
                       step_trace = :step_trace,
                       error = :error,
                       started_at = coalesce(started_at, now()),
                       finished_at = now()
                 where id = :run_id
                """
            ),
            {
                "run_id": run_id,
                "status": status,
                "step_trace": json.dumps(step_trace),
                "error": error,
            },
        )
        await self.session.commit()

