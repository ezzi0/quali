"""SQLAlchemy models"""
from .base import Base
from .contact import Contact
from .lead import Lead, LeadProfile
from .qualification import Qualification
from .unit import Unit
from .activity import Activity
from .task import Task
from .session import Session
from .auth_user import AuthUser
# Marketing models
from .persona import Persona, PersonaStatus
from .audience import Audience, AudiencePlatform, AudienceStatus
from .creative import Creative, CreativeFormat, CreativeStatus
from .campaign import Campaign, AdSet, Ad, CampaignPlatform, CampaignObjective, CampaignStatus
from .experiment import Experiment, ExperimentStatus, ExperimentType
from .marketing_metric import MarketingMetric

__all__ = [
    "Base",
    "Contact",
    "Lead",
    "LeadProfile",
    "Qualification",
    "Unit",
    "Activity",
    "Task",
    "Session",
    "AuthUser",
    # Marketing
    "Persona",
    "PersonaStatus",
    "Audience",
    "AudiencePlatform",
    "AudienceStatus",
    "Creative",
    "CreativeFormat",
    "CreativeStatus",
    "Campaign",
    "AdSet",
    "Ad",
    "CampaignPlatform",
    "CampaignObjective",
    "CampaignStatus",
    "Experiment",
    "ExperimentStatus",
    "ExperimentType",
    "MarketingMetric",
]
