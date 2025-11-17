"""Persona model for marketing segmentation"""
from decimal import Decimal
from sqlalchemy import String, Integer, Enum, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.mutable import MutableDict
from typing import Optional
import enum

from .base import Base, TimestampMixin


class PersonaStatus(str, enum.Enum):
    """Persona status enum"""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class Persona(Base, TimestampMixin):
    """
    Marketing persona - behavioral segments discovered from lead data.
    
    Generated through clustering analysis and LLM labeling.
    Used for targeted campaign creation.
    """
    __tablename__ = "personas"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Identity
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(String(1000))
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[PersonaStatus] = mapped_column(
        Enum(PersonaStatus, native_enum=False, validate_strings=True),
        default=PersonaStatus.DRAFT
    )
    
    # Segmentation criteria (from clustering)
    rules: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSONB), default=dict)
    # Example: {
    #   "budget_range": [100000, 300000],
    #   "property_types": ["apartment", "villa"],
    #   "locations": ["Dubai Marina", "Downtown"],
    #   "urgency": "high"
    # }
    
    # Behavioral characteristics
    characteristics: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSONB), default=dict)
    # Example: {
    #   "decision_speed": "fast",
    #   "price_sensitivity": "low",
    #   "feature_priorities": ["location", "amenities", "size"]
    # }
    
    # Messaging & positioning
    messaging: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSONB), default=dict)
    # Example: {
    #   "hooks": ["Luxury waterfront living", "Investment opportunity"],
    #   "objections": ["Too expensive" -> "Long-term value"],
    #   "tone": "aspirational"
    # }
    
    # Performance metrics
    metrics: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSONB), default=dict)
    # Example: {
    #   "total_leads": 450,
    #   "qualified_rate": 0.72,
    #   "avg_ltv": 15000,
    #   "avg_cac": 850
    # }
    
    # Statistical confidence
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    
    # Relationships
    audiences: Mapped[list["Audience"]] = relationship(back_populates="persona", cascade="all, delete-orphan")
    creatives: Mapped[list["Creative"]] = relationship(back_populates="persona")
    experiments: Mapped[list["Experiment"]] = relationship(back_populates="persona")
