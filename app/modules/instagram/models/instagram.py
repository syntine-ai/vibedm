from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, LargeBinary, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class InstagramConnection(Base):
    __tablename__ = "instagram_connections"
    __table_args__ = {"schema": "public"}

    workspace_id: Mapped[UUID] = mapped_column(primary_key=True)
    ig_user_id: Mapped[str] = mapped_column(Text)
    ig_username: Mapped[str] = mapped_column(Text)
    access_token_enc: Mapped[bytes] = mapped_column(LargeBinary)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scopes: Mapped[list[str]] = mapped_column(ARRAY(Text))
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
