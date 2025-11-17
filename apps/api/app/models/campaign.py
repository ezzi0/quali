"""Campaign model for multi-platform marketing"""
from decimal import Decimal
from sqlalchemy import String, Integer, ForeignKey, Enum, Numeric, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.mutable import MutableDict
from typing import Optional
from datetime import datetime
import enum

from .base import Base, TimestampMixin


class CampaignPlatform(str, enum.Enum):
    """Platform enum"""
    META = "meta"
    GOOGLE = "google"
    TIKTOK = "tiktok"
    MULTI = "multi"


class CampaignObjective(str, enum.Enum):
    """Campaign objective enum"""
    LEAD_GENERATION = "lead_generation"
    TRAFFIC = "traffic"
    CONVERSIONS = "conversions"
    REACH = "reach"
    BRAND_AWARENESS = "brand_awareness"


class CampaignStatus(str, enum.Enum):
    """Campaign status enum"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Campaign(Base, TimestampMixin):
    """
    Marketing campaign across one or more platforms.
    """
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Identity
    name: Mapped[str] = mapped_column(String(200))
    platform: Mapped[CampaignPlatform] = mapped_column(
        Enum(CampaignPlatform, native_enum=False, validate_strings=True)
    )
    objective: Mapped[CampaignObjective] = mapped_column(
        Enum(CampaignObjective, native_enum=False, validate_strings=True)
    )
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus, native_enum=False, validate_strings=True),
        default=CampaignStatus.DRAFT
    )
    
    # Budget
    budget_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    budget_daily: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    currency: Mapped[str] = mapped_column(String(3), default="AED")
    
    # Spend tracking
    spend_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    spend_today: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    
    # Schedule
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Platform IDs
    platform_campaign_id: Mapped[Optional[str]] = mapped_column(String(200))
    platform_metadata: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSONB), default=dict)
    
    # Strategy & hypothesis
    strategy: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSONB), default=dict)
    # Example:
    # {
    #   "target_personas": [1, 2, 3],
    #   "geos": ["Dubai", "Abu Dhabi"],
    #   "expected_cac": 850,
    #   "expected_volume": 500,
    #   "hypothesis": "High-income professionals respond to luxury positioning"
    # }
    
    # Relationships
    ad_sets: Mapped[list["AdSet"]] = relationship(back_populates="campaign", cascade="all, delete-orphan")


class AdSet(Base, TimestampMixin):
    """
    Ad Set - targeting + budget group within a campaign.
    """
    __tablename__ = "ad_sets"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"))
    audience_id: Mapped[Optional[int]] = mapped_column(ForeignKey("audiences.id"))
    
    # Identity
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus, native_enum=False, validate_strings=True),
        default=CampaignStatus.DRAFT
    )
    
    # Budget
    budget_daily: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    bid_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    bid_strategy: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Spend tracking
    spend_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    spend_today: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    
    # Targeting overrides (beyond audience)
    geo: Mapped[Optional[str]] = mapped_column(String(200))
    schedule: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSONB), default=dict)
    
    # Platform IDs
    platform_adset_id: Mapped[Optional[str]] = mapped_column(String(200))
    platform_metadata: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSONB), default=dict)
    
    # Optimization
    optimization_goal: Mapped[Optional[str]] = mapped_column(String(50))
    # e.g., "LEAD", "LANDING_PAGE_VIEWS", "CONVERSIONS"
    
    # Relationships
    campaign: Mapped["Campaign"] = relationship(back_populates="ad_sets")
    audience: Mapped[Optional["Audience"]] = relationship(back_populates="ad_sets")
    ads: Mapped[list["Ad"]] = relationship(back_populates="ad_set", cascade="all, delete-orphan")


class Ad(Base, TimestampMixin):
    """
    Individual ad - creative + placement combination.
    """
    __tablename__ = "ads"

    id: Mapped[int] = mapped_column(primary_key=True)
    ad_set_id: Mapped[int] = mapped_column(ForeignKey("ad_sets.id"))
    creative_id: Mapped[int] = mapped_column(ForeignKey("creatives.id"))
    
    # Identity
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus, native_enum=False, validate_strings=True),
        default=CampaignStatus.DRAFT
    )
    
    # Platform IDs
    platform_ad_id: Mapped[Optional[str]] = mapped_column(String(200))
    platform_metadata: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSONB), default=dict)
    
    # Tracking
    tracking_params: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSONB), default=dict)
    # UTM parameters, conversion pixels, etc.
    
    # Relationships
    ad_set: Mapped["AdSet"] = relationship(back_populates="ads")
    creative: Mapped["Creative"] = relationship(back_populates="ads")
