from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

JobStatus = Literal["queued", "running", "succeeded", "failed", "dead"]


class JobCreate(BaseModel):
    job_type: str
    workspace_id: UUID | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = 0
    run_at: datetime | None = None
    max_attempts: int = 5


class JobRecord(BaseModel):
    id: UUID
    job_type: str
    workspace_id: UUID | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    status: JobStatus
    priority: int
    attempts: int
    max_attempts: int
    run_at: datetime
    locked_at: datetime | None = None
    locked_by: str | None = None
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None


class PostgresJobQueue:
    """Postgres-backed queue adapter.

    Uses public.background_jobs. Claiming is delegated to a SECURITY DEFINER
    database function that uses SELECT FOR UPDATE SKIP LOCKED.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def enqueue(self, job: JobCreate) -> JobRecord:
        import json
        # Use plain model_dump() (NOT mode="json") so that datetime fields like
        # run_at stay as datetime objects — asyncpg requires actual datetime instances,
        # not ISO strings. Only the payload dict needs manual JSON serialization.
        job_data = job.model_dump()
        if isinstance(job_data.get("payload"), dict):
            job_data["payload"] = json.dumps(job_data["payload"])

        result = await self.session.execute(
            text(
                """
                insert into public.background_jobs
                  (job_type, workspace_id, payload, priority, run_at, max_attempts)
                values
                  (:job_type, :workspace_id, :payload, :priority, coalesce(:run_at, now()),
                   :max_attempts)
                returning id, job_type, workspace_id, payload, status::text as status,
                          priority, attempts, max_attempts, run_at, locked_at, locked_by,
                          last_error, created_at, updated_at, completed_at
                """
            ),
            job_data,
        )
        await self.session.commit()
        return JobRecord(**dict(result.mappings().one()))

    async def claim_next(
        self, worker_id: str, job_types: list[str] | None = None
    ) -> JobRecord | None:
        result = await self.session.execute(
            text(
                """
                select id, job_type, workspace_id, payload, status::text as status,
                       priority, attempts, max_attempts, run_at, locked_at, locked_by,
                       last_error, created_at, updated_at, completed_at
                from public.claim_background_job(:worker_id, :job_types)
                """
            ),
            {"worker_id": worker_id, "job_types": job_types},
        )
        row = result.mappings().first()
        if row is None:
            return None
        await self.session.commit()
        return JobRecord(**dict(row))

    async def mark_succeeded(self, job_id: UUID) -> None:
        await self.session.execute(
            text(
                """
                update public.background_jobs
                   set status = 'succeeded',
                       completed_at = now(),
                       locked_at = null,
                       locked_by = null,
                       last_error = null,
                       updated_at = now()
                 where id = :job_id
                """
            ),
            {"job_id": job_id},
        )
        await self.session.commit()

    async def mark_failed(self, job_id: UUID, error: str) -> None:
        await self.session.execute(
            text(
                """
                update public.background_jobs
                   set status = case
                         when attempts >= max_attempts then 'dead'::job_status
                         else 'queued'::job_status
                       end,
                       run_at = case
                         when attempts >= max_attempts then run_at
                         else now() + make_interval(
                           secs => least(3600, (power(2, attempts)::int * 30))
                         )
                       end,
                       locked_at = null,
                       locked_by = null,
                       last_error = :error,
                       completed_at = case
                         when attempts >= max_attempts then now()
                         else null
                       end,
                       updated_at = now()
                 where id = :job_id
                """
            ),
            {"job_id": job_id, "error": error},
        )
        await self.session.commit()

    async def requeue_stale(self, lock_timeout_minutes: int = 15) -> int:
        lock_timeout = timedelta(minutes=lock_timeout_minutes)
        result = await self.session.execute(
            text(
                """
                select public.requeue_stale_background_jobs(:lock_timeout) as count
                """
            ),
            {"lock_timeout": lock_timeout},
        )
        await self.session.commit()
        row = result.mappings().one()
        return int(row["count"])
