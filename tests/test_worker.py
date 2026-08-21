from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.core.jobs import JobRecord


def make_record(job_type: str, payload: dict) -> JobRecord:
    now = datetime.now(UTC)
    return JobRecord(
        id=uuid4(),
        job_type=job_type,
        workspace_id=uuid4(),
        payload=payload,
        status="running",
        priority=0,
        attempts=1,
        max_attempts=5,
        run_at=now,
        locked_at=now,
        locked_by="worker-1",
        last_error=None,
        created_at=now,
        updated_at=now,
        completed_at=None,
    )


async def test_dispatch_supported_worker_job(monkeypatch: pytest.MonkeyPatch) -> None:
    from app import worker

    called: dict[str, object] = {}

    async def fake_run_automation(automation_run_id):
        called["automation_run_id"] = automation_run_id
        return {"status": "ok"}

    monkeypatch.setattr(worker, "run_automation", fake_run_automation)
    automation_run_id = uuid4()

    result = await worker.dispatch_job(
        make_record("automation.run", {"automation_run_id": str(automation_run_id)})
    )

    assert result == {"status": "ok"}
    assert called == {"automation_run_id": automation_run_id}


async def test_dispatch_rejects_unknown_job_type() -> None:
    from app.worker import dispatch_job

    with pytest.raises(ValueError, match="Unsupported job type"):
        await dispatch_job(make_record("unknown.job", {}))
