"""
Lead Persona Matcher Service

Matches incoming leads to existing marketing personas based on
profile characteristics, enabling personalized marketing and attribution.
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import select, func
import numpy as np

from ...config import get_settings
from ...logging import get_logger
from ...models import Lead, LeadProfile, Persona, PersonaStatus

settings = get_settings()
logger = get_logger(__name__)


@dataclass
class PersonaMatch:
    """Result of persona matching for a lead."""
    persona_id: int
    persona_name: str
    match_score: float  # 0-100
    confidence: float  # 0-1
    match_factors: Dict[str, float]  # Individual factor scores
    is_strong_match: bool


class LeadPersonaMatcherService:
    """
    Matches leads to marketing personas.
    
    Uses rule-based matching with weighted scoring:
    1. Budget range overlap
    2. Property type match
    3. Location match
    4. Urgency/timeline alignment
    5. Financing status
    
    This enables:
    - Personalized marketing message selection
    - Campaign attribution
    - Persona performance tracking
    """
    
    # Scoring weights for different factors
    MATCH_WEIGHTS = {
        "budget": 0.30,
        "property_type": 0.20,
        "location": 0.20,
        "urgency": 0.15,
        "financing": 0.15
    }
    
    # Threshold for strong match
    STRONG_MATCH_THRESHOLD = 70
    
    def __init__(self, db: Session):
        self.db = db
    
    def match_lead_to_personas(
        self,
        lead_id: int,
        auto_assign: bool = True,
        min_score: float = 50.0
    ) -> List[PersonaMatch]:
        """
        Match a lead to existing personas.
        
        Args:
            lead_id: Lead to match
            auto_assign: If True, assign best match to lead
            min_score: Minimum match score to consider
        
        Returns:
            List of PersonaMatch objects, sorted by score
        """
        logger.info("lead_persona_matching_started", lead_id=lead_id)
        
        # Fetch lead with profile
        lead = self.db.get(Lead, lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        profile = lead.profile
        if not profile:
            logger.warning("lead_has_no_profile", lead_id=lead_id)
            return []
        
        # Fetch active personas
        personas = self.db.execute(
            select(Persona).where(
                Persona.status.in_([PersonaStatus.ACTIVE, PersonaStatus.DRAFT])
            )
        ).scalars().all()
        
        if not personas:
            logger.warning("no_personas_found")
            return []
        
        # Calculate match score for each persona
        matches = []
        for persona in personas:
            match = self._calculate_match(lead, profile, persona)
            if match.match_score >= min_score:
                matches.append(match)
        
        # Sort by score descending
        matches.sort(key=lambda x: x.match_score, reverse=True)
        
        # Auto-assign best match if enabled
        if auto_assign and matches:
            best_match = matches[0]
            if best_match.is_strong_match:
                lead.marketing_persona_id = best_match.persona_id
                self.db.commit()
                logger.info("lead_persona_assigned",
                           lead_id=lead_id,
                           persona_id=best_match.persona_id,
                           score=best_match.match_score)
        
        logger.info("lead_persona_matching_completed",
                   lead_id=lead_id,
                   matches_found=len(matches))
        
        return matches
    
    def _calculate_match(
        self,
        lead: Lead,
        profile: LeadProfile,
        persona: Persona
    ) -> PersonaMatch:
        """Calculate match score between a lead and persona."""
        rules = persona.rules or {}
        characteristics = persona.characteristics or {}
        
        # Calculate individual factor scores (0-1)
        factors = {}
        
        # 1. Budget match
        factors["budget"] = self._calculate_budget_match(
            profile.budget_min,
            profile.budget_max,
            rules.get("budget_range")
        )
        
        # 2. Property type match
        factors["property_type"] = self._calculate_property_type_match(
            profile.property_type,
            rules.get("property_types", [])
        )
        
        # 3. Location match
        factors["location"] = self._calculate_location_match(
            profile.city,
            profile.areas or [],
            rules.get("locations", [])
        )
        
        # 4. Urgency match
        factors["urgency"] = self._calculate_urgency_match(
            profile.move_in_date,
            characteristics.get("urgency", "medium")
        )
        
        # 5. Financing match
        factors["financing"] = self._calculate_financing_match(
            profile.preapproved,
            characteristics.get("price_sensitivity", "medium")
        )
        
        # Calculate weighted score
        match_score = sum(
            factors[k] * self.MATCH_WEIGHTS[k]
            for k in factors
        ) * 100
        
        # Calculate confidence based on data availability
        confidence = self._calculate_confidence(profile, rules)
        
        return PersonaMatch(
            persona_id=persona.id,
            persona_name=persona.name,
            match_score=match_score,
            confidence=confidence,
            match_factors=factors,
            is_strong_match=match_score >= self.STRONG_MATCH_THRESHOLD
        )
    
    def _calculate_budget_match(
        self,
        lead_min: Optional[float],
        lead_max: Optional[float],
        persona_range: Optional[List[float]]
    ) -> float:
        """Calculate budget range overlap score."""
        if not lead_min and not lead_max:
            return 0.5  # No data, neutral score
        
        if not persona_range or len(persona_range) < 2:
            return 0.5  # No persona range defined
        
        lead_min = float(lead_min or 0)
        lead_max = float(lead_max or lead_min * 1.5)
        persona_min, persona_max = persona_range[0], persona_range[1]
        
        # Calculate overlap
        overlap_min = max(lead_min, persona_min)
        overlap_max = min(lead_max, persona_max)
        
        if overlap_max <= overlap_min:
            # No overlap - check how close
            gap = min(abs(lead_min - persona_max), abs(lead_max - persona_min))
            range_size = max(persona_max - persona_min, 1)
            return max(0.0, 1.0 - (gap / range_size) * 0.5)
        
        # Calculate overlap percentage
        overlap_size = overlap_max - overlap_min
        lead_range_size = max(lead_max - lead_min, 1)
        persona_range_size = max(persona_max - persona_min, 1)
        
        # Score based on overlap with both ranges
        lead_overlap_pct = overlap_size / lead_range_size
        persona_overlap_pct = overlap_size / persona_range_size
        
        return (lead_overlap_pct + persona_overlap_pct) / 2
    
    def _calculate_property_type_match(
        self,
        lead_type: Optional[str],
        persona_types: List[str]
    ) -> float:
        """Calculate property type match score."""
        if not lead_type:
            return 0.5  # No data
        
        if not persona_types:
            return 0.5  # No persona types defined
        
        lead_type_lower = lead_type.lower().strip()
        persona_types_lower = [t.lower().strip() for t in persona_types]
        
        # Exact match
        if lead_type_lower in persona_types_lower:
            return 1.0
        
        # Partial match (e.g., "apartment" matches "flat")
        type_synonyms = {
            "apartment": ["flat", "condo", "unit"],
            "villa": ["house", "detached", "standalone"],
            "townhouse": ["townhome", "row house", "terrace"],
            "penthouse": ["apartment", "flat", "luxury"],
            "studio": ["apartment", "flat", "unit"]
        }
        
        synonyms = type_synonyms.get(lead_type_lower, [])
        for syn in synonyms:
            if syn in persona_types_lower:
                return 0.8
        
        # Check if persona synonyms match lead type
        for persona_type in persona_types_lower:
            persona_synonyms = type_synonyms.get(persona_type, [])
            if lead_type_lower in persona_synonyms:
                return 0.8
        
        return 0.3  # No match
    
    def _calculate_location_match(
        self,
        lead_city: Optional[str],
        lead_areas: List[str],
        persona_locations: List[str]
    ) -> float:
        """Calculate location match score."""
        if not lead_city and not lead_areas:
            return 0.5  # No data
        
        if not persona_locations:
            return 0.5  # No persona locations defined
        
        all_lead_locations = []
        if lead_city:
            all_lead_locations.append(lead_city.lower().strip())
        all_lead_locations.extend([a.lower().strip() for a in lead_areas])
        
        persona_locations_lower = [l.lower().strip() for l in persona_locations]
        
        # Count matches
        matches = 0
        for loc in all_lead_locations:
            for persona_loc in persona_locations_lower:
                if loc in persona_loc or persona_loc in loc:
                    matches += 1
                    break
        
        if matches == 0:
            return 0.3  # No location match
        
        # Score based on proportion of matches
        match_ratio = matches / len(all_lead_locations)
        return 0.5 + (match_ratio * 0.5)
    
    def _calculate_urgency_match(
        self,
        move_in_date: Optional[str],
        persona_urgency: str
    ) -> float:
        """Calculate urgency/timeline match score."""
        if not move_in_date:
            return 0.5  # No data
        
        move_in_lower = move_in_date.lower()
        
        # Determine lead urgency
        lead_urgency = "medium"
        if any(word in move_in_lower for word in ["immediately", "asap", "urgent", "now"]):
            lead_urgency = "high"
        elif any(word in move_in_lower for word in ["flexible", "no rush", "within a year"]):
            lead_urgency = "low"
        elif any(word in move_in_lower for word in ["1 month", "30 days", "next month"]):
            lead_urgency = "high"
        elif any(word in move_in_lower for word in ["3 month", "6 month"]):
            lead_urgency = "medium"
        
        # Match urgencies
        if lead_urgency == persona_urgency:
            return 1.0
        elif abs(["low", "medium", "high"].index(lead_urgency) - 
                 ["low", "medium", "high"].index(persona_urgency)) == 1:
            return 0.7  # Adjacent urgency levels
        else:
            return 0.4  # Opposite urgency
    
    def _calculate_financing_match(
        self,
        preapproved: Optional[bool],
        price_sensitivity: str
    ) -> float:
        """Calculate financing status match score."""
        if preapproved is None:
            return 0.5  # No data
        
        # Pre-approved typically means lower price sensitivity
        if preapproved:
            if price_sensitivity == "low":
                return 1.0
            elif price_sensitivity == "medium":
                return 0.7
            else:
                return 0.5
        else:
            if price_sensitivity == "high":
                return 0.9
            elif price_sensitivity == "medium":
                return 0.7
            else:
                return 0.5
    
    def _calculate_confidence(
        self,
        profile: LeadProfile,
        rules: Dict[str, Any]
    ) -> float:
        """Calculate confidence based on data availability."""
        lead_data_points = 0
        if profile.budget_min or profile.budget_max:
            lead_data_points += 1
        if profile.property_type:
            lead_data_points += 1
        if profile.city or profile.areas:
            lead_data_points += 1
        if profile.move_in_date:
            lead_data_points += 1
        if profile.preapproved is not None:
            lead_data_points += 1
        
        persona_data_points = 0
        if rules.get("budget_range"):
            persona_data_points += 1
        if rules.get("property_types"):
            persona_data_points += 1
        if rules.get("locations"):
            persona_data_points += 1
        if rules.get("urgency"):
            persona_data_points += 1
        
        total_possible = 5
        data_availability = (lead_data_points + persona_data_points) / (total_possible * 2)
        
        return min(1.0, data_availability + 0.2)
    
    def batch_match_leads(
        self,
        lead_ids: Optional[List[int]] = None,
        auto_assign: bool = True,
        min_score: float = 50.0
    ) -> Dict[int, List[PersonaMatch]]:
        """
        Batch match multiple leads to personas.
        
        Args:
            lead_ids: Specific leads to match (None = all unassigned)
            auto_assign: If True, assign best matches
            min_score: Minimum match score
        
        Returns:
            Dict of lead_id -> list of PersonaMatch
        """
        if lead_ids is None:
            # Get all leads without persona assignment
            leads = self.db.execute(
                select(Lead).where(Lead.marketing_persona_id.is_(None))
            ).scalars().all()
            lead_ids = [l.id for l in leads]
        
        results = {}
        for lead_id in lead_ids:
            try:
                matches = self.match_lead_to_personas(
                    lead_id=lead_id,
                    auto_assign=auto_assign,
                    min_score=min_score
                )
                results[lead_id] = matches
            except Exception as e:
                logger.error("lead_matching_failed", lead_id=lead_id, error=str(e))
                results[lead_id] = []
        
        logger.info("batch_matching_completed",
                   total_leads=len(lead_ids),
                   assigned=sum(1 for matches in results.values() if matches and matches[0].is_strong_match))
        
        return results
    
    def get_persona_lead_distribution(self) -> Dict[int, Dict[str, Any]]:
        """
        Get distribution of leads across personas.
        
        Returns:
            Dict of persona_id -> {name, lead_count, avg_score, ...}
        """
        personas = self.db.execute(
            select(Persona).where(Persona.status == PersonaStatus.ACTIVE)
        ).scalars().all()
        
        distribution = {}
        
        for persona in personas:
            # Count leads assigned to this persona
            lead_count = self.db.execute(
                select(func.count(Lead.id)).where(
                    Lead.marketing_persona_id == persona.id
                )
            ).scalar()
            
            distribution[persona.id] = {
                "name": persona.name,
                "lead_count": lead_count or 0,
                "sample_size": persona.sample_size,
                "status": persona.status.value
            }
        
        # Count unassigned leads
        unassigned = self.db.execute(
            select(func.count(Lead.id)).where(
                Lead.marketing_persona_id.is_(None)
            )
        ).scalar()
        
        distribution[0] = {
            "name": "Unassigned",
            "lead_count": unassigned or 0,
            "sample_size": 0,
            "status": "n/a"
        }
        
        return distribution

