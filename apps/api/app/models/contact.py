"""Contact model"""
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from .base import Base, TimestampMixin


class Contact(Base, TimestampMixin):
    """Contact entity - person interacting with system"""
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    locale: Mapped[str] = mapped_column(
        String(10), default="en", server_default="en")

    # Consent flags
    consent_sms: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false")
    consent_email: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false")
    consent_whatsapp: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false")

    # Relationships
    leads: Mapped[list["Lead"]] = relationship(back_populates="contact")
