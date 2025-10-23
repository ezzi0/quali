"""Qualification model"""
from sqlalchemy import String, Integer, ForeignKey, Boolean, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from .base import Base, TimestampMixin


class Qualification(Base, TimestampMixin):
    """AI qualification result"""
    __tablename__ = "qualifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), index=True)

    score: Mapped[int] = mapped_column(Integer)  # 0-100
    qualified: Mapped[bool] = mapped_column(Boolean)

    reasons: Mapped[list[str]] = mapped_column(ARRAY(String))
    missing_info: Mapped[list[str]] = mapped_column(ARRAY(String))
    suggested_next_step: Mapped[str] = mapped_column(String(100))

    # Top matches stored as JSONB
    top_matches: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Relationship
    lead: Mapped["Lead"] = relationship(back_populates="qualifications")
