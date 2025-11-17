"""Audience model for platform-specific targeting"""
from sqlalchemy import String, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.mutable import MutableDict
from typing import Optional
import enum

from .base import Base, TimestampMixin


class AudiencePlatform(str, enum.Enum):
    """Platform enum"""
    META = "meta"  # Facebook + Instagram
    GOOGLE = "google"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"


class AudienceStatus(str, enum.Enum):
    """Audience status enum"""
    DRAFT = "draft"
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class Audience(Base, TimestampMixin):
    """
    Platform-specific audience definition.
    
    Translates persona rules into platform targeting parameters.
    """
    __tablename__ = "audiences"

    id: Mapped[int] = mapped_column(primary_key=True)
    persona_id: Mapped[int] = mapped_column(ForeignKey("personas.id"))
    
    # Platform
    platform: Mapped[AudiencePlatform] = mapped_column(
        Enum(AudiencePlatform, native_enum=False, validate_strings=True)
    )
    
    # Identity
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[AudienceStatus] = mapped_column(
        Enum(AudienceStatus, native_enum=False, validate_strings=True),
        default=AudienceStatus.DRAFT
    )
    
    # Targeting definition (platform-specific)
    targeting: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSONB), default=dict)
    # Example for Meta:
    # {
    #   "geo_locations": {"countries": ["AE"], "cities": [{"key": "2211096", "name": "Dubai"}]},
    #   "age_min": 25,
    #   "age_max": 55,
    #   "interests": [{"id": "6003139266461", "name": "Real estate"}],
    #   "behaviors": [{"id": "6015559470583", "name": "Likely to move"}],
    #   "income": ["top_10_percent"]
    # }
    
    # Size estimates
    estimated_size: Mapped[Optional[int]] = mapped_column(Integer)
    size_lower: Mapped[Optional[int]] = mapped_column(Integer)
    size_upper: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Platform IDs
    platform_audience_id: Mapped[Optional[str]] = mapped_column(String(200))
    platform_metadata: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSONB), default=dict)
    
    # Relationships
    persona: Mapped["Persona"] = relationship(back_populates="audiences")
    ad_sets: Mapped[list["AdSet"]] = relationship(back_populates="audience")
