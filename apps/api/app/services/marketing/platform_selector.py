"""
Platform Selector Service

Determines the optimal advertising platform(s) for each persona based on
historical performance, persona characteristics, and platform-specific strengths.
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ...config import get_settings
from ...logging import get_logger
from ...models import (
    Persona, Campaign, AdSet, MarketingMetric,
    CampaignPlatform, CampaignStatus
)

settings = get_settings()
logger = get_logger(__name__)


@dataclass
class PlatformScore:
    """Platform scoring result for a persona."""
    platform: str
    score: float  # 0-100
    confidence: float  # 0-1
    recommended_budget_pct: float  # 0-1, percentage of total budget
    rationale: str
    metrics: Dict[str, float]


@dataclass
class PlatformRecommendation:
    """Platform recommendation for a persona."""
    persona_id: int
    persona_name: str
    platforms: List[PlatformScore]
    total_recommended_platforms: int
    primary_platform: str
    strategy: str


class PlatformSelectorService:
    """
    Selects optimal advertising platforms for personas.
    
    Uses multiple signals:
    1. Historical performance per platform (CVR, CPA, ROAS)
    2. Persona characteristics (demographics, behavior)
    3. Platform strengths (visual content, B2B, young demographics)
    4. Available budget and minimum thresholds
    
    Implements a weighted scoring model with Thompson Sampling
    for exploration/exploitation balance.
    """
    
    # Platform characteristics and strengths
    PLATFORM_PROFILES = {
        "meta": {
            "display_name": "Meta (Facebook/Instagram)",
            "strengths": ["visual_content", "retargeting", "lookalike", "broad_reach"],
            "demographics": {"age_min": 25, "age_max": 55, "skews": ["female"]},
            "min_daily_budget": 10.0,
            "best_for": ["luxury", "lifestyle", "investment", "first_time_buyer"],
            "objective_fit": {
                "lead_generation": 0.9,
                "brand_awareness": 0.85,
                "conversions": 0.8,
                "traffic": 0.75
            }
        },
        "google": {
            "display_name": "Google Ads",
            "strengths": ["intent_based", "search", "high_intent", "broad_reach"],
            "demographics": {"age_min": 25, "age_max": 65, "skews": []},
            "min_daily_budget": 20.0,
            "best_for": ["investor", "luxury", "commercial", "high_budget"],
            "objective_fit": {
                "lead_generation": 0.85,
                "conversions": 0.95,
                "traffic": 0.9,
                "brand_awareness": 0.6
            }
        },
        "tiktok": {
            "display_name": "TikTok Ads",
            "strengths": ["video_content", "viral", "young_audience", "engagement"],
            "demographics": {"age_min": 18, "age_max": 40, "skews": ["young"]},
            "min_daily_budget": 20.0,
            "best_for": ["first_time_buyer", "renter", "young_professional"],
            "objective_fit": {
                "brand_awareness": 0.9,
                "traffic": 0.8,
                "lead_generation": 0.7,
                "conversions": 0.65
            }
        }
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def select_platforms_for_persona(
        self,
        persona_id: int,
        total_budget: float,
        objective: str = "lead_generation",
        lookback_days: int = 30,
        max_platforms: int = 3
    ) -> PlatformRecommendation:
        """
        Select and rank platforms for a persona.
        
        Args:
            persona_id: Target persona
            total_budget: Total daily budget available
            objective: Campaign objective
            lookback_days: Days of historical data to use
            max_platforms: Maximum platforms to recommend
        
        Returns:
            PlatformRecommendation with ranked platforms and budget allocation
        """
        logger.info("platform_selection_started", persona_id=persona_id)
        
        # Fetch persona
        persona = self.db.get(Persona, persona_id)
        if not persona:
            raise ValueError(f"Persona {persona_id} not found")
        
        # Calculate scores for each platform
        platform_scores = []
        for platform_key in self.PLATFORM_PROFILES.keys():
            score = self._calculate_platform_score(
                persona=persona,
                platform=platform_key,
                objective=objective,
                lookback_days=lookback_days,
                total_budget=total_budget
            )
            platform_scores.append(score)
        
        # Sort by score
        platform_scores.sort(key=lambda x: x.score, reverse=True)
        
        # Filter platforms that meet minimum budget
        viable_platforms = [
            p for p in platform_scores
            if total_budget * p.recommended_budget_pct >= self.PLATFORM_PROFILES[p.platform]["min_daily_budget"]
        ]
        
        # Limit to max_platforms
        selected_platforms = viable_platforms[:max_platforms]
        
        # Rebalance budget allocation
        if selected_platforms:
            selected_platforms = self._rebalance_budget(selected_platforms, total_budget)
        
        # Determine strategy
        strategy = self._determine_strategy(selected_platforms, persona)
        
        recommendation = PlatformRecommendation(
            persona_id=persona_id,
            persona_name=persona.name,
            platforms=selected_platforms,
            total_recommended_platforms=len(selected_platforms),
            primary_platform=selected_platforms[0].platform if selected_platforms else "meta",
            strategy=strategy
        )
        
        logger.info("platform_selection_completed",
                   persona_id=persona_id,
                   platforms=[p.platform for p in selected_platforms])
        
        return recommendation
    
    def _calculate_platform_score(
        self,
        persona: Persona,
        platform: str,
        objective: str,
        lookback_days: int,
        total_budget: float
    ) -> PlatformScore:
        """Calculate platform score for a persona."""
        profile = self.PLATFORM_PROFILES[platform]
        
        # Component scores (0-1 scale)
        scores = {}
        
        # 1. Historical performance (40% weight)
        perf_score, perf_metrics, perf_confidence = self._get_historical_performance(
            persona.id, platform, lookback_days
        )
        scores["historical"] = perf_score
        
        # 2. Persona fit (25% weight)
        persona_fit = self._calculate_persona_fit(persona, profile)
        scores["persona_fit"] = persona_fit
        
        # 3. Objective alignment (20% weight)
        objective_score = profile["objective_fit"].get(objective.lower(), 0.7)
        scores["objective"] = objective_score
        
        # 4. Budget efficiency (15% weight)
        budget_score = self._calculate_budget_efficiency(
            platform, total_budget, profile["min_daily_budget"]
        )
        scores["budget"] = budget_score
        
        # Weighted average
        weights = {
            "historical": 0.40,
            "persona_fit": 0.25,
            "objective": 0.20,
            "budget": 0.15
        }
        
        # Adjust weights if low confidence on historical data
        if perf_confidence < 0.3:
            weights["historical"] = 0.20
            weights["persona_fit"] = 0.35
            weights["objective"] = 0.30
            weights["budget"] = 0.15
        
        final_score = sum(scores[k] * weights[k] for k in scores) * 100
        
        # Calculate recommended budget percentage using Thompson Sampling
        budget_pct = self._calculate_budget_allocation(
            score=final_score / 100,
            confidence=perf_confidence,
            min_budget=profile["min_daily_budget"],
            total_budget=total_budget
        )
        
        # Generate rationale
        rationale = self._generate_rationale(
            platform, profile, scores, perf_metrics, persona
        )
        
        return PlatformScore(
            platform=platform,
            score=final_score,
            confidence=perf_confidence,
            recommended_budget_pct=budget_pct,
            rationale=rationale,
            metrics=perf_metrics
        )
    
    def _get_historical_performance(
        self,
        persona_id: int,
        platform: str,
        lookback_days: int
    ) -> Tuple[float, Dict[str, float], float]:
        """Get historical performance for persona on platform."""
        cutoff_date = datetime.utcnow().date() - timedelta(days=lookback_days)
        
        # Find campaigns for this persona on this platform
        campaigns = self.db.execute(
            select(Campaign).where(
                Campaign.platform == CampaignPlatform(platform),
                Campaign.strategy["persona_id"].astext.cast(int) == persona_id
            )
        ).scalars().all()
        
        if not campaigns:
            # No historical data - return neutral score with low confidence
            return 0.5, {}, 0.1
        
        campaign_ids = [c.id for c in campaigns]
        
        # Aggregate metrics
        metrics = self.db.execute(
            select(
                func.sum(MarketingMetric.impressions).label('impressions'),
                func.sum(MarketingMetric.clicks).label('clicks'),
                func.sum(MarketingMetric.spend).label('spend'),
                func.sum(MarketingMetric.leads).label('leads'),
                func.sum(MarketingMetric.qualified_leads).label('qualified_leads'),
                func.sum(MarketingMetric.closed_won).label('conversions')
            ).where(
                MarketingMetric.campaign_id.in_(campaign_ids),
                MarketingMetric.date >= cutoff_date
            )
        ).first()
        
        if not metrics or not metrics.impressions:
            return 0.5, {}, 0.1
        
        # Calculate performance metrics
        impressions = metrics.impressions or 0
        clicks = metrics.clicks or 0
        spend = float(metrics.spend or 0)
        leads = metrics.leads or 0
        qualified_leads = metrics.qualified_leads or 0
        conversions = metrics.conversions or 0
        
        perf_metrics = {
            "impressions": impressions,
            "clicks": clicks,
            "spend": spend,
            "leads": leads,
            "ctr": clicks / impressions if impressions > 0 else 0,
            "cpl": spend / leads if leads > 0 else 0,
            "cvr": conversions / leads if leads > 0 else 0,
            "qualification_rate": qualified_leads / leads if leads > 0 else 0
        }
        
        # Calculate performance score (0-1)
        # Good CTR: >2%, Good CVR: >5%, Good CPL: depends on industry
        ctr_score = min(1.0, perf_metrics["ctr"] / 0.03)  # 3% CTR = perfect
        cvr_score = min(1.0, perf_metrics["cvr"] / 0.08)  # 8% CVR = perfect
        cpl_score = max(0.0, 1.0 - (perf_metrics["cpl"] / 500))  # $500 CPL = 0
        
        perf_score = (ctr_score * 0.2 + cvr_score * 0.5 + cpl_score * 0.3)
        
        # Confidence based on sample size
        confidence = min(1.0, leads / 100)  # 100 leads = full confidence
        
        return perf_score, perf_metrics, confidence
    
    def _calculate_persona_fit(self, persona: Persona, profile: Dict) -> float:
        """Calculate how well persona matches platform profile."""
        fit_scores = []
        
        # Check if persona type matches platform strengths
        characteristics = persona.characteristics or {}
        rules = persona.rules or {}
        
        # Budget fit (luxury buyers -> Meta/Google, value seekers -> TikTok)
        budget_range = rules.get("budget_range", [0, 1000000])
        avg_budget = sum(budget_range) / 2 if budget_range else 500000
        
        if avg_budget > 1500000:  # Luxury
            if "luxury" in profile.get("best_for", []):
                fit_scores.append(1.0)
            else:
                fit_scores.append(0.5)
        elif avg_budget < 500000:  # First-time/value
            if "first_time_buyer" in profile.get("best_for", []):
                fit_scores.append(1.0)
            else:
                fit_scores.append(0.6)
        else:
            fit_scores.append(0.75)
        
        # Urgency fit
        urgency = characteristics.get("urgency", "medium")
        if urgency == "high":
            # High intent -> Google Search
            if "intent_based" in profile.get("strengths", []):
                fit_scores.append(1.0)
            elif "visual_content" in profile.get("strengths", []):
                fit_scores.append(0.7)
            else:
                fit_scores.append(0.6)
        else:
            fit_scores.append(0.75)
        
        # Decision speed
        decision_speed = characteristics.get("decision_speed", "moderate")
        if decision_speed == "fast":
            if "intent_based" in profile.get("strengths", []):
                fit_scores.append(0.9)
            else:
                fit_scores.append(0.7)
        else:
            fit_scores.append(0.75)
        
        return sum(fit_scores) / len(fit_scores) if fit_scores else 0.5
    
    def _calculate_budget_efficiency(
        self,
        platform: str,
        total_budget: float,
        min_budget: float
    ) -> float:
        """Calculate budget efficiency score."""
        if total_budget < min_budget:
            return 0.0
        
        # Score based on how much above minimum we are
        headroom = (total_budget - min_budget) / min_budget
        return min(1.0, 0.5 + (headroom * 0.1))
    
    def _calculate_budget_allocation(
        self,
        score: float,
        confidence: float,
        min_budget: float,
        total_budget: float
    ) -> float:
        """Calculate recommended budget percentage using Thompson Sampling."""
        # Sample from Beta distribution based on score and confidence
        alpha = score * confidence * 10 + 1
        beta = (1 - score) * confidence * 10 + 1
        
        sampled_score = np.random.beta(alpha, beta)
        
        # Ensure minimum viable budget
        min_pct = min_budget / total_budget if total_budget > 0 else 0
        
        # Scale sampled score to budget percentage
        budget_pct = max(min_pct, sampled_score * 0.6)  # Max 60% per platform
        
        return budget_pct
    
    def _rebalance_budget(
        self,
        platforms: List[PlatformScore],
        total_budget: float
    ) -> List[PlatformScore]:
        """Rebalance budget allocations to sum to 100%."""
        total_pct = sum(p.recommended_budget_pct for p in platforms)
        
        if total_pct == 0:
            # Equal distribution
            equal_pct = 1.0 / len(platforms)
            for p in platforms:
                p.recommended_budget_pct = equal_pct
        else:
            # Normalize
            for p in platforms:
                p.recommended_budget_pct = p.recommended_budget_pct / total_pct
        
        return platforms
    
    def _determine_strategy(
        self,
        platforms: List[PlatformScore],
        persona: Persona
    ) -> str:
        """Determine campaign strategy based on platform selection."""
        if len(platforms) == 1:
            return f"Single-platform focus on {platforms[0].platform.title()}"
        
        if len(platforms) >= 2:
            primary = platforms[0]
            secondary = platforms[1]
            
            if primary.score - secondary.score < 10:
                return f"Balanced multi-platform: {primary.platform.title()} + {secondary.platform.title()}"
            else:
                return f"Primary on {primary.platform.title()}, testing {secondary.platform.title()}"
        
        return "Exploratory multi-platform strategy"
    
    def _generate_rationale(
        self,
        platform: str,
        profile: Dict,
        scores: Dict[str, float],
        metrics: Dict[str, float],
        persona: Persona
    ) -> str:
        """Generate human-readable rationale for platform selection."""
        parts = []
        
        # Historical performance
        if metrics:
            if metrics.get("cvr", 0) > 0.05:
                parts.append(f"Strong historical CVR ({metrics['cvr']:.1%})")
            elif metrics.get("cvr", 0) > 0:
                parts.append(f"Historical CVR: {metrics['cvr']:.1%}")
        else:
            parts.append("No historical data, using predictive scoring")
        
        # Persona fit
        if scores.get("persona_fit", 0) > 0.8:
            parts.append(f"Excellent fit for {persona.name}")
        elif scores.get("persona_fit", 0) > 0.6:
            parts.append(f"Good fit for {persona.name}")
        
        # Platform strengths
        strengths = profile.get("strengths", [])[:2]
        if strengths:
            parts.append(f"Strengths: {', '.join(s.replace('_', ' ') for s in strengths)}")
        
        return ". ".join(parts) if parts else "Standard recommendation"
    
    def get_platform_performance_summary(
        self,
        lookback_days: int = 30
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get aggregated performance summary for all platforms.
        
        Returns:
            Dict with platform -> performance metrics
        """
        cutoff_date = datetime.utcnow().date() - timedelta(days=lookback_days)
        
        summary = {}
        
        for platform_key in self.PLATFORM_PROFILES.keys():
            # Get campaigns for this platform
            campaigns = self.db.execute(
                select(Campaign).where(
                    Campaign.platform == CampaignPlatform(platform_key),
                    Campaign.status.in_([CampaignStatus.ACTIVE, CampaignStatus.COMPLETED])
                )
            ).scalars().all()
            
            if not campaigns:
                summary[platform_key] = {
                    "display_name": self.PLATFORM_PROFILES[platform_key]["display_name"],
                    "campaigns": 0,
                    "has_data": False
                }
                continue
            
            campaign_ids = [c.id for c in campaigns]
            
            # Aggregate metrics
            metrics = self.db.execute(
                select(
                    func.sum(MarketingMetric.impressions).label('impressions'),
                    func.sum(MarketingMetric.clicks).label('clicks'),
                    func.sum(MarketingMetric.spend).label('spend'),
                    func.sum(MarketingMetric.leads).label('leads'),
                    func.sum(MarketingMetric.closed_won).label('conversions')
                ).where(
                    MarketingMetric.campaign_id.in_(campaign_ids),
                    MarketingMetric.date >= cutoff_date
                )
            ).first()
            
            if metrics and metrics.impressions:
                spend = float(metrics.spend or 0)
                leads = metrics.leads or 0
                conversions = metrics.conversions or 0
                
                summary[platform_key] = {
                    "display_name": self.PLATFORM_PROFILES[platform_key]["display_name"],
                    "campaigns": len(campaigns),
                    "has_data": True,
                    "impressions": metrics.impressions,
                    "clicks": metrics.clicks,
                    "spend": spend,
                    "leads": leads,
                    "conversions": conversions,
                    "ctr": metrics.clicks / metrics.impressions if metrics.impressions else 0,
                    "cpl": spend / leads if leads > 0 else 0,
                    "cvr": conversions / leads if leads > 0 else 0,
                    "cpa": spend / conversions if conversions > 0 else 0,
                }
            else:
                summary[platform_key] = {
                    "display_name": self.PLATFORM_PROFILES[platform_key]["display_name"],
                    "campaigns": len(campaigns),
                    "has_data": False
                }
        
        return summary

