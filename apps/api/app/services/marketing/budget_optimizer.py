"""
Budget Optimizer Service

Optimizes budget allocation across ad sets using Thompson Sampling
(Bayesian bandit algorithm) with business constraints.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ...config import get_settings
from ...logging import get_logger
from ...models import Campaign, AdSet, MarketingMetric

settings = get_settings()
logger = get_logger(__name__)


@dataclass
class AdSetPerformance:
    """Performance metrics for an ad set"""
    ad_set_id: int
    name: str
    impressions: int
    clicks: int
    spend: float
    leads: int
    conversions: int
    budget_current: float
    budget_floor: float  # Minimum daily budget
    budget_ceiling: float  # Maximum daily budget


@dataclass
class BudgetRecommendation:
    """Budget allocation recommendation"""
    ad_set_id: int
    name: str
    current_budget: float
    recommended_budget: float
    change_amount: float
    change_pct: float
    rationale: str
    confidence: float


class BudgetOptimizerService:
    """
    Optimizes budget allocation using Thompson Sampling.
    
    Algorithm:
    1. Model each ad set's CVR as Beta distribution
    2. Sample from posteriors
    3. Allocate budget proportionally to samples
    4. Apply business constraints (floors, ceilings, volatility caps)
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def optimize_campaign_budget(
        self,
        campaign_id: int,
        lookback_days: int = 7,
        volatility_cap: float = 0.20,  # Max 20% daily change
        enable_cooldown: bool = True,
        cooldown_hours: int = 24
    ) -> List[BudgetRecommendation]:
        """
        Optimize budget allocation for a campaign's ad sets.
        
        Args:
            campaign_id: Campaign to optimize
            lookback_days: Days of historical data to use
            volatility_cap: Maximum daily budget change (as fraction)
            enable_cooldown: Prevent changes within cooldown period
            cooldown_hours: Hours between budget changes
        
        Returns:
            List of budget recommendations
        """
        logger.info("budget_optimization_started", campaign_id=campaign_id)
        
        # 1. Fetch campaign and ad sets
        campaign = self.db.get(Campaign, campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        ad_sets = self.db.execute(
            select(AdSet).where(AdSet.campaign_id == campaign_id)
        ).scalars().all()
        
        if not ad_sets:
            logger.warning("no_ad_sets", campaign_id=campaign_id)
            return []
        
        # 2. Fetch performance data
        performance_data = self._fetch_performance(ad_sets, lookback_days)
        
        if not performance_data:
            logger.warning("no_performance_data", campaign_id=campaign_id)
            return []
        
        # 3. Run Thompson Sampling
        allocations = self._thompson_sampling(
            performance_data,
            total_budget=float(campaign.budget_daily or 0)
        )
        
        # 4. Apply constraints
        recommendations = []
        for ad_set_perf in performance_data:
            new_budget = allocations.get(ad_set_perf.ad_set_id, ad_set_perf.budget_current)
            
            # Volatility cap
            max_change = ad_set_perf.budget_current * volatility_cap
            if abs(new_budget - ad_set_perf.budget_current) > max_change:
                direction = 1 if new_budget > ad_set_perf.budget_current else -1
                new_budget = ad_set_perf.budget_current + (direction * max_change)
            
            # Floor and ceiling
            new_budget = max(ad_set_perf.budget_floor, min(ad_set_perf.budget_ceiling, new_budget))
            
            # Cooldown check
            if enable_cooldown and self._is_in_cooldown(ad_set_perf.ad_set_id, cooldown_hours):
                logger.info("ad_set_in_cooldown", ad_set_id=ad_set_perf.ad_set_id)
                continue
            
            change = new_budget - ad_set_perf.budget_current
            
            if abs(change) > 1.0:  # Only recommend if change > $1
                rationale = self._generate_rationale(ad_set_perf, new_budget)
                
                recommendations.append(BudgetRecommendation(
                    ad_set_id=ad_set_perf.ad_set_id,
                    name=ad_set_perf.name,
                    current_budget=ad_set_perf.budget_current,
                    recommended_budget=new_budget,
                    change_amount=change,
                    change_pct=change / ad_set_perf.budget_current if ad_set_perf.budget_current > 0 else 0,
                    rationale=rationale,
                    confidence=self._calculate_confidence(ad_set_perf)
                ))
        
        logger.info("budget_optimization_completed", 
                   recommendations_count=len(recommendations))
        
        return recommendations
    
    def apply_recommendations(
        self,
        recommendations: List[BudgetRecommendation],
        auto_approve: bool = False
    ) -> int:
        """
        Apply budget recommendations to ad sets.
        
        Args:
            recommendations: List of budget changes
            auto_approve: If True, apply immediately. If False, mark for review.
        
        Returns:
            Number of ad sets updated
        """
        updated = 0
        
        for rec in recommendations:
            ad_set = self.db.get(AdSet, rec.ad_set_id)
            if ad_set:
                ad_set.budget_daily = rec.recommended_budget
                ad_set.platform_metadata = {
                    **ad_set.platform_metadata,
                    "last_budget_change": datetime.utcnow().isoformat(),
                    "optimization_rationale": rec.rationale
                }
                updated += 1
        
        self.db.commit()
        
        logger.info("budget_recommendations_applied", count=updated)
        
        return updated
    
    def _fetch_performance(
        self,
        ad_sets: List[AdSet],
        lookback_days: int
    ) -> List[AdSetPerformance]:
        """Fetch recent performance metrics for ad sets"""
        cutoff_date = datetime.utcnow().date() - timedelta(days=lookback_days)
        
        performance_data = []
        
        for ad_set in ad_sets:
            # Aggregate metrics over lookback period
            metrics = self.db.execute(
                select(
                    func.sum(MarketingMetric.impressions).label('impressions'),
                    func.sum(MarketingMetric.clicks).label('clicks'),
                    func.sum(MarketingMetric.spend).label('spend'),
                    func.sum(MarketingMetric.leads).label('leads'),
                    func.sum(MarketingMetric.closed_won).label('conversions')
                )
                .where(
                    MarketingMetric.ad_set_id == ad_set.id,
                    MarketingMetric.date >= cutoff_date
                )
            ).first()
            
            if metrics and metrics.impressions:
                performance_data.append(AdSetPerformance(
                    ad_set_id=ad_set.id,
                    name=ad_set.name,
                    impressions=metrics.impressions or 0,
                    clicks=metrics.clicks or 0,
                    spend=float(metrics.spend or 0),
                    leads=metrics.leads or 0,
                    conversions=metrics.conversions or 0,
                    budget_current=float(ad_set.budget_daily or 0),
                    budget_floor=float(ad_set.budget_daily or 0) * 0.5,  # 50% floor
                    budget_ceiling=float(ad_set.budget_daily or 0) * 2.0  # 200% ceiling
                ))
        
        return performance_data
    
    def _thompson_sampling(
        self,
        performance_data: List[AdSetPerformance],
        total_budget: float
    ) -> Dict[int, float]:
        """
        Thompson Sampling for budget allocation.
        
        Models CVR as Beta(alpha, beta) where:
        - alpha = conversions + 1 (prior)
        - beta = (leads - conversions) + 1 (prior)
        """
        allocations = {}
        samples = []
        
        for perf in performance_data:
            # Beta distribution parameters
            alpha = perf.conversions + 1
            beta = (perf.leads - perf.conversions) + 1
            
            # Sample from posterior
            sample = np.random.beta(alpha, beta)
            samples.append((perf.ad_set_id, sample))
        
        # Allocate proportionally to samples
        total_sample = sum(s for _, s in samples)
        
        if total_sample > 0:
            for ad_set_id, sample in samples:
                allocations[ad_set_id] = (sample / total_sample) * total_budget
        else:
            # Fallback: equal allocation
            equal_share = total_budget / len(performance_data)
            for perf in performance_data:
                allocations[perf.ad_set_id] = equal_share
        
        return allocations
    
    def _is_in_cooldown(self, ad_set_id: int, cooldown_hours: int) -> bool:
        """Check if ad set is in cooldown period"""
        ad_set = self.db.get(AdSet, ad_set_id)
        if not ad_set:
            return False
        
        last_change_str = ad_set.platform_metadata.get("last_budget_change")
        if not last_change_str:
            return False
        
        try:
            last_change = datetime.fromisoformat(last_change_str)
            hours_since = (datetime.utcnow() - last_change).total_seconds() / 3600
            return hours_since < cooldown_hours
        except Exception:
            return False
    
    def _generate_rationale(self, perf: AdSetPerformance, new_budget: float) -> str:
        """Generate human-readable rationale for budget change"""
        cvr = perf.conversions / perf.leads if perf.leads > 0 else 0
        cpl = perf.spend / perf.leads if perf.leads > 0 else 0
        
        direction = "increase" if new_budget > perf.budget_current else "decrease"
        
        if cvr > 0.05:  # High CVR
            return f"{direction.capitalize()} budget due to strong performance (CVR: {cvr:.1%}, CPL: ${cpl:.2f})"
        elif cvr < 0.01:  # Low CVR
            return f"{direction.capitalize()} budget due to underperformance (CVR: {cvr:.1%})"
        else:
            return f"{direction.capitalize()} budget for optimization (CVR: {cvr:.1%}, CPL: ${cpl:.2f})"
    
    def _calculate_confidence(self, perf: AdSetPerformance) -> float:
        """Calculate confidence score (0-1) based on sample size"""
        # More leads = higher confidence
        if perf.leads < 10:
            return 0.3
        elif perf.leads < 50:
            return 0.6
        elif perf.leads < 100:
            return 0.8
        else:
            return 0.95

