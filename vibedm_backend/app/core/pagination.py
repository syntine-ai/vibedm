from __future__ import annotations

import base64
from typing import Any


def encode_cursor(payload: dict[str, Any]) -> str:
    raw = repr(payload).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def clamp_limit(limit: int | None, *, default: int = 25, maximum: int = 100) -> int:
    if limit is None:
        return default
    return max(1, min(limit, maximum))
