"""Experiment model for A/B testing"""
from sqlalchemy import String, Integer, ForeignKey, Enum, Float, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.mutable import MutableDict
from typing import Optional
from datetime import datetime
import enum

from .base import Base, TimestampMixin


class ExperimentStatus(str, enum.Enum):
    """Experiment status enum"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"


class ExperimentType(str, enum.Enum):
    """Experiment type enum"""
    AB_TEST = "ab_test"
    MULTIVARIATE = "multivariate"
    SEQUENTIAL = "sequential"


class Experiment(Base, TimestampMixin):
    """
    A/B test or multivariate experiment.
    
    Tests hypotheses about persona targeting, creative variants, or budget allocation.
    """
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(primary_key=True)
    persona_id: Mapped[Optional[int]] = mapped_column(ForeignKey("personas.id"))
    
    # Identity
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[ExperimentType] = mapped_column(
        Enum(ExperimentType, native_enum=False, validate_strings=True)
    )
    status: Mapped[ExperimentStatus] = mapped_column(
        Enum(ExperimentStatus, native_enum=False, validate_strings=True),
        default=ExperimentStatus.DRAFT
    )
    
    # Hypothesis
    hypothesis: Mapped[str] = mapped_column(String(1000))
    # Example: "Luxury positioning outperforms investment angle for high-income persona"
    
    # Design
    design: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSONB), default=dict)
    # Example:
    # {
    #   "control": {"creative_id": 1, "audience_id": 5},
    #   "variants": [
    #     {"name": "variant_a", "creative_id": 2, "audience_id": 5},
    #     {"name": "variant_b", "creative_id": 3, "audience_id": 5}
    #   ],
    #   "split": [0.4, 0.3, 0.3],  # traffic allocation
    #   "metrics": ["ctr", "cpl", "conversion_rate"],
    #   "mde": 0.05  # minimum detectable effect
    # }
    
    # Statistical parameters
    confidence_level: Mapped[float] = mapped_column(Float, default=0.95)
    minimum_sample_size: Mapped[int] = mapped_column(Integer, default=1000)
    mde: Mapped[float] = mapped_column(Float, default=0.05)  # minimum detectable effect
    
    # Schedule
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    stop_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Stopping rules
    stop_rules: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSONB), default=dict)
    # Example:
    # {
    #   "max_duration_days": 14,
    #   "early_stop_on_significance": true,
    #   "futility_threshold": 0.1
    # }
    
    # Results
    results: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSONB), default=dict)
    # Example:
    # {
    #   "winner": "variant_a",
    #   "lift": 0.23,
    #   "p_value": 0.003,
    #   "confidence_interval": [0.15, 0.31],
    #   "recommendation": "Deploy variant_a to all traffic"
    # }
    
    # Relationships
    persona: Mapped[Optional["Persona"]] = relationship(back_populates="experiments")
