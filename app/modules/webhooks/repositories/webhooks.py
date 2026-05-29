from __future__ import annotations

from uuid import UUID
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class WebhookRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_event(self, provider: str, external_id: str, payload: dict) -> bool:
        import json
        payload_str = json.dumps(payload) if isinstance(payload, (dict, list)) else payload
        try:
            await self.session.execute(
                text(
                    """
                    insert into public.webhook_events (provider, external_id, payload)
                    values (:provider, :external_id, :payload)
                    """
                ),
                {"provider": provider, "external_id": external_id, "payload": payload_str},
            )
            await self.session.commit()
            return True
        except IntegrityError:
            await self.session.rollback()
            return False

    async def find_workspace_by_ig_user(self, ig_user_id: str) -> UUID | None:
        result = await self.session.execute(
            text(
                """
                select workspace_id
                from public.instagram_connections
                where ig_user_id = :ig_user_id
                """
            ),
            {"ig_user_id": ig_user_id},
        )
        row = result.mappings().first()
        return row["workspace_id"] if row else None

    async def list_active_automations(self, workspace_id: UUID) -> list[dict]:
        result = await self.session.execute(
            text(
                """
                select id, trigger_type::text as trigger_type, trigger_config
                from public.automations
                where workspace_id = :workspace_id
                  and status = 'active'
                  and deleted_at is null
                """
            ),
            {"workspace_id": workspace_id},
        )
        return [dict(row) for row in result.mappings().all()]

    async def upsert_contact(
        self,
        workspace_id: UUID,
        ig_user_id: str,
        ig_username: str | None,
        source_automation_id: UUID | None = None,
    ) -> UUID:
        result = await self.session.execute(
            text(
                """
                insert into public.contacts (workspace_id, ig_user_id, ig_username, source_automation_id)
                values (:workspace_id, :ig_user_id, :ig_username, :source_automation_id)
                on conflict (workspace_id, ig_user_id) do update set
                    ig_username = coalesce(:ig_username, public.contacts.ig_username),
                    updated_at = now()
                returning id
                """
            ),
            {
                "workspace_id": workspace_id,
                "ig_user_id": ig_user_id,
                "ig_username": ig_username,
                "source_automation_id": source_automation_id,
            },
        )
        await self.session.commit()
        return result.scalar_one()

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

    async def enqueue_automation_job(self, workspace_id: UUID, automation_run_id: UUID) -> None:
        import json
        payload = {"automation_run_id": str(automation_run_id)}
        payload_str = json.dumps(payload)
        await self.session.execute(
            text(
                """
                insert into public.background_jobs
                  (job_type, workspace_id, payload, priority, run_at, max_attempts)
                values
                  ('automation.run', :workspace_id, :payload, 0, now(), 5)
                """
            ),
            {
                "workspace_id": workspace_id,
                "payload": payload_str,
            },
        )
        await self.session.commit()

    async def update_contact_leads(
        self,
        workspace_id: UUID,
        ig_user_id: str,
        email: str | None = None,
        phone: str | None = None,
    ) -> None:
        await self.session.execute(
            text(
                """
                update public.contacts
                   set email = coalesce(:email, email),
                       phone = coalesce(:phone, phone),
                       updated_at = now()
                 where workspace_id = :workspace_id and ig_user_id = :ig_user_id
                """
            ),
            {
                "workspace_id": workspace_id,
                "ig_user_id": ig_user_id,
                "email": email,
                "phone": phone,
            },
        )
        await self.session.commit()

    async def find_contact_by_ig_user(self, workspace_id: UUID, ig_user_id: str) -> UUID | None:
        result = await self.session.execute(
            text(
                """
                select id
                from public.contacts
                where workspace_id = :workspace_id and ig_user_id = :ig_user_id
                """
            ),
            {"workspace_id": workspace_id, "ig_user_id": ig_user_id},
        )
        row = result.mappings().first()
        return row["id"] if row else None

    async def find_awaiting_run(self, workspace_id: UUID, contact_id: UUID) -> UUID | None:
        result = await self.session.execute(
            text(
                """
                select id
                from public.automation_runs
                where workspace_id = :workspace_id
                  and contact_id = :contact_id
                  and status = 'awaiting_interaction'
                order by created_at desc
                limit 1
                """
            ),
            {"workspace_id": workspace_id, "contact_id": contact_id},
        )
        row = result.mappings().first()
        return row["id"] if row else None

    async def resume_awaiting_run(self, workspace_id: UUID, run_id: UUID) -> None:
        await self.session.execute(
            text(
                """
                update public.automation_runs
                set status = 'queued'
                where id = :run_id
                """
            ),
            {"run_id": run_id},
        )
        await self.enqueue_automation_job(workspace_id, run_id)
        await self.session.commit()
