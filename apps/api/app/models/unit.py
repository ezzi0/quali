"""Unit/inventory model"""
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, Enum, ARRAY, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.mutable import MutableList
from typing import Optional
import enum

from .base import Base, TimestampMixin


class UnitStatus(str, enum.Enum):
    """Unit availability status"""
    AVAILABLE = "available"
    RESERVED = "reserved"
    SOLD = "sold"
    RENTED = "rented"


class Unit(Base, TimestampMixin):
    """Real estate unit/property"""
    __tablename__ = "units"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[Optional[str]] = mapped_column(String(255))
    developer: Mapped[Optional[str]] = mapped_column(String(255))
    image_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Pricing
    price: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    currency: Mapped[str] = mapped_column(
        String(3), default="AED", server_default="AED")
    price_display: Mapped[Optional[str]] = mapped_column(String(50))
    payment_plan: Mapped[Optional[str]] = mapped_column(String(50))

    # Physical
    area_m2: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    beds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    baths: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bedrooms_label: Mapped[Optional[str]] = mapped_column(String(100))
    unit_sizes: Mapped[Optional[str]] = mapped_column(String(100))

    # Location
    location: Mapped[str] = mapped_column(String(255), index=True)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    area: Mapped[Optional[str]] = mapped_column(String(100))

    # Type
    # apartment, villa, etc.
    property_type: Mapped[str] = mapped_column(String(50), index=True)

    # Status
    status: Mapped[UnitStatus] = mapped_column(
        Enum(UnitStatus, native_enum=False, validate_strings=True),
        default=UnitStatus.AVAILABLE,
        server_default="available",
        index=True,
    )
    active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true")
    featured: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false")

    # Timeline & ROI
    handover: Mapped[Optional[str]] = mapped_column(String(50))
    handover_year: Mapped[Optional[int]] = mapped_column(Integer)
    roi: Mapped[Optional[str]] = mapped_column(String(50))

    # Features/amenities
    features: Mapped[Optional[list[str]]] = mapped_column(
        MutableList.as_mutable(ARRAY(String)))

    # Description
    description: Mapped[Optional[str]] = mapped_column(String(2000))
