from __future__ import annotations

from uuid import UUID


async def run_automation(automation_run_id: UUID) -> dict[str, str]:
    return {"automation_run_id": str(automation_run_id), "status": "queued"}
