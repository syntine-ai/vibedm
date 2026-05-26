from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Automation(Base):
    __tablename__ = "automations"
    __table_args__ = {"schema": "public"}

    id: Mapped[UUID] = mapped_column(primary_key=True)
    workspace_id: Mapped[UUID]
    name: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    trigger_type: Mapped[str | None] = mapped_column(Text)
    trigger_config: Mapped[dict] = mapped_column(JSONB)
    created_by: Mapped[UUID | None]
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AutomationStep(Base):
    __tablename__ = "automation_steps"
    __table_args__ = {"schema": "public"}

    id: Mapped[UUID] = mapped_column(primary_key=True)
    automation_id: Mapped[UUID] = mapped_column(ForeignKey("public.automations.id"))
    step_order: Mapped[int] = mapped_column(Integer)
    action_type: Mapped[str] = mapped_column(Text)
    config: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
