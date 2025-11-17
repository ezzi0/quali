"""Unit/inventory model"""
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, Enum, ARRAY
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

    # Pricing
    price: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    currency: Mapped[str] = mapped_column(
        String(3), default="AED", server_default="AED")

    # Physical
    area_m2: Mapped[int] = mapped_column(Integer)
    beds: Mapped[int] = mapped_column(Integer)
    baths: Mapped[Optional[int]] = mapped_column(Integer)

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

    # Features/amenities
    features: Mapped[Optional[list[str]]] = mapped_column(
        MutableList.as_mutable(ARRAY(String)))

    # Description
    description: Mapped[Optional[str]] = mapped_column(String(2000))
