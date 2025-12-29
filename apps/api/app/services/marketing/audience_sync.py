"""
Audience Sync Service

Synchronizes personas to platform-specific audiences across
Meta, Google, and TikTok ad platforms.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from ...config import get_settings
from ...logging import get_logger
from ...models import Persona, Audience, AudiencePlatform, AudienceStatus
from ...adapters.meta_marketing import MetaMarketingAdapter
from ...adapters.google_ads import GoogleAdsAdapter
from ...adapters.tiktok_ads import TikTokAdsAdapter

settings = get_settings()
logger = get_logger(__name__)


@dataclass
class AudienceSyncResult:
    """Result of syncing an audience to a platform."""
    audience_id: int
    platform: str
    status: str
    platform_audience_id: Optional[str]
    estimated_size: Optional[int]
    error: Optional[str]


class AudienceSyncService:
    """
    Syncs personas to platform-specific audiences.
    
    Translates persona rules into platform targeting specs:
    - Meta: Custom audiences, lookalikes, interest targeting
    - Google: Customer match, affinity audiences
    - TikTok: Custom audiences, interest categories
    
    Features:
    1. Create platform audiences from personas
    2. Update audience targeting based on persona changes
    3. Sync audience sizes back to database
    4. Manage audience lifecycle
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.meta_adapter = MetaMarketingAdapter(dry_run=True)
        self.google_adapter = GoogleAdsAdapter(dry_run=True)
        self.tiktok_adapter = TikTokAdsAdapter(dry_run=True)
    
    def sync_persona_to_platforms(
        self,
        persona_id: int,
        platforms: List[str] = None
    ) -> List[AudienceSyncResult]:
        """
        Sync a persona to specified platforms.
        
        Args:
            persona_id: Persona to sync
            platforms: Platforms to sync to (default: all)
        
        Returns:
            List of sync results per platform
        """
        logger.info("audience_sync_started", persona_id=persona_id)
        
        persona = self.db.get(Persona, persona_id)
        if not persona:
            raise ValueError(f"Persona {persona_id} not found")
        
        platforms = platforms or ["meta", "google", "tiktok"]
        results = []
        
        for platform in platforms:
            try:
                result = self._sync_to_platform(persona, platform)
                results.append(result)
            except Exception as e:
                logger.error("audience_sync_failed",
                           persona_id=persona_id,
                           platform=platform,
                           error=str(e))
                results.append(AudienceSyncResult(
                    audience_id=0,
                    platform=platform,
                    status="failed",
                    platform_audience_id=None,
                    estimated_size=None,
                    error=str(e)
                ))
        
        logger.info("audience_sync_completed",
                   persona_id=persona_id,
                   results=[r.status for r in results])
        
        return results
    
    def _sync_to_platform(
        self,
        persona: Persona,
        platform: str
    ) -> AudienceSyncResult:
        """Sync persona to a specific platform."""
        # Check for existing audience
        existing = self.db.execute(
            select(Audience).where(
                Audience.persona_id == persona.id,
                Audience.platform == AudiencePlatform(platform)
            )
        ).scalar_one_or_none()
        
        # Translate persona rules to platform targeting
        targeting = self._translate_targeting(persona.rules or {}, platform)
        
        if existing:
            # Update existing audience
            audience = existing
            audience.targeting = targeting
            audience.status = AudienceStatus.PENDING
        else:
            # Create new audience
            audience = Audience(
                persona_id=persona.id,
                platform=AudiencePlatform(platform),
                name=f"{persona.name} - {platform.title()}",
                status=AudienceStatus.PENDING,
                targeting=targeting
            )
            self.db.add(audience)
        
        self.db.flush()
        
        # Sync to platform
        platform_id = None
        estimated_size = None
        
        if platform == "meta":
            platform_id, estimated_size = self._sync_to_meta(audience, targeting)
        elif platform == "google":
            platform_id, estimated_size = self._sync_to_google(audience, targeting)
        elif platform == "tiktok":
            platform_id, estimated_size = self._sync_to_tiktok(audience, targeting)
        
        # Update audience record
        if platform_id:
            audience.platform_audience_id = platform_id
            audience.status = AudienceStatus.ACTIVE
        
        if estimated_size:
            audience.estimated_size = estimated_size
        
        self.db.commit()
        
        return AudienceSyncResult(
            audience_id=audience.id,
            platform=platform,
            status="synced" if platform_id else "created",
            platform_audience_id=platform_id,
            estimated_size=estimated_size,
            error=None
        )
    
    def _translate_targeting(
        self,
        rules: Dict[str, Any],
        platform: str
    ) -> Dict[str, Any]:
        """Translate persona rules to platform-specific targeting."""
        if platform == "meta":
            return self._translate_to_meta(rules)
        elif platform == "google":
            return self._translate_to_google(rules)
        elif platform == "tiktok":
            return self._translate_to_tiktok(rules)
        return {}
    
    def _translate_to_meta(self, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Translate to Meta targeting spec."""
        targeting = {
            "geo_locations": {
                "countries": ["AE"],  # Default UAE
            },
            "age_min": 25,
            "age_max": 55,
        }
        
        # Location rules
        locations = rules.get("locations", [])
        if locations:
            targeting["geo_locations"]["cities"] = [
                {"name": loc} for loc in locations[:10]
            ]
        
        # Budget-based interest targeting
        budget_range = rules.get("budget_range", [])
        if budget_range and len(budget_range) >= 2:
            avg_budget = sum(budget_range) / 2
            
            if avg_budget > 2000000:  # Luxury
                targeting["interests"] = [
                    {"name": "Luxury real estate"},
                    {"name": "High net worth"},
                    {"name": "Luxury lifestyle"}
                ]
                targeting["behaviors"] = [
                    {"name": "Frequent international travelers"}
                ]
            elif avg_budget > 1000000:  # Premium
                targeting["interests"] = [
                    {"name": "Real estate investing"},
                    {"name": "Property investment"},
                    {"name": "Finance"}
                ]
            else:  # Standard
                targeting["interests"] = [
                    {"name": "Real estate"},
                    {"name": "Home buying"},
                    {"name": "Apartments"}
                ]
        
        # Property type targeting
        property_types = rules.get("property_types", [])
        if "villa" in [p.lower() for p in property_types]:
            targeting.setdefault("interests", []).append(
                {"name": "Villas and houses"}
            )
        
        return targeting
    
    def _translate_to_google(self, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Translate to Google Ads targeting spec."""
        targeting = {
            "geo_targets": {
                "countries": ["AE"],
            }
        }
        
        # Location targeting
        locations = rules.get("locations", [])
        if locations:
            targeting["geo_targets"]["cities"] = locations[:10]
        
        # Affinity audiences based on budget
        budget_range = rules.get("budget_range", [])
        if budget_range and len(budget_range) >= 2:
            avg_budget = sum(budget_range) / 2
            
            if avg_budget > 2000000:
                targeting["affinity_audiences"] = [
                    "Luxury shoppers",
                    "High-end real estate enthusiasts"
                ]
            else:
                targeting["affinity_audiences"] = [
                    "Property buyers",
                    "Real estate enthusiasts"
                ]
        
        # In-market audiences
        targeting["in_market_audiences"] = [
            "Real estate",
            "Residential properties"
        ]
        
        # Keywords for search
        property_types = rules.get("property_types", [])
        targeting["keywords"] = [
            f"{pt} for sale dubai" for pt in property_types[:5]
        ] if property_types else ["property for sale dubai"]
        
        return targeting
    
    def _translate_to_tiktok(self, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Translate to TikTok targeting spec."""
        targeting = {
            "location_ids": ["AE"],  # UAE
            "gender": "GENDER_UNLIMITED",
            "age_groups": ["AGE_25_34", "AGE_35_44", "AGE_45_54"],
        }
        
        # Location targeting
        locations = rules.get("locations", [])
        if locations:
            # TikTok uses different location IDs
            targeting["location_names"] = locations[:10]
        
        # Interest categories based on budget and property type
        budget_range = rules.get("budget_range", [])
        interests = []
        
        if budget_range and len(budget_range) >= 2:
            avg_budget = sum(budget_range) / 2
            
            if avg_budget > 1500000:
                interests.extend([
                    "Luxury lifestyle",
                    "Finance & investing",
                    "Travel & tourism"
                ])
            else:
                interests.extend([
                    "Home & garden",
                    "Real estate",
                    "Personal finance"
                ])
        
        targeting["interest_categories"] = interests
        
        # Behaviors
        targeting["behaviors"] = [
            "Real estate app users",
            "Property seekers"
        ]
        
        return targeting
    
    def _sync_to_meta(
        self,
        audience: Audience,
        targeting: Dict[str, Any]
    ) -> tuple:
        """Sync audience to Meta."""
        # In production, this would create/update a saved audience
        # For now, return mock data
        logger.info("meta_audience_sync", audience_id=audience.id)
        
        # Simulate audience creation
        platform_id = f"meta_aud_{audience.id}_{int(datetime.utcnow().timestamp())}"
        estimated_size = 150000  # Mock estimate
        
        return platform_id, estimated_size
    
    def _sync_to_google(
        self,
        audience: Audience,
        targeting: Dict[str, Any]
    ) -> tuple:
        """Sync audience to Google Ads."""
        logger.info("google_audience_sync", audience_id=audience.id)
        
        platform_id = f"google_aud_{audience.id}_{int(datetime.utcnow().timestamp())}"
        estimated_size = 120000
        
        return platform_id, estimated_size
    
    def _sync_to_tiktok(
        self,
        audience: Audience,
        targeting: Dict[str, Any]
    ) -> tuple:
        """Sync audience to TikTok."""
        logger.info("tiktok_audience_sync", audience_id=audience.id)
        
        platform_id = f"tiktok_aud_{audience.id}_{int(datetime.utcnow().timestamp())}"
        estimated_size = 200000
        
        return platform_id, estimated_size
    
    def sync_all_personas(
        self,
        platforms: List[str] = None
    ) -> Dict[int, List[AudienceSyncResult]]:
        """
        Sync all active personas to platforms.
        
        Args:
            platforms: Platforms to sync to
        
        Returns:
            Dict of persona_id -> list of results
        """
        from ...models import PersonaStatus
        
        personas = self.db.execute(
            select(Persona).where(Persona.status == PersonaStatus.ACTIVE)
        ).scalars().all()
        
        results = {}
        for persona in personas:
            try:
                results[persona.id] = self.sync_persona_to_platforms(
                    persona.id, platforms
                )
            except Exception as e:
                logger.error("persona_sync_failed",
                           persona_id=persona.id,
                           error=str(e))
                results[persona.id] = []
        
        return results
    
    def get_audience_status(self, persona_id: int) -> Dict[str, Dict[str, Any]]:
        """Get sync status for all audiences of a persona."""
        audiences = self.db.execute(
            select(Audience).where(Audience.persona_id == persona_id)
        ).scalars().all()
        
        status = {}
        for audience in audiences:
            status[audience.platform.value] = {
                "audience_id": audience.id,
                "status": audience.status.value,
                "platform_audience_id": audience.platform_audience_id,
                "estimated_size": audience.estimated_size,
                "last_updated": audience.updated_at.isoformat() if audience.updated_at else None
            }
        
        return status
    
    def refresh_audience_sizes(self) -> Dict[str, int]:
        """
        Refresh audience size estimates from platforms.
        
        Returns:
            Count of audiences updated per platform
        """
        updated = {"meta": 0, "google": 0, "tiktok": 0}
        
        audiences = self.db.execute(
            select(Audience).where(
                Audience.status == AudienceStatus.ACTIVE,
                Audience.platform_audience_id.isnot(None)
            )
        ).scalars().all()
        
        for audience in audiences:
            try:
                # In production, would call platform APIs to get current size
                # For now, simulate slight variation
                import random
                if audience.estimated_size:
                    variation = random.uniform(0.95, 1.05)
                    audience.estimated_size = int(audience.estimated_size * variation)
                    updated[audience.platform.value] += 1
            except Exception as e:
                logger.warning("audience_size_refresh_failed",
                             audience_id=audience.id,
                             error=str(e))
        
        self.db.commit()
        
        return updated

