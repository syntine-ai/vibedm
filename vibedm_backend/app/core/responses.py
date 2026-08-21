from __future__ import annotations

from typing import Any


def list_response(items: list[Any], next_cursor: str | None = None) -> dict[str, Any]:
    return {"items": items, "next_cursor": next_cursor}
