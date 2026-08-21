from __future__ import annotations

from typing import Any
from uuid import UUID


async def rollup_usage(workspace_id: UUID | None, payload: dict[str, Any]) -> dict[str, str]:
    return {
        "workspace_id": str(workspace_id) if workspace_id else "",
        "status": "scheduled",
        "source": str(payload.get("source", "manual")),
    }
