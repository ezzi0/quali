"""
Marketing Agent Orchestrator

Coordinates the full marketing campaign lifecycle from persona discovery
through creative generation, campaign deployment, and budget optimization.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from openai import OpenAI

from ..config import get_settings
from ..logging import get_logger
from ..models import Persona, Creative, Campaign, AdSet, Ad, CreativeFormat
from ..services.marketing.persona_discovery import PersonaDiscoveryService
from ..services.marketing.creative_generator import CreativeGeneratorService
from ..services.marketing.budget_optimizer import BudgetOptimizerService
from ..adapters.meta_marketing import MetaMarketingAdapter

settings = get_settings()
logger = get_logger(__name__)


class MarketingAgent:
    """
    Marketing Agent orchestrates the full campaign lifecycle.
    
    Process:
    1. Discover personas from qualified leads
    2. Generate creatives for each persona
    3. Deploy campaigns to advertising platforms
    4. Monitor and optimize budget allocation
    5. Track attribution and close the loop
    
    This agent works in tandem with the QualificationAgent:
    - QualificationAgent: Inbound lead qualification
    - MarketingAgent: Outbound campaign generation
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        
        # Initialize services
        self.persona_service = PersonaDiscoveryService(db)
        self.creative_service = CreativeGeneratorService(db)
        self.budget_service = BudgetOptimizerService(db)
        
        # Initialize adapters (default to dry-run)
        self.meta_adapter = MetaMarketingAdapter(dry_run=True)
    
    async def run_campaign_workflow(
        self,
        budget_daily: float,
        platforms: List[str] = ["meta"],
        auto_deploy: bool = False
    ) -> Dict[str, Any]:
        """
        Run complete campaign workflow from persona discovery to deployment.
        
        Args:
            budget_daily: Total daily budget to allocate
            platforms: Platforms to deploy to (meta, google, tiktok)
            auto_deploy: If True, deploy campaigns automatically
        
        Returns:
            Workflow results with campaign IDs and metrics
        """
        logger.info("marketing_workflow_started",
                   budget_daily=budget_daily,
                   platforms=platforms)
        
        results = {
            "personas_discovered": 0,
            "creatives_generated": 0,
            "campaigns_created": 0,
            "status": "success"
        }
        
        try:
            # Step 1: Discover personas
            personas = self.persona_service.discover_personas(
                min_cluster_size=25,
                method="hdbscan"
            )
            results["personas_discovered"] = len(personas)
            
            if not personas:
                logger.warning("no_personas_discovered")
                results["status"] = "no_personas"
                return results
            
            # Step 2: Generate creatives for each persona
            all_creatives = []
            for persona in personas[:3]:  # Top 3 personas
                creatives = self.creative_service.generate_creatives(
                    persona_id=persona.id,
                    format=CreativeFormat.IMAGE,
                    count=2  # 2 variants per persona
                )
                all_creatives.extend(creatives)
            
            results["creatives_generated"] = len(all_creatives)
            
            # Step 3: Deploy campaigns (if auto_deploy)
            if auto_deploy and "meta" in platforms:
                campaigns = await self._deploy_meta_campaigns(
                    personas=personas[:3],
                    creatives=all_creatives,
                    budget_daily=budget_daily
                )
                results["campaigns_created"] = len(campaigns)
                results["campaign_ids"] = [c.id for c in campaigns]
            
            logger.info("marketing_workflow_completed", results=results)
            
            return results
            
        except Exception as e:
            logger.error("marketing_workflow_failed", error=str(e))
            results["status"] = "failed"
            results["error"] = str(e)
            return results
    
    async def _deploy_meta_campaigns(
        self,
        personas: List[Persona],
        creatives: List[Creative],
        budget_daily: float
    ) -> List[Campaign]:
        """Deploy campaigns to Meta (Facebook/Instagram)"""
        
        campaigns = []
        budget_per_persona = budget_daily / len(personas)
        
        for persona in personas:
            # Get creatives for this persona
            persona_creatives = [c for c in creatives if c.persona_id == persona.id]
            
            if not persona_creatives:
                continue
            
            # Create campaign
            campaign_data = await self.meta_adapter.create_campaign(
                name=f"{persona.name} - Lead Gen",
                objective="LEAD_GENERATION",
                status="PAUSED",  # Start paused for review
                budget_daily=budget_per_persona,
                special_ad_categories=["HOUSING"]
            )
            
            # Save campaign to DB
            campaign = Campaign(
                name=campaign_data["name"],
                platform="meta",
                objective="lead_generation",
                status="draft",
                budget_daily=budget_per_persona,
                platform_campaign_id=campaign_data["id"],
                strategy={
                    "persona_id": persona.id,
                    "target_personas": [persona.id],
                    "hypothesis": f"Target {persona.name} with {len(persona_creatives)} creative variants"
                }
            )
            self.db.add(campaign)
            self.db.flush()
            
            # Create ad set for each creative
            for creative in persona_creatives:
                # Build targeting from persona
                targeting = self._build_targeting(persona)
                
                adset_data = await self.meta_adapter.create_ad_set(
                    campaign_id=campaign_data["id"],
                    name=f"{persona.name} - {creative.name}",
                    targeting=targeting,
                    budget_daily=budget_per_persona / len(persona_creatives),
                    status="PAUSED"
                )
                
                # Save ad set to DB
                ad_set = AdSet(
                    campaign_id=campaign.id,
                    name=adset_data["name"],
                    status="draft",
                    budget_daily=budget_per_persona / len(persona_creatives),
                    platform_adset_id=adset_data["id"]
                )
                self.db.add(ad_set)
                self.db.flush()
                
                # Create ad
                creative_spec = self._build_creative_spec(creative)
                
                ad_data = await self.meta_adapter.create_ad(
                    adset_id=adset_data["id"],
                    name=creative.name,
                    creative=creative_spec,
                    status="PAUSED"
                )
                
                # Save ad to DB
                ad = Ad(
                    ad_set_id=ad_set.id,
                    creative_id=creative.id,
                    name=ad_data["name"],
                    status="draft",
                    platform_ad_id=ad_data["id"],
                    tracking_params={
                        "utm_source": "facebook",
                        "utm_medium": "cpc",
                        "utm_campaign": campaign.id,
                        "utm_adset": ad_set.id,
                        "utm_ad": ad.id
                    }
                )
                self.db.add(ad)
            
            campaigns.append(campaign)
        
        self.db.commit()
        
        return campaigns
    
    def _build_targeting(self, persona: Persona) -> Dict[str, Any]:
        """Build Meta targeting spec from persona"""
        rules = persona.rules
        
        targeting = {
            "geo_locations": {
                "countries": ["AE"],  # United Arab Emirates
            },
            "age_min": 25,
            "age_max": 55,
        }
        
        # Add cities if specified
        if "locations" in rules and rules["locations"]:
            targeting["geo_locations"]["cities"] = [
                {"name": loc} for loc in rules["locations"][:5]
            ]
        
        # Add interests (real estate related)
        targeting["interests"] = [
            {"name": "Real estate"},
            {"name": "Property investment"},
            {"name": "Luxury goods"}
        ]
        
        return targeting
    
    def _build_creative_spec(self, creative: Creative) -> Dict[str, Any]:
        """Build Meta creative spec from Creative object"""
        return {
            "object_story_spec": {
                "page_id": "PAGE_ID",  # TODO: Configure
                "link_data": {
                    "message": creative.primary_text,
                    "link": "https://example.com",  # TODO: Configure landing page
                    "name": creative.headline,
                    "description": creative.description,
                    "call_to_action": {
                        "type": creative.call_to_action.upper().replace(" ", "_")
                    }
                }
            }
        }
    
    def optimize_active_campaigns(self, auto_apply: bool = False) -> Dict[str, Any]:
        """
        Optimize budget allocation across all active campaigns.
        
        Args:
            auto_apply: If True, automatically apply recommendations
        
        Returns:
            Optimization results
        """
        from sqlalchemy import select
        from ..models import CampaignStatus
        
        campaigns = self.db.execute(
            select(Campaign).where(Campaign.status == CampaignStatus.ACTIVE)
        ).scalars().all()
        
        if not campaigns:
            return {"status": "no_active_campaigns", "recommendations": 0}
        
        total_recommendations = 0
        total_applied = 0
        
        for campaign in campaigns:
            recommendations = self.budget_service.optimize_campaign_budget(
                campaign_id=campaign.id,
                lookback_days=7
            )
            
            total_recommendations += len(recommendations)
            
            if auto_apply and recommendations:
                applied = self.budget_service.apply_recommendations(
                    recommendations,
                    auto_approve=True
                )
                total_applied += applied
        
        return {
            "status": "success",
            "campaigns_optimized": len(campaigns),
            "total_recommendations": total_recommendations,
            "total_applied": total_applied
        }

