"""
Learning Service

Implements the learning and adaptation loop for the marketing agent.
Tracks performance, learns from results, and refines personas and creatives.
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import select, func, update

from ...config import get_settings
from ...logging import get_logger
from ...models import (
    Persona, PersonaStatus, Creative, CreativeStatus,
    Campaign, AdSet, Ad, MarketingMetric,
    CampaignPlatform, CampaignStatus
)

settings = get_settings()
logger = get_logger(__name__)


@dataclass
class CreativePerformance:
    """Performance data for a creative."""
    creative_id: int
    creative_name: str
    persona_id: int
    impressions: int
    clicks: int
    leads: int
    conversions: int
    spend: float
    ctr: float
    cvr: float
    cpl: float
    performance_score: float
    rank: int


@dataclass
class PersonaInsight:
    """Learning insights for a persona."""
    persona_id: int
    persona_name: str
    total_leads: int
    qualified_rate: float
    conversion_rate: float
    avg_cpl: float
    best_platform: str
    best_creative_id: Optional[int]
    best_creative_name: Optional[str]
    messaging_effectiveness: Dict[str, float]
    recommended_adjustments: List[str]


@dataclass
class LearningCycleResult:
    """Results from a learning cycle."""
    cycle_id: str
    timestamp: datetime
    personas_analyzed: int
    creatives_analyzed: int
    insights: List[PersonaInsight]
    creative_rankings: Dict[int, List[CreativePerformance]]
    actions_taken: List[Dict[str, Any]]
    improvements: Dict[str, float]


class LearningService:
    """
    Implements learning and adaptation for marketing campaigns.
    
    Learning loops:
    1. Creative performance learning - which creatives work best per persona
    2. Platform learning - which platforms work best per persona  
    3. Persona refinement - update persona messaging based on results
    4. Budget learning - track ROI and adjust allocations
    
    This enables the agent to improve over time by:
    - Promoting winning creatives
    - Pausing underperformers
    - Refining messaging based on engagement
    - Adjusting platform mix
    """
    
    # Performance thresholds
    TOP_PERFORMER_THRESHOLD = 0.75  # Top 25%
    UNDERPERFORMER_THRESHOLD = 0.25  # Bottom 25%
    
    # Minimum data requirements
    MIN_IMPRESSIONS_FOR_LEARNING = 1000
    MIN_LEADS_FOR_CONFIDENCE = 20
    
    def __init__(self, db: Session):
        self.db = db
    
    def run_learning_cycle(
        self,
        lookback_days: int = 7,
        auto_apply: bool = False
    ) -> LearningCycleResult:
        """
        Run a complete learning cycle.
        
        Args:
            lookback_days: Days of data to analyze
            auto_apply: If True, automatically apply learnings
        
        Returns:
            LearningCycleResult with insights and actions
        """
        cycle_id = f"learn_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        logger.info("learning_cycle_started", cycle_id=cycle_id)
        
        # 1. Analyze creative performance
        creative_rankings = self._analyze_creative_performance(lookback_days)
        
        # 2. Generate persona insights
        insights = self._generate_persona_insights(lookback_days)
        
        # 3. Determine and optionally apply actions
        actions = []
        if auto_apply:
            actions = self._apply_learnings(creative_rankings, insights)
        
        # 4. Calculate improvements
        improvements = self._calculate_improvements(lookback_days)
        
        result = LearningCycleResult(
            cycle_id=cycle_id,
            timestamp=datetime.utcnow(),
            personas_analyzed=len(insights),
            creatives_analyzed=sum(len(v) for v in creative_rankings.values()),
            insights=insights,
            creative_rankings=creative_rankings,
            actions_taken=actions,
            improvements=improvements
        )
        
        logger.info("learning_cycle_completed",
                   cycle_id=cycle_id,
                   personas=len(insights),
                   actions=len(actions))
        
        return result
    
    def _analyze_creative_performance(
        self,
        lookback_days: int
    ) -> Dict[int, List[CreativePerformance]]:
        """Analyze performance of all creatives by persona."""
        cutoff_date = datetime.utcnow().date() - timedelta(days=lookback_days)
        
        # Get all active ads with metrics
        ads = self.db.execute(
            select(Ad).where(
                Ad.status.in_([CampaignStatus.ACTIVE, CampaignStatus.PAUSED])
            )
        ).scalars().all()
        
        rankings = {}  # persona_id -> list of CreativePerformance
        
        for ad in ads:
            creative = ad.creative
            if not creative or not creative.persona_id:
                continue
            
            # Get metrics for this ad
            metrics = self.db.execute(
                select(
                    func.sum(MarketingMetric.impressions).label('impressions'),
                    func.sum(MarketingMetric.clicks).label('clicks'),
                    func.sum(MarketingMetric.spend).label('spend'),
                    func.sum(MarketingMetric.leads).label('leads'),
                    func.sum(MarketingMetric.closed_won).label('conversions')
                ).where(
                    MarketingMetric.ad_id == ad.id,
                    MarketingMetric.date >= cutoff_date
                )
            ).first()
            
            if not metrics or not metrics.impressions:
                continue
            
            impressions = metrics.impressions or 0
            clicks = metrics.clicks or 0
            spend = float(metrics.spend or 0)
            leads = metrics.leads or 0
            conversions = metrics.conversions or 0
            
            if impressions < self.MIN_IMPRESSIONS_FOR_LEARNING:
                continue
            
            ctr = clicks / impressions if impressions > 0 else 0
            cvr = conversions / leads if leads > 0 else 0
            cpl = spend / leads if leads > 0 else 0
            
            # Calculate performance score
            score = self._calculate_creative_score(ctr, cvr, cpl, impressions)
            
            perf = CreativePerformance(
                creative_id=creative.id,
                creative_name=creative.name,
                persona_id=creative.persona_id,
                impressions=impressions,
                clicks=clicks,
                leads=leads,
                conversions=conversions,
                spend=spend,
                ctr=ctr,
                cvr=cvr,
                cpl=cpl,
                performance_score=score,
                rank=0  # Will be set after sorting
            )
            
            if creative.persona_id not in rankings:
                rankings[creative.persona_id] = []
            rankings[creative.persona_id].append(perf)
        
        # Sort and rank within each persona
        for persona_id in rankings:
            rankings[persona_id].sort(key=lambda x: x.performance_score, reverse=True)
            for i, perf in enumerate(rankings[persona_id]):
                perf.rank = i + 1
        
        return rankings
    
    def _calculate_creative_score(
        self,
        ctr: float,
        cvr: float,
        cpl: float,
        impressions: int
    ) -> float:
        """Calculate a composite performance score for a creative."""
        # Normalize metrics to 0-1 scale
        ctr_score = min(1.0, ctr / 0.03)  # 3% CTR = perfect
        cvr_score = min(1.0, cvr / 0.08)  # 8% CVR = perfect
        cpl_score = max(0.0, 1.0 - (cpl / 500))  # $500 CPL = 0
        
        # Volume bonus (more data = more reliable)
        volume_bonus = min(0.1, impressions / 100000)
        
        # Weighted score
        score = (ctr_score * 0.25 + cvr_score * 0.45 + cpl_score * 0.30) + volume_bonus
        
        return score
    
    def _generate_persona_insights(
        self,
        lookback_days: int
    ) -> List[PersonaInsight]:
        """Generate insights for each persona."""
        cutoff_date = datetime.utcnow().date() - timedelta(days=lookback_days)
        
        personas = self.db.execute(
            select(Persona).where(Persona.status == PersonaStatus.ACTIVE)
        ).scalars().all()
        
        insights = []
        
        for persona in personas:
            # Get campaigns for this persona
            campaigns = self.db.execute(
                select(Campaign).where(
                    Campaign.strategy["persona_id"].astext.cast(int) == persona.id
                )
            ).scalars().all()
            
            if not campaigns:
                continue
            
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
            
            if not metrics or not metrics.leads:
                continue
            
            leads = metrics.leads or 0
            qualified = metrics.qualified_leads or 0
            conversions = metrics.conversions or 0
            spend = float(metrics.spend or 0)
            
            qualified_rate = qualified / leads if leads > 0 else 0
            conversion_rate = conversions / leads if leads > 0 else 0
            avg_cpl = spend / leads if leads > 0 else 0
            
            # Find best platform
            best_platform = self._find_best_platform(campaign_ids, cutoff_date)
            
            # Find best creative
            best_creative = self._find_best_creative(persona.id, cutoff_date)
            
            # Analyze messaging effectiveness
            messaging_effectiveness = self._analyze_messaging_effectiveness(
                persona, cutoff_date
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                persona, qualified_rate, conversion_rate, avg_cpl,
                best_platform, messaging_effectiveness
            )
            
            insight = PersonaInsight(
                persona_id=persona.id,
                persona_name=persona.name,
                total_leads=leads,
                qualified_rate=qualified_rate,
                conversion_rate=conversion_rate,
                avg_cpl=avg_cpl,
                best_platform=best_platform,
                best_creative_id=best_creative[0] if best_creative else None,
                best_creative_name=best_creative[1] if best_creative else None,
                messaging_effectiveness=messaging_effectiveness,
                recommended_adjustments=recommendations
            )
            
            insights.append(insight)
        
        return insights
    
    def _find_best_platform(
        self,
        campaign_ids: List[int],
        cutoff_date
    ) -> str:
        """Find the best performing platform for campaigns."""
        platform_performance = {}
        
        for platform in ["meta", "google", "tiktok"]:
            # Get campaigns for this platform
            platform_campaigns = self.db.execute(
                select(Campaign.id).where(
                    Campaign.id.in_(campaign_ids),
                    Campaign.platform == CampaignPlatform(platform)
                )
            ).scalars().all()
            
            if not platform_campaigns:
                continue
            
            # Get metrics
            metrics = self.db.execute(
                select(
                    func.sum(MarketingMetric.leads).label('leads'),
                    func.sum(MarketingMetric.closed_won).label('conversions')
                ).where(
                    MarketingMetric.campaign_id.in_(platform_campaigns),
                    MarketingMetric.date >= cutoff_date
                )
            ).first()
            
            if metrics and metrics.leads:
                cvr = (metrics.conversions or 0) / metrics.leads
                platform_performance[platform] = cvr
        
        if not platform_performance:
            return "meta"  # Default
        
        return max(platform_performance, key=platform_performance.get)
    
    def _find_best_creative(
        self,
        persona_id: int,
        cutoff_date
    ) -> Optional[Tuple[int, str]]:
        """Find the best performing creative for a persona."""
        creatives = self.db.execute(
            select(Creative).where(Creative.persona_id == persona_id)
        ).scalars().all()
        
        if not creatives:
            return None
        
        best_creative = None
        best_score = -1
        
        for creative in creatives:
            # Get ads using this creative
            ads = self.db.execute(
                select(Ad.id).where(Ad.creative_id == creative.id)
            ).scalars().all()
            
            if not ads:
                continue
            
            # Get metrics
            metrics = self.db.execute(
                select(
                    func.sum(MarketingMetric.impressions).label('impressions'),
                    func.sum(MarketingMetric.clicks).label('clicks'),
                    func.sum(MarketingMetric.leads).label('leads'),
                    func.sum(MarketingMetric.spend).label('spend'),
                    func.sum(MarketingMetric.closed_won).label('conversions')
                ).where(
                    MarketingMetric.ad_id.in_(ads),
                    MarketingMetric.date >= cutoff_date
                )
            ).first()
            
            if not metrics or not metrics.impressions:
                continue
            
            impressions = metrics.impressions or 0
            clicks = metrics.clicks or 0
            leads = metrics.leads or 0
            spend = float(metrics.spend or 0)
            conversions = metrics.conversions or 0
            
            ctr = clicks / impressions if impressions > 0 else 0
            cvr = conversions / leads if leads > 0 else 0
            cpl = spend / leads if leads > 0 else 0
            
            score = self._calculate_creative_score(ctr, cvr, cpl, impressions)
            
            if score > best_score:
                best_score = score
                best_creative = (creative.id, creative.name)
        
        return best_creative
    
    def _analyze_messaging_effectiveness(
        self,
        persona: Persona,
        cutoff_date
    ) -> Dict[str, float]:
        """Analyze which messaging hooks are most effective."""
        messaging = persona.messaging or {}
        hooks = messaging.get("hooks", [])
        
        if not hooks:
            return {}
        
        # Get creatives for this persona
        creatives = self.db.execute(
            select(Creative).where(Creative.persona_id == persona.id)
        ).scalars().all()
        
        hook_performance = {}
        
        for hook in hooks:
            # Find creatives using this hook (simple text matching)
            hook_lower = hook.lower()
            matching_creatives = [
                c for c in creatives
                if hook_lower in (c.headline or "").lower() 
                or hook_lower in (c.primary_text or "").lower()
            ]
            
            if not matching_creatives:
                continue
            
            creative_ids = [c.id for c in matching_creatives]
            
            # Get ads using these creatives
            ads = self.db.execute(
                select(Ad.id).where(Ad.creative_id.in_(creative_ids))
            ).scalars().all()
            
            if not ads:
                continue
            
            # Get metrics
            metrics = self.db.execute(
                select(
                    func.sum(MarketingMetric.impressions).label('impressions'),
                    func.sum(MarketingMetric.clicks).label('clicks')
                ).where(
                    MarketingMetric.ad_id.in_(ads),
                    MarketingMetric.date >= cutoff_date
                )
            ).first()
            
            if metrics and metrics.impressions:
                ctr = (metrics.clicks or 0) / metrics.impressions
                hook_performance[hook] = ctr
        
        return hook_performance
    
    def _generate_recommendations(
        self,
        persona: Persona,
        qualified_rate: float,
        conversion_rate: float,
        avg_cpl: float,
        best_platform: str,
        messaging_effectiveness: Dict[str, float]
    ) -> List[str]:
        """Generate actionable recommendations for persona improvement."""
        recommendations = []
        
        # Qualification rate recommendations
        if qualified_rate < 0.5:
            recommendations.append(
                "Low qualification rate - consider tighter targeting or different messaging"
            )
        elif qualified_rate > 0.8:
            recommendations.append(
                "High qualification rate - consider expanding audience reach"
            )
        
        # Conversion rate recommendations
        if conversion_rate < 0.03:
            recommendations.append(
                "Low conversion rate - review follow-up process and offer"
            )
        
        # CPL recommendations
        if avg_cpl > 200:
            recommendations.append(
                f"High CPL (${avg_cpl:.0f}) - optimize bidding and targeting"
            )
        elif avg_cpl < 50 and conversion_rate > 0.05:
            recommendations.append(
                f"Excellent efficiency (${avg_cpl:.0f} CPL, {conversion_rate:.1%} CVR) - increase budget"
            )
        
        # Platform recommendations
        characteristics = persona.characteristics or {}
        if best_platform == "google" and characteristics.get("urgency") != "high":
            recommendations.append(
                "Google performing well - persona may have higher intent than expected"
            )
        
        # Messaging recommendations
        if messaging_effectiveness:
            best_hook = max(messaging_effectiveness, key=messaging_effectiveness.get)
            worst_hook = min(messaging_effectiveness, key=messaging_effectiveness.get)
            
            if messaging_effectiveness[best_hook] > 0.04:
                recommendations.append(
                    f"Top hook: '{best_hook}' - create more variations"
                )
            
            if messaging_effectiveness[worst_hook] < 0.01:
                recommendations.append(
                    f"Underperforming hook: '{worst_hook}' - consider replacing"
                )
        
        return recommendations
    
    def _apply_learnings(
        self,
        creative_rankings: Dict[int, List[CreativePerformance]],
        insights: List[PersonaInsight]
    ) -> List[Dict[str, Any]]:
        """Apply learnings automatically."""
        actions = []
        
        # 1. Pause underperforming creatives
        for persona_id, rankings in creative_rankings.items():
            if len(rankings) < 3:
                continue
            
            threshold_idx = int(len(rankings) * self.UNDERPERFORMER_THRESHOLD)
            underperformers = rankings[-threshold_idx:] if threshold_idx > 0 else []
            
            for perf in underperformers:
                if perf.leads >= self.MIN_LEADS_FOR_CONFIDENCE:
                    # Pause the creative
                    self.db.execute(
                        update(Creative)
                        .where(Creative.id == perf.creative_id)
                        .values(status=CreativeStatus.ARCHIVED)
                    )
                    
                    actions.append({
                        "type": "pause_creative",
                        "creative_id": perf.creative_id,
                        "reason": f"Underperforming (rank {perf.rank}/{len(rankings)}, CVR: {perf.cvr:.2%})"
                    })
        
        # 2. Update persona metrics
        for insight in insights:
            persona = self.db.get(Persona, insight.persona_id)
            if persona:
                current_metrics = persona.metrics or {}
                current_metrics.update({
                    "last_learning_cycle": datetime.utcnow().isoformat(),
                    "total_leads": insight.total_leads,
                    "qualified_rate": insight.qualified_rate,
                    "conversion_rate": insight.conversion_rate,
                    "avg_cpl": insight.avg_cpl,
                    "best_platform": insight.best_platform
                })
                persona.metrics = current_metrics
                
                actions.append({
                    "type": "update_persona_metrics",
                    "persona_id": insight.persona_id,
                    "metrics_updated": list(current_metrics.keys())
                })
        
        self.db.commit()
        
        return actions
    
    def _calculate_improvements(
        self,
        lookback_days: int
    ) -> Dict[str, float]:
        """Calculate improvement metrics compared to previous period."""
        current_start = datetime.utcnow().date() - timedelta(days=lookback_days)
        previous_start = current_start - timedelta(days=lookback_days)
        
        # Current period metrics
        current_metrics = self.db.execute(
            select(
                func.sum(MarketingMetric.spend).label('spend'),
                func.sum(MarketingMetric.leads).label('leads'),
                func.sum(MarketingMetric.closed_won).label('conversions')
            ).where(MarketingMetric.date >= current_start)
        ).first()
        
        # Previous period metrics
        previous_metrics = self.db.execute(
            select(
                func.sum(MarketingMetric.spend).label('spend'),
                func.sum(MarketingMetric.leads).label('leads'),
                func.sum(MarketingMetric.closed_won).label('conversions')
            ).where(
                MarketingMetric.date >= previous_start,
                MarketingMetric.date < current_start
            )
        ).first()
        
        improvements = {}
        
        if current_metrics and previous_metrics:
            # CPL improvement
            current_cpl = (float(current_metrics.spend or 0) / 
                          (current_metrics.leads or 1))
            previous_cpl = (float(previous_metrics.spend or 0) / 
                           (previous_metrics.leads or 1))
            if previous_cpl > 0:
                improvements["cpl_change"] = (previous_cpl - current_cpl) / previous_cpl
            
            # CVR improvement
            current_cvr = ((current_metrics.conversions or 0) / 
                          (current_metrics.leads or 1))
            previous_cvr = ((previous_metrics.conversions or 0) / 
                           (previous_metrics.leads or 1))
            if previous_cvr > 0:
                improvements["cvr_change"] = (current_cvr - previous_cvr) / previous_cvr
            
            # Lead volume change
            current_leads = current_metrics.leads or 0
            previous_leads = previous_metrics.leads or 0
            if previous_leads > 0:
                improvements["lead_volume_change"] = (current_leads - previous_leads) / previous_leads
        
        return improvements
    
    def get_learning_summary(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get a summary of learning over a period."""
        cutoff_date = datetime.utcnow().date() - timedelta(days=days)
        
        # Count personas with data
        personas_with_campaigns = self.db.execute(
            select(func.count(func.distinct(
                Campaign.strategy["persona_id"].astext
            ))).where(Campaign.status == CampaignStatus.ACTIVE)
        ).scalar()
        
        # Count active creatives
        active_creatives = self.db.execute(
            select(func.count(Creative.id)).where(
                Creative.status == CreativeStatus.ACTIVE
            )
        ).scalar()
        
        # Get overall metrics
        metrics = self.db.execute(
            select(
                func.sum(MarketingMetric.spend).label('spend'),
                func.sum(MarketingMetric.leads).label('leads'),
                func.sum(MarketingMetric.closed_won).label('conversions')
            ).where(MarketingMetric.date >= cutoff_date)
        ).first()
        
        return {
            "period_days": days,
            "personas_with_campaigns": personas_with_campaigns or 0,
            "active_creatives": active_creatives or 0,
            "total_spend": float(metrics.spend or 0) if metrics else 0,
            "total_leads": metrics.leads or 0 if metrics else 0,
            "total_conversions": metrics.conversions or 0 if metrics else 0,
            "avg_cpl": (float(metrics.spend or 0) / (metrics.leads or 1)) if metrics else 0,
            "avg_cvr": ((metrics.conversions or 0) / (metrics.leads or 1)) if metrics and metrics.leads else 0
        }

