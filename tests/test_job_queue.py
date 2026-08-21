from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.jobs import JobCreate, PostgresJobQueue


class FakeMappings:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows

    def one(self) -> dict:
        return self.rows[0]

    def first(self) -> dict | None:
        return self.rows[0] if self.rows else None


class FakeResult:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows

    def mappings(self) -> FakeMappings:
        return FakeMappings(self.rows)


class FakeSession:
    def __init__(self, rows: list[dict] | None = None) -> None:
        self.rows = rows or []
        self.calls: list[tuple[str, dict]] = []
        self.commits = 0

    async def execute(self, statement, params: dict | None = None) -> FakeResult:
        self.calls.append((str(statement), params or {}))
        return FakeResult(self.rows)

    async def commit(self) -> None:
        self.commits += 1


def job_row(**overrides) -> dict:
    now = datetime.now(UTC)
    return {
        "id": uuid4(),
        "job_type": "automation.run",
        "workspace_id": uuid4(),
        "payload": {"automation_run_id": str(uuid4())},
        "status": "queued",
        "priority": 0,
        "attempts": 0,
        "max_attempts": 5,
        "run_at": now,
        "locked_at": None,
        "locked_by": None,
        "last_error": None,
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
    } | overrides


async def test_enqueue_writes_to_background_jobs_not_webhook_events() -> None:
    session = FakeSession(rows=[job_row()])
    queue = PostgresJobQueue(session)  # type: ignore[arg-type]

    record = await queue.enqueue(
        JobCreate(job_type="automation.run", payload={"automation_run_id": "run_1"})
    )

    sql = session.calls[0][0]
    assert "public.background_jobs" in sql
    assert "webhook_events" not in sql
    assert session.calls[0][1]["job_type"] == "automation.run"
    assert record.status == "queued"
    assert session.commits == 1


async def test_claim_next_returns_running_job_record() -> None:
    session = FakeSession(rows=[job_row(status="running", attempts=1, locked_by="worker-1")])
    queue = PostgresJobQueue(session)  # type: ignore[arg-type]

    record = await queue.claim_next("worker-1", ["automation.run"])

    assert record is not None
    assert record.status == "running"
    assert record.locked_by == "worker-1"
    assert "claim_background_job" in session.calls[0][0]
    assert session.calls[0][1]["job_types"] == ["automation.run"]


async def test_claim_next_returns_none_when_no_job_is_ready() -> None:
    session = FakeSession(rows=[])
    queue = PostgresJobQueue(session)  # type: ignore[arg-type]

    record = await queue.claim_next("worker-1")

    assert record is None


async def test_mark_succeeded_completes_and_unlocks_job() -> None:
    session = FakeSession()
    queue = PostgresJobQueue(session)  # type: ignore[arg-type]
    job_id = uuid4()

    await queue.mark_succeeded(job_id)

    sql = session.calls[0][0]
    assert "status = 'succeeded'" in sql
    assert "completed_at = now()" in sql
    assert "locked_at = null" in sql
    assert session.calls[0][1]["job_id"] == job_id
    assert session.commits == 1


async def test_mark_failed_retries_or_dead_letters_with_backoff() -> None:
    session = FakeSession()
    queue = PostgresJobQueue(session)  # type: ignore[arg-type]

    await queue.mark_failed(uuid4(), "boom")

    sql = session.calls[0][0]
    assert "when attempts >= max_attempts then 'dead'::job_status" in sql
    assert "else 'queued'::job_status" in sql
    assert "power(2, attempts)" in sql
    assert session.calls[0][1]["error"] == "boom"


async def test_requeue_stale_calls_database_recovery_function() -> None:
    session = FakeSession(rows=[{"count": 2}])
    queue = PostgresJobQueue(session)  # type: ignore[arg-type]

    count = await queue.requeue_stale(lock_timeout_minutes=30)

    assert count == 2
    assert "requeue_stale_background_jobs" in session.calls[0][0]
    assert session.calls[0][1]["lock_timeout"] == timedelta(minutes=30)
