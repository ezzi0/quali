"""Activity/timeline model"""
from sqlalchemy import String, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.mutable import MutableDict
from typing import Optional
import enum

from .base import Base, TimestampMixin


class ActivityType(str, enum.Enum):
    """Activity type enum"""
    MESSAGE = "message"
    NOTE = "note"
    CALL = "call"
    MEETING = "meeting"
    STATUS_CHANGE = "status_change"
    EMAIL = "email"
    WHATSAPP = "whatsapp"


class Activity(Base, TimestampMixin):
    """Timeline activity for a lead"""
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), index=True)

    type: Mapped[ActivityType] = mapped_column(
        Enum(ActivityType, native_enum=False, validate_strings=True))

    # Flexible payload
    payload: Mapped[Optional[dict]] = mapped_column(
        MutableDict.as_mutable(JSONB))

    # Relationship
    lead: Mapped["Lead"] = relationship(
        back_populates="activities",
        passive_deletes=True,
    )
