"""Task model"""
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
import enum

from .base import Base, TimestampMixin


class TaskStatus(str, enum.Enum):
    """Task status enum"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class Task(Base, TimestampMixin):
    """Follow-up task"""
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), index=True)

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(String(1000))

    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, native_enum=False),
        default=TaskStatus.TODO,
        server_default="todo",
    )

    assignee: Mapped[Optional[str]] = mapped_column(String(100))

    # Relationship
    lead: Mapped["Lead"] = relationship(back_populates="tasks")
