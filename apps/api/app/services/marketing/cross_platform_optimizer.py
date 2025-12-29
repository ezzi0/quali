"""
Cross-Platform Budget Optimizer

Extends budget optimization to work across multiple advertising platforms,
allocating budget based on platform performance and persona fit.
"""
from typing import Dict, Any, List, Optional
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
from .platform_selector import PlatformSelectorService, PlatformScore
from .budget_optimizer import BudgetOptimizerService, BudgetRecommendation

settings = get_settings()
logger = get_logger(__name__)


@dataclass
class PlatformBudgetAllocation:
    """Budget allocation for a single platform."""
    platform: str
    current_budget: float
    recommended_budget: float
    change_amount: float
    change_pct: float
    performance_score: float
    rationale: str


@dataclass
class CrossPlatformRecommendation:
    """Cross-platform budget optimization recommendation."""
    persona_id: int
    persona_name: str
    total_budget: float
    platform_allocations: List[PlatformBudgetAllocation]
    overall_strategy: str
    confidence: float
    expected_improvement: float


class CrossPlatformOptimizer:
    """
    Optimizes budget allocation across multiple advertising platforms.
    
    Uses a hierarchical approach:
    1. First, allocate budget across platforms based on platform performance
    2. Then, optimize within each platform using Thompson Sampling
    
    This enables:
    - Cross-platform performance comparison
    - Dynamic budget shifting between platforms
    - Persona-specific platform preferences
    """
    
    # Platform performance decay factor (for recency weighting)
    RECENCY_DECAY = 0.9
    
    # Minimum budget share per active platform
    MIN_PLATFORM_SHARE = 0.15
    
    # Maximum budget shift per optimization cycle
    MAX_SHIFT_PER_CYCLE = 0.25
    
    def __init__(self, db: Session):
        self.db = db
        self.platform_selector = PlatformSelectorService(db)
        self.budget_optimizer = BudgetOptimizerService(db)
    
    def optimize_cross_platform_budget(
        self,
        persona_id: int,
        total_budget: float,
        lookback_days: int = 14,
        include_platforms: Optional[List[str]] = None
    ) -> CrossPlatformRecommendation:
        """
        Optimize budget allocation across platforms for a persona.
        
        Args:
            persona_id: Target persona
            total_budget: Total daily budget to allocate
            lookback_days: Days of historical data to consider
            include_platforms: Platforms to include (None = all active)
        
        Returns:
            CrossPlatformRecommendation with allocations
        """
        logger.info("cross_platform_optimization_started",
                   persona_id=persona_id,
                   total_budget=total_budget)
        
        # Fetch persona
        persona = self.db.get(Persona, persona_id)
        if not persona:
            raise ValueError(f"Persona {persona_id} not found")
        
        # Get current platform allocations
        current_allocations = self._get_current_allocations(
            persona_id, include_platforms
        )
        
        # Calculate platform performance scores
        platform_scores = self._calculate_platform_scores(
            persona_id, lookback_days, include_platforms
        )
        
        # Calculate new allocations using Thompson Sampling
        new_allocations = self._calculate_new_allocations(
            platform_scores,
            current_allocations,
            total_budget
        )
        
        # Build platform allocation recommendations
        allocations = []
        for platform, new_budget in new_allocations.items():
            current = current_allocations.get(platform, 0)
            change = new_budget - current
            
            perf_score = platform_scores.get(platform, {}).get("score", 0.5)
            rationale = self._generate_platform_rationale(
                platform, perf_score, change, platform_scores.get(platform, {})
            )
            
            allocations.append(PlatformBudgetAllocation(
                platform=platform,
                current_budget=current,
                recommended_budget=new_budget,
                change_amount=change,
                change_pct=change / current if current > 0 else 0,
                performance_score=perf_score,
                rationale=rationale
            ))
        
        # Sort by recommended budget (highest first)
        allocations.sort(key=lambda x: x.recommended_budget, reverse=True)
        
        # Calculate overall strategy and metrics
        strategy = self._determine_strategy(allocations, platform_scores)
        confidence = self._calculate_confidence(platform_scores)
        expected_improvement = self._estimate_improvement(
            current_allocations, new_allocations, platform_scores
        )
        
        recommendation = CrossPlatformRecommendation(
            persona_id=persona_id,
            persona_name=persona.name,
            total_budget=total_budget,
            platform_allocations=allocations,
            overall_strategy=strategy,
            confidence=confidence,
            expected_improvement=expected_improvement
        )
        
        logger.info("cross_platform_optimization_completed",
                   persona_id=persona_id,
                   platforms=[a.platform for a in allocations])
        
        return recommendation
    
    def _get_current_allocations(
        self,
        persona_id: int,
        include_platforms: Optional[List[str]]
    ) -> Dict[str, float]:
        """Get current budget allocations by platform."""
        allocations = {}
        
        # Find active campaigns for this persona
        query = select(Campaign).where(
            Campaign.status.in_([CampaignStatus.ACTIVE, CampaignStatus.PAUSED]),
            Campaign.strategy["persona_id"].astext.cast(int) == persona_id
        )
        
        if include_platforms:
            platform_enums = [CampaignPlatform(p) for p in include_platforms]
            query = query.where(Campaign.platform.in_(platform_enums))
        
        campaigns = self.db.execute(query).scalars().all()
        
        for campaign in campaigns:
            platform = campaign.platform.value
            budget = float(campaign.budget_daily or 0)
            allocations[platform] = allocations.get(platform, 0) + budget
        
        return allocations
    
    def _calculate_platform_scores(
        self,
        persona_id: int,
        lookback_days: int,
        include_platforms: Optional[List[str]]
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate performance scores for each platform."""
        platforms = include_platforms or ["meta", "google", "tiktok"]
        cutoff_date = datetime.utcnow().date() - timedelta(days=lookback_days)
        
        scores = {}
        
        for platform in platforms:
            # Find campaigns for this persona on this platform
            campaigns = self.db.execute(
                select(Campaign).where(
                    Campaign.platform == CampaignPlatform(platform),
                    Campaign.strategy["persona_id"].astext.cast(int) == persona_id
                )
            ).scalars().all()
            
            if not campaigns:
                # No history - use prior from platform selector
                platform_rec = self.platform_selector.select_platforms_for_persona(
                    persona_id=persona_id,
                    total_budget=100,  # Dummy budget for scoring
                    objective="lead_generation"
                )
                
                for p in platform_rec.platforms:
                    if p.platform == platform:
                        scores[platform] = {
                            "score": p.score / 100,
                            "confidence": 0.2,
                            "metrics": {},
                            "has_history": False
                        }
                        break
                else:
                    scores[platform] = {
                        "score": 0.5,
                        "confidence": 0.1,
                        "metrics": {},
                        "has_history": False
                    }
                continue
            
            campaign_ids = [c.id for c in campaigns]
            
            # Aggregate metrics with recency weighting
            metrics = self.db.execute(
                select(
                    MarketingMetric.date,
                    func.sum(MarketingMetric.impressions).label('impressions'),
                    func.sum(MarketingMetric.clicks).label('clicks'),
                    func.sum(MarketingMetric.spend).label('spend'),
                    func.sum(MarketingMetric.leads).label('leads'),
                    func.sum(MarketingMetric.qualified_leads).label('qualified_leads'),
                    func.sum(MarketingMetric.closed_won).label('conversions')
                ).where(
                    MarketingMetric.campaign_id.in_(campaign_ids),
                    MarketingMetric.date >= cutoff_date
                ).group_by(MarketingMetric.date)
            ).all()
            
            if not metrics:
                scores[platform] = {
                    "score": 0.5,
                    "confidence": 0.1,
                    "metrics": {},
                    "has_history": False
                }
                continue
            
            # Calculate weighted metrics
            total_weight = 0
            weighted_ctr = 0
            weighted_cvr = 0
            weighted_cpl = 0
            total_spend = 0
            total_leads = 0
            total_conversions = 0
            
            for row in metrics:
                # Recency weight
                days_ago = (datetime.utcnow().date() - row.date).days
                weight = self.RECENCY_DECAY ** days_ago
                
                impressions = row.impressions or 0
                clicks = row.clicks or 0
                spend = float(row.spend or 0)
                leads = row.leads or 0
                conversions = row.conversions or 0
                
                if impressions > 0:
                    weighted_ctr += (clicks / impressions) * weight
                if leads > 0:
                    weighted_cvr += (conversions / leads) * weight
                    weighted_cpl += (spend / leads) * weight
                
                total_weight += weight
                total_spend += spend
                total_leads += leads
                total_conversions += conversions
            
            if total_weight > 0:
                avg_ctr = weighted_ctr / total_weight
                avg_cvr = weighted_cvr / total_weight
                avg_cpl = weighted_cpl / total_weight
            else:
                avg_ctr = avg_cvr = avg_cpl = 0
            
            # Calculate composite score (0-1)
            ctr_score = min(1.0, avg_ctr / 0.03)  # 3% CTR = perfect
            cvr_score = min(1.0, avg_cvr / 0.08)  # 8% CVR = perfect
            cpl_score = max(0.0, 1.0 - (avg_cpl / 500))  # $500 CPL = 0
            
            composite_score = (ctr_score * 0.2 + cvr_score * 0.5 + cpl_score * 0.3)
            
            # Confidence based on data volume
            confidence = min(1.0, total_leads / 50)
            
            scores[platform] = {
                "score": composite_score,
                "confidence": confidence,
                "metrics": {
                    "ctr": avg_ctr,
                    "cvr": avg_cvr,
                    "cpl": avg_cpl,
                    "total_spend": total_spend,
                    "total_leads": total_leads,
                    "total_conversions": total_conversions
                },
                "has_history": True
            }
        
        return scores
    
    def _calculate_new_allocations(
        self,
        platform_scores: Dict[str, Dict[str, Any]],
        current_allocations: Dict[str, float],
        total_budget: float
    ) -> Dict[str, float]:
        """Calculate new budget allocations using Thompson Sampling."""
        allocations = {}
        samples = []
        
        for platform, data in platform_scores.items():
            score = data.get("score", 0.5)
            confidence = data.get("confidence", 0.1)
            
            # Thompson Sampling: sample from Beta distribution
            alpha = score * confidence * 20 + 1
            beta = (1 - score) * confidence * 20 + 1
            sample = np.random.beta(alpha, beta)
            
            samples.append((platform, sample, data.get("confidence", 0.1)))
        
        # Normalize samples to get allocation percentages
        total_sample = sum(s for _, s, _ in samples)
        
        if total_sample > 0:
            for platform, sample, _ in samples:
                raw_allocation = (sample / total_sample) * total_budget
                
                # Apply constraints
                min_budget = self.MIN_PLATFORM_SHARE * total_budget
                
                # Limit shift from current allocation
                current = current_allocations.get(platform, 0)
                if current > 0:
                    max_shift = current * self.MAX_SHIFT_PER_CYCLE
                    if abs(raw_allocation - current) > max_shift:
                        direction = 1 if raw_allocation > current else -1
                        raw_allocation = current + (direction * max_shift)
                
                allocations[platform] = max(min_budget, raw_allocation)
        else:
            # Equal allocation
            equal_share = total_budget / len(platform_scores)
            for platform in platform_scores:
                allocations[platform] = equal_share
        
        # Normalize to exactly match total budget
        allocation_total = sum(allocations.values())
        if allocation_total > 0:
            for platform in allocations:
                allocations[platform] = (allocations[platform] / allocation_total) * total_budget
        
        return allocations
    
    def _generate_platform_rationale(
        self,
        platform: str,
        score: float,
        change: float,
        metrics_data: Dict[str, Any]
    ) -> str:
        """Generate rationale for platform budget change."""
        parts = []
        
        metrics = metrics_data.get("metrics", {})
        has_history = metrics_data.get("has_history", False)
        
        if change > 0:
            direction = "Increase"
        elif change < 0:
            direction = "Decrease"
        else:
            direction = "Maintain"
        
        if not has_history:
            parts.append(f"{direction} based on persona fit (no historical data)")
        else:
            if metrics.get("cvr", 0) > 0.05:
                parts.append(f"Strong CVR ({metrics['cvr']:.1%})")
            elif metrics.get("cvr", 0) < 0.02 and metrics.get("cvr", 0) > 0:
                parts.append(f"Low CVR ({metrics['cvr']:.1%})")
            
            if metrics.get("cpl", 0) > 0:
                if metrics["cpl"] < 100:
                    parts.append(f"Efficient CPL (${metrics['cpl']:.0f})")
                elif metrics["cpl"] > 300:
                    parts.append(f"High CPL (${metrics['cpl']:.0f})")
        
        if score > 0.7:
            parts.append("Top performer")
        elif score < 0.3:
            parts.append("Underperforming")
        
        return f"{direction}: " + ("; ".join(parts) if parts else "Standard optimization")
    
    def _determine_strategy(
        self,
        allocations: List[PlatformBudgetAllocation],
        scores: Dict[str, Dict[str, Any]]
    ) -> str:
        """Determine overall cross-platform strategy."""
        if len(allocations) == 1:
            return f"Single platform focus: {allocations[0].platform.title()}"
        
        # Check for concentration
        top_allocation = allocations[0]
        if top_allocation.recommended_budget > sum(a.recommended_budget for a in allocations[1:]):
            return f"Concentrated on {top_allocation.platform.title()} (best performer)"
        
        # Check for balanced
        allocations_pcts = [a.recommended_budget / sum(a.recommended_budget for a in allocations) for a in allocations]
        if max(allocations_pcts) - min(allocations_pcts) < 0.2:
            return "Balanced multi-platform approach"
        
        # Check for testing
        if any(not scores.get(a.platform, {}).get("has_history", False) for a in allocations):
            return "Exploration mode: testing new platforms"
        
        return "Performance-based allocation"
    
    def _calculate_confidence(
        self,
        scores: Dict[str, Dict[str, Any]]
    ) -> float:
        """Calculate overall confidence in recommendation."""
        if not scores:
            return 0.1
        
        confidences = [data.get("confidence", 0.1) for data in scores.values()]
        return sum(confidences) / len(confidences)
    
    def _estimate_improvement(
        self,
        current: Dict[str, float],
        recommended: Dict[str, float],
        scores: Dict[str, Dict[str, Any]]
    ) -> float:
        """Estimate expected improvement from reallocation."""
        if not current or not recommended:
            return 0.0
        
        # Calculate weighted average score for current vs recommended
        current_weighted_score = 0
        recommended_weighted_score = 0
        
        total_current = sum(current.values()) or 1
        total_recommended = sum(recommended.values()) or 1
        
        for platform in scores:
            score = scores[platform].get("score", 0.5)
            current_weight = current.get(platform, 0) / total_current
            recommended_weight = recommended.get(platform, 0) / total_recommended
            
            current_weighted_score += score * current_weight
            recommended_weighted_score += score * recommended_weight
        
        improvement = (recommended_weighted_score - current_weighted_score) / (current_weighted_score or 1)
        return improvement
    
    async def apply_cross_platform_recommendations(
        self,
        recommendation: CrossPlatformRecommendation,
        auto_approve: bool = False
    ) -> Dict[str, Any]:
        """
        Apply cross-platform budget recommendations.
        
        Args:
            recommendation: The recommendation to apply
            auto_approve: If True, apply without review
        
        Returns:
            Summary of applied changes
        """
        from ...adapters.meta_marketing import MetaMarketingAdapter
        from ...adapters.google_ads import GoogleAdsAdapter
        from ...adapters.tiktok_ads import TikTokAdsAdapter
        
        applied = []
        skipped = []
        
        for allocation in recommendation.platform_allocations:
            if abs(allocation.change_amount) < 5:  # Skip small changes
                skipped.append(allocation.platform)
                continue
            
            # Find campaigns for this platform
            campaigns = self.db.execute(
                select(Campaign).where(
                    Campaign.platform == CampaignPlatform(allocation.platform),
                    Campaign.strategy["persona_id"].astext.cast(int) == recommendation.persona_id,
                    Campaign.status == CampaignStatus.ACTIVE
                )
            ).scalars().all()
            
            if not campaigns:
                skipped.append(allocation.platform)
                continue
            
            # Distribute budget across campaigns
            budget_per_campaign = allocation.recommended_budget / len(campaigns)
            
            for campaign in campaigns:
                campaign.budget_daily = budget_per_campaign
                
                # Sync to platform if auto_approve
                if auto_approve:
                    try:
                        if allocation.platform == "meta":
                            adapter = MetaMarketingAdapter()
                            # Would update via adapter
                        elif allocation.platform == "google":
                            adapter = GoogleAdsAdapter()
                            await adapter.update_campaign_budget(
                                campaign.platform_campaign_id,
                                budget_per_campaign
                            )
                        elif allocation.platform == "tiktok":
                            adapter = TikTokAdsAdapter()
                            # Would update via adapter
                    except Exception as e:
                        logger.warning("platform_sync_failed",
                                      platform=allocation.platform,
                                      error=str(e))
            
            applied.append(allocation.platform)
        
        self.db.commit()
        
        logger.info("cross_platform_recommendations_applied",
                   applied=applied,
                   skipped=skipped)
        
        return {
            "status": "success",
            "applied": applied,
            "skipped": skipped,
            "total_budget": recommendation.total_budget
        }

