"""Auth user model (present but unused in no-auth MVP)"""
from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
import enum

from .base import Base, TimestampMixin


class UserRole(str, enum.Enum):
    """User role enum"""
    ADMIN = "admin"
    AGENT = "agent"


class AuthUser(Base, TimestampMixin):
    """User account - for future use"""
    __tablename__ = "auth_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, validate_strings=True),
        default=UserRole.AGENT,
        server_default="agent",
    )
    name: Mapped[Optional[str]] = mapped_column(String(255))
