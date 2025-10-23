"""Lead and LeadProfile models"""
from sqlalchemy import String, Integer, ForeignKey, Enum, ARRAY, Numeric, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
import enum

from .base import Base, TimestampMixin


class LeadSource(str, enum.Enum):
    """Lead source enum"""
    WHATSAPP = "whatsapp"
    LEAD_AD = "lead_ad"
    WEB = "web"


class LeadPersona(str, enum.Enum):
    """Lead persona enum"""
    BUYER = "buyer"
    RENTER = "renter"
    SELLER = "seller"


class LeadStatus(str, enum.Enum):
    """Lead status enum"""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    VIEWING = "viewing"
    OFFER = "offer"
    WON = "won"
    LOST = "lost"
    NURTURE = "nurture"


class Lead(Base, TimestampMixin):
    """Lead entity - sales opportunity"""
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[LeadSource] = mapped_column(
        Enum(LeadSource, native_enum=False))
    persona: Mapped[Optional[LeadPersona]] = mapped_column(
        Enum(LeadPersona, native_enum=False))
    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus, native_enum=False),
        default=LeadStatus.NEW,
        server_default="new",
    )

    contact_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("contacts.id"))

    # Relationships
    contact: Mapped[Optional["Contact"]] = relationship(back_populates="leads")
    profile: Mapped[Optional["LeadProfile"]] = relationship(
        back_populates="lead", uselist=False)
    qualifications: Mapped[list["Qualification"]
                           ] = relationship(back_populates="lead")
    activities: Mapped[list["Activity"]] = relationship(back_populates="lead")
    tasks: Mapped[list["Task"]] = relationship(back_populates="lead")
    sessions: Mapped[list["Session"]] = relationship(back_populates="lead")


class LeadProfile(Base, TimestampMixin):
    """Detailed lead preferences and requirements"""
    __tablename__ = "lead_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), unique=True)

    # Geo
    city: Mapped[Optional[str]] = mapped_column(String(100))
    areas: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String))

    # Property
    property_type: Mapped[Optional[str]] = mapped_column(
        String(50))  # apartment, villa, townhouse
    beds: Mapped[Optional[int]] = mapped_column(Integer)
    min_size_m2: Mapped[Optional[int]] = mapped_column(Integer)

    # Budget
    budget_min: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    budget_max: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    currency: Mapped[str] = mapped_column(
        String(3), default="AED", server_default="AED")

    # Timeline
    move_in_date: Mapped[Optional[str]] = mapped_column(String(50))
    flexible: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true")

    # Financing
    preapproved: Mapped[Optional[bool]] = mapped_column(Boolean)
    financing_notes: Mapped[Optional[str]] = mapped_column(String(500))

    # Preferences (array of strings)
    preferences: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String))

    # Relationship
    lead: Mapped["Lead"] = relationship(back_populates="profile")
