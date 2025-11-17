"""Marketing metrics model for performance tracking"""
from decimal import Decimal
from sqlalchemy import String, Integer, ForeignKey, Date, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.mutable import MutableDict
from typing import Optional
from datetime import date

from .base import Base, TimestampMixin


class MarketingMetric(Base, TimestampMixin):
    """
    Daily aggregated marketing metrics by campaign/ad_set/ad.
    
    Updated by sync jobs pulling from platform APIs.
    """
    __tablename__ = "marketing_metrics"
    
    __table_args__ = (
        UniqueConstraint('date', 'campaign_id', 'ad_set_id', 'ad_id', name='uix_metrics_date_campaign_adset_ad'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Date
    date: Mapped[date] = mapped_column(Date, index=True)
    
    # Hierarchy (nullable to allow rollups)
    campaign_id: Mapped[Optional[int]] = mapped_column(ForeignKey("campaigns.id"), index=True)
    ad_set_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ad_sets.id"))
    ad_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ads.id"))
    
    # Platform
    platform: Mapped[str] = mapped_column(String(50))
    channel: Mapped[str] = mapped_column(String(50))  # facebook, instagram, google_search, etc.
    
    # Top-of-funnel
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    reach: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    
    # Engagement
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    saves: Mapped[int] = mapped_column(Integer, default=0)
    
    # Conversions
    leads: Mapped[int] = mapped_column(Integer, default=0)
    qualified_leads: Mapped[int] = mapped_column(Integer, default=0)
    appointments: Mapped[int] = mapped_column(Integer, default=0)
    viewings: Mapped[int] = mapped_column(Integer, default=0)
    contracts: Mapped[int] = mapped_column(Integer, default=0)
    closed_won: Mapped[int] = mapped_column(Integer, default=0)
    
    # Financial
    spend: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    revenue: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    currency: Mapped[str] = mapped_column(String(3), default="AED")
    
    # Calculated rates (for fast queries)
    ctr: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))  # click-through rate
    cpc: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))  # cost per click
    cpl: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))  # cost per lead
    cpa: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))  # cost per acquisition
    roas: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))  # return on ad spend
    conversion_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))
    
    # Raw data from platform
    platform_data: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSONB), default=dict)
