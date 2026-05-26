from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

AutomationStatus = Literal["draft", "active", "inactive"]
TriggerType = Literal["comment_post", "dm", "live_comment", "story_reply", "story_mention"]
ActionType = Literal[
    "send_dm", "send_comment_reply", "ask_for_email", "ask_for_phone", "send_link", "tag_contact"
]


class AutomationStep(BaseModel):
    id: UUID | None = None
    order: int = Field(gt=0)
    action_type: ActionType
    config: dict = Field(default_factory=dict)


class AutomationCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    trigger_type: TriggerType | None = None


class AutomationUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    trigger_type: TriggerType | None = None
    trigger_config: dict | None = None
    steps: list[AutomationStep] | None = None


class AutomationSummary(BaseModel):
    id: UUID
    name: str
    status: AutomationStatus
    trigger_type: TriggerType | None = None
    trigger_config: dict = Field(default_factory=dict)


class AutomationDetail(AutomationSummary):
    steps: list[AutomationStep] = Field(default_factory=list)


class TestTriggerRequest(BaseModel):
    event: dict = Field(default_factory=dict)


class AutomationRunResponse(BaseModel):
    id: UUID
    automation_id: UUID
    status: str
    trigger_event: dict
    step_trace: list[dict] = Field(default_factory=list)
