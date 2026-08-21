from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DashboardStatsResponse(BaseModel):
    dms_sent: int
    active_automations: int
    contacts_captured: int
    revenue_paise: int = 0


class UsageResponse(BaseModel):
    dm_count: int
    dm_limit: int
    contact_count: int
    contact_limit: int


class ActivityResponse(BaseModel):
    id: str
    type: str
    label: str
    created_at: datetime
