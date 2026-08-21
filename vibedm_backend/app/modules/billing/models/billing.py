from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = {"schema": "public"}

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    tier: Mapped[str] = mapped_column(Text)
    display_name: Mapped[str] = mapped_column(Text)
    monthly_paise: Mapped[int] = mapped_column(Integer)
    features: Mapped[list[str]] = mapped_column(JSONB)
    is_popular: Mapped[bool] = mapped_column(Boolean)
    sort_order: Mapped[int] = mapped_column(Integer)


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = {"schema": "public"}

    id: Mapped[UUID] = mapped_column(primary_key=True)
    workspace_id: Mapped[UUID]
    plan_id: Mapped[str] = mapped_column(Text)
    cycle: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean)
    provider: Mapped[str | None] = mapped_column(Text)
    provider_customer_id: Mapped[str | None] = mapped_column(Text)
    provider_subscription_id: Mapped[str | None] = mapped_column(Text)
