"""Shared qualification schema"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any


class LeadQualification(BaseModel):
    """Structured output from qualification agent"""
    qualified: bool
    score: int = Field(ge=0, le=100, description="Lead quality score 0-100")
    reasons: List[str] = Field(description="Why qualified or not")
    missing_info: List[str] = Field(
        description="What information is still needed")
    suggested_next_step: str = Field(
        description="Next action: schedule_viewing, human_followup, or nurture"
    )
    top_matches: List[Dict[str, Any]] = Field(
        description="Top matching units with id, title, price, area_m2, location"
    )
