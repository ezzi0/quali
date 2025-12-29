"""
Marketing Agent Orchestrator

Coordinates the full marketing campaign lifecycle from persona discovery
through creative generation, multi-platform campaign deployment, budget 
optimization, and continuous learning.
"""
from typing import Dict, Any, List, Optional
from dataclasses import asdict
from sqlalchemy.orm import Session
from openai import OpenAI

from ..config import get_settings
from ..logging import get_logger
from ..models import (
    Persona, Creative, Campaign, AdSet, Ad, CreativeFormat,
    CampaignPlatform, CampaignStatus
)
from ..services.marketing.persona_discovery import PersonaDiscoveryService
from ..services.marketing.creative_generator import CreativeGeneratorService
from ..services.marketing.budget_optimizer import BudgetOptimizerService
from ..services.marketing.platform_selector import PlatformSelectorService
from ..services.marketing.cross_platform_optimizer import CrossPlatformOptimizer
from ..services.marketing.learning_service import LearningService
from ..services.marketing.lead_persona_matcher import LeadPersonaMatcherService
from ..services.marketing.audience_sync import AudienceSyncService
from ..services.marketing.experiment_runner import ExperimentRunnerService
from ..adapters.meta_marketing import MetaMarketingAdapter
from ..adapters.google_ads import GoogleAdsAdapter
from ..adapters.tiktok_ads import TikTokAdsAdapter

settings = get_settings()
logger = get_logger(__name__)


class MarketingAgent:
    """
    Marketing Agent orchestrates the full campaign lifecycle with learning.
    
    Process:
    1. Discover personas from qualified leads
    2. Match incoming leads to personas
    3. Generate creatives for each persona
    4. Select optimal platforms for each persona
    5. Deploy campaigns to multiple platforms
    6. Monitor and optimize budget allocation
    7. Learn from results and adapt
    8. Track attribution and close the loop
    
    This agent works in tandem with the QualificationAgent:
    - QualificationAgent: Inbound lead qualification
    - MarketingAgent: Outbound campaign generation
    """
    
    def __init__(self, db: Session, dry_run: bool = True):
        self.db = db
        self.dry_run = dry_run
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        
        # Initialize all services
        self.persona_service = PersonaDiscoveryService(db)
        self.creative_service = CreativeGeneratorService(db)
        self.budget_service = BudgetOptimizerService(db)
        self.platform_selector = PlatformSelectorService(db)
        self.cross_platform_optimizer = CrossPlatformOptimizer(db)
        self.learning_service = LearningService(db)
        self.lead_matcher = LeadPersonaMatcherService(db)
        self.audience_sync = AudienceSyncService(db)
        self.experiment_runner = ExperimentRunnerService(db)
        
        # Initialize adapters
        self.meta_adapter = MetaMarketingAdapter(dry_run=dry_run)
        self.google_adapter = GoogleAdsAdapter(dry_run=dry_run)
        self.tiktok_adapter = TikTokAdsAdapter(dry_run=dry_run)
    
    async def run_full_workflow(
        self,
        total_budget: float,
        platforms: Optional[List[str]] = None,
        auto_deploy: bool = False,
        run_learning: bool = True
    ) -> Dict[str, Any]:
        """
        Run the complete marketing workflow from persona discovery to deployment.
        
        Args:
            total_budget: Total daily budget to allocate across all platforms
            platforms: Platforms to deploy to (default: all available)
            auto_deploy: If True, deploy campaigns automatically
            run_learning: If True, run learning cycle after deployment
        
        Returns:
            Comprehensive workflow results
        """
        logger.info("marketing_full_workflow_started",
                   total_budget=total_budget,
                   platforms=platforms,
                   auto_deploy=auto_deploy)
        
        platforms = platforms or ["meta", "google", "tiktok"]
        
        results = {
            "status": "success",
            "personas_discovered": 0,
            "creatives_generated": 0,
            "platform_allocations": {},
            "campaigns_created": {},
            "learning_insights": None,
            "errors": []
        }
        
        try:
            # Step 1: Discover personas
            personas = await self._discover_personas()
            results["personas_discovered"] = len(personas)
            
            if not personas:
                logger.warning("no_personas_discovered")
                results["status"] = "no_personas"
                return results
            
            # Step 2: Sync personas to platform audiences
            for persona in personas[:3]:
                try:
                    self.audience_sync.sync_persona_to_platforms(
                        persona.id, platforms
                    )
                except Exception as e:
                    results["errors"].append(f"Audience sync failed for persona {persona.id}: {str(e)}")
            
            # Step 3: Generate creatives for each persona
            all_creatives = []
            for persona in personas[:3]:  # Top 3 personas
                creatives = self.creative_service.generate_creatives(
                    persona_id=persona.id,
                    format=CreativeFormat.IMAGE,
                    count=2
                )
                all_creatives.extend(creatives)
            
            results["creatives_generated"] = len(all_creatives)
            
            # Step 4: Select optimal platforms for each persona
            platform_recommendations = {}
            for persona in personas[:3]:
                try:
                    recommendation = self.platform_selector.select_platforms_for_persona(
                        persona_id=persona.id,
                        total_budget=total_budget / len(personas[:3]),
                        objective="lead_generation"
                    )
                    platform_recommendations[persona.id] = recommendation
                except Exception as e:
                    results["errors"].append(f"Platform selection failed for persona {persona.id}: {str(e)}")
            
            # Build platform allocation summary
            for persona_id, rec in platform_recommendations.items():
                results["platform_allocations"][persona_id] = {
                    "persona_name": rec.persona_name,
                    "primary_platform": rec.primary_platform,
                    "platforms": [
                        {
                            "platform": p.platform,
                            "score": p.score,
                            "budget_pct": p.recommended_budget_pct,
                            "rationale": p.rationale
                        }
                        for p in rec.platforms
                    ]
                }
            
            # Step 5: Deploy campaigns (if auto_deploy)
            if auto_deploy:
                campaigns_created = await self._deploy_multi_platform_campaigns(
                    personas=personas[:3],
                    creatives=all_creatives,
                    platform_recommendations=platform_recommendations,
                    total_budget=total_budget
                )
                results["campaigns_created"] = campaigns_created
            
            # Step 6: Run learning cycle
            if run_learning:
                try:
                    learning_result = self.learning_service.run_learning_cycle(
                        lookback_days=7,
                        auto_apply=auto_deploy
                    )
                    results["learning_insights"] = {
                        "cycle_id": learning_result.cycle_id,
                        "personas_analyzed": learning_result.personas_analyzed,
                        "creatives_analyzed": learning_result.creatives_analyzed,
                        "actions_taken": len(learning_result.actions_taken),
                        "improvements": learning_result.improvements
                    }
                except Exception as e:
                    results["errors"].append(f"Learning cycle failed: {str(e)}")
            
            logger.info("marketing_full_workflow_completed", results=results)
            
        except Exception as e:
            logger.error("marketing_full_workflow_failed", error=str(e))
            results["status"] = "failed"
            results["errors"].append(str(e))
        
        return results
    
    async def _discover_personas(self) -> List[Persona]:
        """Discover personas from lead data."""
        return self.persona_service.discover_personas(
            min_cluster_size=25,
            method="hdbscan"
        )
    
    async def _deploy_multi_platform_campaigns(
        self,
        personas: List[Persona],
        creatives: List[Creative],
        platform_recommendations: Dict,
        total_budget: float
    ) -> Dict[str, List[int]]:
        """Deploy campaigns to multiple platforms based on recommendations."""
        campaigns_created = {"meta": [], "google": [], "tiktok": []}
        
        for persona in personas:
            recommendation = platform_recommendations.get(persona.id)
            if not recommendation:
                continue
            
            # Get creatives for this persona
            persona_creatives = [c for c in creatives if c.persona_id == persona.id]
            if not persona_creatives:
                continue
            
            # Deploy to each recommended platform
            for platform_score in recommendation.platforms:
                platform = platform_score.platform
                budget = total_budget * platform_score.recommended_budget_pct / len(personas)
                
                try:
                    if platform == "meta":
                        campaign = await self._deploy_meta_campaign(
                            persona, persona_creatives, budget
                        )
                    elif platform == "google":
                        campaign = await self._deploy_google_campaign(
                            persona, persona_creatives, budget
                        )
                    elif platform == "tiktok":
                        campaign = await self._deploy_tiktok_campaign(
                            persona, persona_creatives, budget
                        )
                    else:
                        continue
                    
                    if campaign:
                        campaigns_created[platform].append(campaign.id)
                        
                except Exception as e:
                    logger.error("campaign_deployment_failed",
                               persona_id=persona.id,
                               platform=platform,
                               error=str(e))
        
        return campaigns_created
    
    async def _deploy_meta_campaign(
        self,
        persona: Persona,
        creatives: List[Creative],
        budget_daily: float
    ) -> Optional[Campaign]:
        """Deploy campaign to Meta (Facebook/Instagram)."""
        
        # Create campaign
        campaign_data = await self.meta_adapter.create_campaign(
            name=f"{persona.name} - Lead Gen",
            objective="LEAD_GENERATION",
            status="PAUSED",
            budget_daily=budget_daily,
            special_ad_categories=["HOUSING"]
        )
        
        # Save campaign to DB
        campaign = Campaign(
            name=campaign_data["name"],
            platform=CampaignPlatform.META,
            objective="lead_generation",
            status=CampaignStatus.DRAFT,
            budget_daily=budget_daily,
            platform_campaign_id=campaign_data["id"],
            strategy={
                "persona_id": persona.id,
                "target_personas": [persona.id],
                "hypothesis": f"Target {persona.name} on Meta"
            }
        )
        self.db.add(campaign)
        self.db.flush()
        
        # Create ad sets and ads
        await self._create_meta_ads(campaign, persona, creatives, budget_daily)
        
        self.db.commit()
        
        logger.info("meta_campaign_deployed",
                   campaign_id=campaign.id,
                   persona=persona.name)
        
        return campaign
    
    async def _create_meta_ads(
        self,
        campaign: Campaign,
        persona: Persona,
        creatives: List[Creative],
        budget_daily: float
    ):
        """Create ad sets and ads for Meta campaign."""
        budget_per_creative = budget_daily / max(len(creatives), 1)
        
        for creative in creatives:
            targeting = self._build_meta_targeting(persona)
            
            adset_data = await self.meta_adapter.create_ad_set(
                campaign_id=campaign.platform_campaign_id,
                name=f"{persona.name} - {creative.name}",
                targeting=targeting,
                budget_daily=budget_per_creative,
                status="PAUSED"
            )
            
            ad_set = AdSet(
                campaign_id=campaign.id,
                name=adset_data["name"],
                status=CampaignStatus.DRAFT,
                budget_daily=budget_per_creative,
                platform_adset_id=adset_data["id"]
            )
            self.db.add(ad_set)
            self.db.flush()
            
            creative_spec = self._build_meta_creative_spec(creative)
            
            ad_data = await self.meta_adapter.create_ad(
                adset_id=adset_data["id"],
                name=creative.name,
                creative=creative_spec,
                status="PAUSED"
            )
            
            ad = Ad(
                ad_set_id=ad_set.id,
                creative_id=creative.id,
                name=ad_data["name"],
                status=CampaignStatus.DRAFT,
                platform_ad_id=ad_data["id"],
                tracking_params={
                    "utm_source": "facebook",
                    "utm_medium": "cpc",
                    "utm_campaign": str(campaign.id),
                    "utm_adset": str(ad_set.id)
                }
            )
            self.db.add(ad)
    
    async def _deploy_google_campaign(
        self,
        persona: Persona,
        creatives: List[Creative],
        budget_daily: float
    ) -> Optional[Campaign]:
        """Deploy campaign to Google Ads."""
        
        # Create campaign
        campaign_data = await self.google_adapter.create_campaign(
            name=f"{persona.name} - Search",
            budget_daily=budget_daily,
            objective="LEAD_GENERATION",
            status="PAUSED"
        )
        
        # Save campaign to DB
        campaign = Campaign(
            name=campaign_data["name"],
            platform=CampaignPlatform.GOOGLE,
            objective="lead_generation",
            status=CampaignStatus.DRAFT,
            budget_daily=budget_daily,
            platform_campaign_id=campaign_data["id"],
            strategy={
                "persona_id": persona.id,
                "target_personas": [persona.id],
                "hypothesis": f"Target {persona.name} on Google Search"
            }
        )
        self.db.add(campaign)
        self.db.flush()
        
        # Create ad groups and ads
        await self._create_google_ads(campaign, persona, creatives, budget_daily)
        
        self.db.commit()
        
        logger.info("google_campaign_deployed",
                   campaign_id=campaign.id,
                   persona=persona.name)
        
        return campaign
    
    async def _create_google_ads(
        self,
        campaign: Campaign,
        persona: Persona,
        creatives: List[Creative],
        budget_daily: float
    ):
        """Create ad groups and responsive search ads for Google."""
        targeting = self._build_google_targeting(persona)
        
        adgroup_data = await self.google_adapter.create_ad_group(
            campaign_id=campaign.platform_campaign_id,
            name=f"{persona.name} - Main",
            targeting=targeting
        )
        
        ad_set = AdSet(
            campaign_id=campaign.id,
            name=adgroup_data["name"],
            status=CampaignStatus.DRAFT,
            budget_daily=budget_daily,
            platform_adset_id=adgroup_data["id"]
        )
        self.db.add(ad_set)
        self.db.flush()
        
        # Create responsive search ad from best creative
        if creatives:
            creative = creatives[0]
            
            # Build headlines and descriptions from creative
            headlines = [
                creative.headline or f"Find Your Dream Property",
                f"{persona.name} - Special Offer",
                "Exclusive Properties Available"
            ]
            descriptions = [
                creative.primary_text or "Discover luxury properties tailored to your needs.",
                creative.description or "Contact us today for a personalized consultation."
            ]
            
            ad_data = await self.google_adapter.create_ad(
                ad_group_id=adgroup_data["id"],
                headlines=headlines,
                descriptions=descriptions,
                final_urls=["https://example.com"]  # TODO: Configure
            )
            
            ad = Ad(
                ad_set_id=ad_set.id,
                creative_id=creative.id,
                name=f"{persona.name} - RSA",
                status=CampaignStatus.DRAFT,
                platform_ad_id=ad_data["id"],
                tracking_params={
                    "utm_source": "google",
                    "utm_medium": "cpc",
                    "utm_campaign": str(campaign.id)
                }
            )
            self.db.add(ad)
    
    async def _deploy_tiktok_campaign(
        self,
        persona: Persona,
        creatives: List[Creative],
        budget_daily: float
    ) -> Optional[Campaign]:
        """Deploy campaign to TikTok."""
        
        # Create campaign
        campaign_data = await self.tiktok_adapter.create_campaign(
            name=f"{persona.name} - TikTok",
            budget_daily=budget_daily,
            objective="LEAD_GENERATION"
        )
        
        # Save campaign to DB
        campaign = Campaign(
            name=campaign_data["name"],
            platform=CampaignPlatform.TIKTOK,
            objective="lead_generation",
            status=CampaignStatus.DRAFT,
            budget_daily=budget_daily,
            platform_campaign_id=campaign_data["id"],
            strategy={
                "persona_id": persona.id,
                "target_personas": [persona.id],
                "hypothesis": f"Target {persona.name} on TikTok"
            }
        )
        self.db.add(campaign)
        self.db.flush()
        
        # Create ad groups and ads
        await self._create_tiktok_ads(campaign, persona, creatives, budget_daily)
        
        self.db.commit()
        
        logger.info("tiktok_campaign_deployed",
                   campaign_id=campaign.id,
                   persona=persona.name)
        
        return campaign
    
    async def _create_tiktok_ads(
        self,
        campaign: Campaign,
        persona: Persona,
        creatives: List[Creative],
        budget_daily: float
    ):
        """Create ad groups and ads for TikTok."""
        targeting = self._build_tiktok_targeting(persona)
        
        adgroup_data = await self.tiktok_adapter.create_ad_group(
            campaign_id=campaign.platform_campaign_id,
            name=f"{persona.name} - Main",
            budget_daily=budget_daily,
            targeting=targeting
        )
        
        ad_set = AdSet(
            campaign_id=campaign.id,
            name=adgroup_data["name"],
            status=CampaignStatus.DRAFT,
            budget_daily=budget_daily,
            platform_adset_id=adgroup_data["id"]
        )
        self.db.add(ad_set)
        self.db.flush()
        
        # Create ads
        for creative in creatives[:2]:  # Max 2 per ad group
            ad_data = await self.tiktok_adapter.create_ad(
                ad_group_id=adgroup_data["id"],
                name=creative.name,
                creative={
                    "format": "SINGLE_IMAGE",
                    "primary_text": creative.primary_text or "",
                    "display_name": "Property Expert"
                },
                landing_page_url="https://example.com",  # TODO: Configure
                call_to_action="LEARN_MORE"
            )
            
            ad = Ad(
                ad_set_id=ad_set.id,
                creative_id=creative.id,
                name=ad_data["name"],
                status=CampaignStatus.DRAFT,
                platform_ad_id=ad_data["id"],
                tracking_params={
                    "utm_source": "tiktok",
                    "utm_medium": "cpc",
                    "utm_campaign": str(campaign.id)
                }
            )
            self.db.add(ad)
    
    def _build_meta_targeting(self, persona: Persona) -> Dict[str, Any]:
        """Build Meta targeting spec from persona."""
        rules = persona.rules or {}
        
        targeting = {
            "geo_locations": {
                "countries": ["AE"],
            },
            "age_min": 25,
            "age_max": 55,
        }
        
        if "locations" in rules and rules["locations"]:
            targeting["geo_locations"]["cities"] = [
                {"name": loc} for loc in rules["locations"][:5]
            ]
        
        targeting["interests"] = [
            {"name": "Real estate"},
            {"name": "Property investment"},
        ]
        
        return targeting
    
    def _build_google_targeting(self, persona: Persona) -> Dict[str, Any]:
        """Build Google targeting spec from persona."""
        rules = persona.rules or {}
        
        targeting = {
            "geo_targets": {"countries": ["AE"]},
            "keywords": []
        }
        
        # Build keywords from persona
        property_types = rules.get("property_types", ["property"])
        locations = rules.get("locations", ["dubai"])
        
        for pt in property_types[:3]:
            for loc in locations[:3]:
                targeting["keywords"].append(f"{pt} for sale {loc}")
                targeting["keywords"].append(f"buy {pt} {loc}")
        
        return targeting
    
    def _build_tiktok_targeting(self, persona: Persona) -> Dict[str, Any]:
        """Build TikTok targeting spec from persona."""
        rules = persona.rules or {}
        
        targeting = {
            "geo_locations": {"countries": ["AE"]},
            "age_min": 25,
            "age_max": 45,
            "interests": ["Real estate", "Home & garden"]
        }
        
        if "locations" in rules:
            targeting["geo_locations"]["cities"] = rules["locations"][:5]
        
        return targeting
    
    def _build_meta_creative_spec(self, creative: Creative) -> Dict[str, Any]:
        """Build Meta creative spec from Creative object."""
        return {
            "object_story_spec": {
                "page_id": settings.meta_app_id or "PAGE_ID",
                "link_data": {
                    "message": creative.primary_text,
                    "link": "https://example.com",
                    "name": creative.headline,
                    "description": creative.description,
                    "call_to_action": {
                        "type": (creative.call_to_action or "LEARN_MORE").upper().replace(" ", "_")
                    }
                }
            }
        }
    
    async def optimize_active_campaigns(
        self,
        auto_apply: bool = False
    ) -> Dict[str, Any]:
        """
        Optimize budget allocation across all active campaigns.
        
        Args:
            auto_apply: If True, automatically apply recommendations
        
        Returns:
            Optimization results
        """
        from sqlalchemy import select
        
        campaigns = self.db.execute(
            select(Campaign).where(Campaign.status == CampaignStatus.ACTIVE)
        ).scalars().all()
        
        if not campaigns:
            return {"status": "no_active_campaigns", "recommendations": 0}
        
        results = {
            "campaigns_analyzed": len(campaigns),
            "recommendations": [],
            "cross_platform_optimizations": []
        }
        
        # Group campaigns by persona
        persona_campaigns = {}
        for campaign in campaigns:
            persona_id = campaign.strategy.get("persona_id")
            if persona_id:
                if persona_id not in persona_campaigns:
                    persona_campaigns[persona_id] = []
                persona_campaigns[persona_id].append(campaign)
        
        # Run cross-platform optimization for each persona
        for persona_id, camps in persona_campaigns.items():
            total_budget = sum(float(c.budget_daily or 0) for c in camps)
            
            if total_budget > 0:
                try:
                    recommendation = self.cross_platform_optimizer.optimize_cross_platform_budget(
                        persona_id=persona_id,
                        total_budget=total_budget
                    )
                    
                    results["cross_platform_optimizations"].append({
                        "persona_id": persona_id,
                        "total_budget": total_budget,
                        "allocations": [
                            {
                                "platform": a.platform,
                                "current": a.current_budget,
                                "recommended": a.recommended_budget,
                                "change_pct": a.change_pct
                            }
                            for a in recommendation.platform_allocations
                        ],
                        "strategy": recommendation.overall_strategy
                    })
                    
                    if auto_apply:
                        await self.cross_platform_optimizer.apply_cross_platform_recommendations(
                            recommendation, auto_approve=True
                        )
                        
                except Exception as e:
                    logger.error("cross_platform_optimization_failed",
                               persona_id=persona_id,
                               error=str(e))
        
        # Run within-campaign optimization
        for campaign in campaigns:
            try:
                recommendations = self.budget_service.optimize_campaign_budget(
                    campaign_id=campaign.id,
                    lookback_days=7
                )
                
                results["recommendations"].extend([
                    {
                        "campaign_id": campaign.id,
                        "ad_set_id": r.ad_set_id,
                        "current": r.current_budget,
                        "recommended": r.recommended_budget,
                        "rationale": r.rationale
                    }
                    for r in recommendations
                ])
                
                if auto_apply and recommendations:
                    await self.budget_service.apply_recommendations(
                        recommendations, auto_approve=True
                    )
                    
            except Exception as e:
                logger.error("campaign_optimization_failed",
                           campaign_id=campaign.id,
                           error=str(e))
        
        return results
    
    async def run_learning_and_adaptation(
        self,
        lookback_days: int = 7,
        auto_apply: bool = False
    ) -> Dict[str, Any]:
        """
        Run the learning and adaptation cycle.
        
        Args:
            lookback_days: Days of data to analyze
            auto_apply: If True, automatically apply learnings
        
        Returns:
            Learning cycle results
        """
        logger.info("learning_adaptation_started", lookback_days=lookback_days)
        
        results = {
            "status": "success",
            "learning_cycle": None,
            "experiments_checked": 0,
            "experiments_stopped": 0,
            "personas_matched": 0
        }
        
        try:
            # Run main learning cycle
            learning_result = self.learning_service.run_learning_cycle(
                lookback_days=lookback_days,
                auto_apply=auto_apply
            )
            
            results["learning_cycle"] = {
                "cycle_id": learning_result.cycle_id,
                "personas_analyzed": learning_result.personas_analyzed,
                "creatives_analyzed": learning_result.creatives_analyzed,
                "actions_taken": len(learning_result.actions_taken),
                "insights": [
                    {
                        "persona_name": i.persona_name,
                        "conversion_rate": i.conversion_rate,
                        "best_platform": i.best_platform,
                        "recommendations": i.recommended_adjustments[:3]
                    }
                    for i in learning_result.insights
                ]
            }
            
            # Check experiment stopping rules
            experiments_to_stop = self.experiment_runner.run_experiment_checks()
            results["experiments_checked"] = len(experiments_to_stop)
            
            if auto_apply:
                for exp in experiments_to_stop:
                    self.experiment_runner.stop_experiment(
                        exp["experiment_id"],
                        reason="; ".join(exp["reasons"])
                    )
                    results["experiments_stopped"] += 1
            
            # Match unassigned leads to personas
            lead_matches = self.lead_matcher.batch_match_leads(
                auto_assign=auto_apply
            )
            results["personas_matched"] = sum(
                1 for matches in lead_matches.values()
                if matches and matches[0].is_strong_match
            )
            
            logger.info("learning_adaptation_completed", results=results)
            
        except Exception as e:
            logger.error("learning_adaptation_failed", error=str(e))
            results["status"] = "failed"
            results["error"] = str(e)
        
        return results
    
    def get_marketing_dashboard(self) -> Dict[str, Any]:
        """
        Get comprehensive marketing dashboard data.
        
        Returns:
            Dashboard metrics and summaries
        """
        from sqlalchemy import select, func
        
        # Get counts
        active_personas = self.db.execute(
            select(func.count(Persona.id)).where(Persona.status == "active")
        ).scalar() or 0
        
        active_campaigns = self.db.execute(
            select(func.count(Campaign.id)).where(
                Campaign.status == CampaignStatus.ACTIVE
            )
        ).scalar() or 0
        
        active_creatives = self.db.execute(
            select(func.count(Creative.id)).where(
                Creative.status == "active"
            )
        ).scalar() or 0
        
        # Get platform performance summary
        platform_summary = self.platform_selector.get_platform_performance_summary(
            lookback_days=30
        )
        
        # Get learning summary
        learning_summary = self.learning_service.get_learning_summary(days=30)
        
        # Get lead distribution
        lead_distribution = self.lead_matcher.get_persona_lead_distribution()
        
        return {
            "summary": {
                "active_personas": active_personas,
                "active_campaigns": active_campaigns,
                "active_creatives": active_creatives
            },
            "platform_performance": platform_summary,
            "learning_summary": learning_summary,
            "lead_distribution": lead_distribution
        }
