"""Session model"""
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from .base import Base, TimestampMixin


class Session(Base, TimestampMixin):
    """Chat/interaction session"""
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), nullable=True)

    channel: Mapped[str] = mapped_column(String(50))  # web, whatsapp, etc.
    session_key: Mapped[str] = mapped_column(
        String(255), unique=True, index=True)

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Relationship
    lead: Mapped[Optional["Lead"]] = relationship(
        back_populates="sessions",
        passive_deletes=True,
    )
