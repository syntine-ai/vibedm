from __future__ import annotations

from pydantic import BaseModel


class WebhookReceipt(BaseModel):
    received: bool
    duplicate: bool = False
