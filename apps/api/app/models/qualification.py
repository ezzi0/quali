"""Qualification model"""
from decimal import Decimal
from sqlalchemy import String, Integer, ForeignKey, Boolean, ARRAY, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.mutable import MutableDict, MutableList
from typing import Optional

from .base import Base, TimestampMixin


class Qualification(Base, TimestampMixin):
    """AI qualification result"""
    __tablename__ = "qualifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), index=True)

    score: Mapped[int] = mapped_column(Integer)  # 0-100
    qualified: Mapped[bool] = mapped_column(Boolean)

    reasons: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(ARRAY(String)))
    missing_info: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(ARRAY(String)))
    suggested_next_step: Mapped[str] = mapped_column(String(100))

    # Top matches stored as JSONB
    top_matches: Mapped[Optional[dict]] = mapped_column(
        MutableDict.as_mutable(JSONB))
    
    # Marketing integration
    predicted_ltv: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    acquisition_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))

    # Relationship
    lead: Mapped["Lead"] = relationship(
        back_populates="qualifications",
        passive_deletes=True,
    )
