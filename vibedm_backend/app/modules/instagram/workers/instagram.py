from __future__ import annotations

from uuid import UUID


async def refresh_token(workspace_id: UUID) -> dict[str, str]:
    return {"workspace_id": str(workspace_id), "status": "scheduled"}
