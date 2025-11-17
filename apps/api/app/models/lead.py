"""Lead and LeadProfile models"""
from decimal import Decimal
from sqlalchemy import String, Integer, ForeignKey, Enum, ARRAY, Numeric, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.mutable import MutableDict, MutableList
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
        Enum(LeadSource, native_enum=False, validate_strings=True))
    persona: Mapped[Optional[LeadPersona]] = mapped_column(
        Enum(LeadPersona, native_enum=False, validate_strings=True))
    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus, native_enum=False, validate_strings=True),
        default=LeadStatus.NEW,
        server_default="new",
    )

    contact_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("contacts.id", ondelete="SET NULL"))
    
    # Marketing integration
    marketing_persona_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("personas.id", ondelete="SET NULL"))
    attribution_data: Mapped[Optional[dict]] = mapped_column(
        MutableDict.as_mutable(JSONB))

    # Relationships
    contact: Mapped[Optional["Contact"]] = relationship(back_populates="leads")
    profile: Mapped[Optional["LeadProfile"]] = relationship(
        back_populates="lead",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    qualifications: Mapped[list["Qualification"]] = relationship(
        back_populates="lead",
        cascade="all, delete-orphan",
        single_parent=True,
    )
    activities: Mapped[list["Activity"]] = relationship(
        back_populates="lead",
        cascade="all, delete-orphan",
        single_parent=True,
    )
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="lead",
        cascade="all, delete-orphan",
        single_parent=True,
    )
    sessions: Mapped[list["Session"]] = relationship(
        back_populates="lead",
        cascade="all, delete-orphan",
        single_parent=True,
    )


class LeadProfile(Base, TimestampMixin):
    """Detailed lead preferences and requirements"""
    __tablename__ = "lead_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"),
        unique=True,
    )

    # Geo
    city: Mapped[Optional[str]] = mapped_column(String(100))
    areas: Mapped[Optional[list[str]]] = mapped_column(
        MutableList.as_mutable(ARRAY(String)))

    # Property
    property_type: Mapped[Optional[str]] = mapped_column(
        String(50))  # apartment, villa, townhouse
    beds: Mapped[Optional[int]] = mapped_column(Integer)
    min_size_m2: Mapped[Optional[int]] = mapped_column(Integer)

    # Budget
    budget_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    budget_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
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
    preferences: Mapped[Optional[list[str]]] = mapped_column(
        MutableList.as_mutable(ARRAY(String)))

    # Relationship
    lead: Mapped["Lead"] = relationship(back_populates="profile")
