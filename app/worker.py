from __future__ import annotations

import asyncio
import os
import socket
from typing import Any
from uuid import UUID

from app.config import get_settings
from app.core.jobs import JobRecord, PostgresJobQueue
from app.db import get_sessionmaker
from app.modules.automations.workers.automations import run_automation
from app.modules.billing.workers.billing import sync_subscription
from app.modules.dashboard.workers.dashboard import rollup_usage
from app.modules.instagram.workers.instagram import refresh_token

SUPPORTED_JOB_TYPES = [
    "automation.run",
    "instagram.refresh_token",
    "billing.sync_subscription",
    "usage.rollup",
]


def build_worker_id() -> str:
    settings = get_settings()
    if settings.job_worker_id:
        return settings.job_worker_id
    return f"{socket.gethostname()}:{os.getpid()}"


def _uuid_from_payload(payload: dict[str, Any], key: str) -> UUID:
    value = payload.get(key)
    if value is None:
        raise ValueError(f"Job payload missing {key}")
    return UUID(str(value))


async def dispatch_job(job: JobRecord) -> dict[str, Any]:
    if job.job_type == "automation.run":
        return await run_automation(_uuid_from_payload(job.payload, "automation_run_id"))
    if job.job_type == "instagram.refresh_token":
        if job.workspace_id is None:
            raise ValueError("instagram.refresh_token requires workspace_id")
        return await refresh_token(job.workspace_id)
    if job.job_type == "billing.sync_subscription":
        if job.workspace_id is None:
            raise ValueError("billing.sync_subscription requires workspace_id")
        return await sync_subscription(job.workspace_id)
    if job.job_type == "usage.rollup":
        return await rollup_usage(job.workspace_id, job.payload)
    raise ValueError(f"Unsupported job type: {job.job_type}")


async def run_worker() -> None:
    settings = get_settings()
    worker_id = build_worker_id()
    sessionmaker = get_sessionmaker()
    stale_check_every = max(1, int(60 / max(settings.job_poll_interval_seconds, 1)))
    tick = 0

    async with sessionmaker() as session:
        queue = PostgresJobQueue(session)
        await queue.requeue_stale(settings.job_lock_timeout_minutes)

    while True:
        async with sessionmaker() as session:
            queue = PostgresJobQueue(session)
            if tick % stale_check_every == 0:
                await queue.requeue_stale(settings.job_lock_timeout_minutes)

            job = await queue.claim_next(worker_id, SUPPORTED_JOB_TYPES)
            if job is None:
                tick += 1
                await asyncio.sleep(settings.job_poll_interval_seconds)
                continue

            try:
                await dispatch_job(job)
            except Exception as exc:
                await queue.mark_failed(job.id, str(exc))
            else:
                await queue.mark_succeeded(job.id)
            tick += 1


def main() -> None:
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
