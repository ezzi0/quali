"""
Experiment Runner Service

Executes and analyzes A/B tests for marketing campaigns.
Implements statistical significance testing and auto-stopping rules.
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from scipy import stats
from sqlalchemy.orm import Session
from sqlalchemy import select, func, update

from ...config import get_settings
from ...logging import get_logger
from ...models import (
    Experiment, ExperimentStatus, ExperimentType,
    Campaign, AdSet, Ad, MarketingMetric, Creative,
    CampaignStatus
)

settings = get_settings()
logger = get_logger(__name__)


@dataclass
class VariantResult:
    """Results for a single experiment variant."""
    variant_name: str
    creative_id: Optional[int]
    impressions: int
    clicks: int
    leads: int
    conversions: int
    spend: float
    ctr: float
    cvr: float
    cpl: float


@dataclass
class ExperimentResult:
    """Complete experiment analysis result."""
    experiment_id: int
    experiment_name: str
    status: str
    control: VariantResult
    variants: List[VariantResult]
    winner: Optional[str]
    winning_variant: Optional[VariantResult]
    lift: float
    p_value: float
    confidence_interval: Tuple[float, float]
    is_significant: bool
    sample_size_sufficient: bool
    recommendation: str
    days_running: int


class ExperimentRunnerService:
    """
    Runs and analyzes A/B experiments for marketing.
    
    Features:
    1. Create experiments from personas/creatives
    2. Monitor running experiments
    3. Statistical significance testing
    4. Auto-stopping rules
    5. Winner declaration and application
    
    Uses Bayesian A/B testing with early stopping.
    """
    
    # Statistical parameters
    DEFAULT_CONFIDENCE_LEVEL = 0.95
    DEFAULT_MDE = 0.05  # 5% minimum detectable effect
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_experiment(
        self,
        name: str,
        persona_id: int,
        control_creative_id: int,
        variant_creative_ids: List[int],
        hypothesis: str,
        experiment_type: ExperimentType = ExperimentType.AB_TEST,
        confidence_level: float = DEFAULT_CONFIDENCE_LEVEL,
        mde: float = DEFAULT_MDE,
        min_sample_size: int = 1000,
        max_duration_days: int = 14
    ) -> Experiment:
        """
        Create a new experiment.
        
        Args:
            name: Experiment name
            persona_id: Target persona
            control_creative_id: Control creative ID
            variant_creative_ids: List of variant creative IDs
            hypothesis: What we're testing
            experiment_type: Type of experiment
            confidence_level: Required confidence level (0.95 = 95%)
            mde: Minimum detectable effect
            min_sample_size: Minimum impressions per variant
            max_duration_days: Maximum experiment duration
        
        Returns:
            Created Experiment object
        """
        logger.info("creating_experiment", name=name, persona_id=persona_id)
        
        # Build design spec
        design = {
            "control": {"creative_id": control_creative_id},
            "variants": [
                {"name": f"variant_{i+1}", "creative_id": cid}
                for i, cid in enumerate(variant_creative_ids)
            ],
            "split": self._calculate_traffic_split(1 + len(variant_creative_ids)),
            "metrics": ["ctr", "cvr", "cpl"],
            "mde": mde
        }
        
        # Build stopping rules
        stop_rules = {
            "max_duration_days": max_duration_days,
            "early_stop_on_significance": True,
            "futility_threshold": 0.1,  # Stop if winning probability < 10%
            "min_sample_per_variant": min_sample_size
        }
        
        experiment = Experiment(
            name=name,
            persona_id=persona_id,
            type=experiment_type,
            status=ExperimentStatus.DRAFT,
            hypothesis=hypothesis,
            design=design,
            confidence_level=confidence_level,
            minimum_sample_size=min_sample_size,
            mde=mde,
            stop_rules=stop_rules,
            results={}
        )
        
        self.db.add(experiment)
        self.db.commit()
        
        logger.info("experiment_created", experiment_id=experiment.id, name=name)
        
        return experiment
    
    def _calculate_traffic_split(self, num_variants: int) -> List[float]:
        """Calculate equal traffic split."""
        split = 1.0 / num_variants
        return [split] * num_variants
    
    def start_experiment(self, experiment_id: int) -> Experiment:
        """Start an experiment."""
        experiment = self.db.get(Experiment, experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        if experiment.status != ExperimentStatus.DRAFT:
            raise ValueError(f"Experiment is {experiment.status.value}, cannot start")
        
        experiment.status = ExperimentStatus.RUNNING
        experiment.start_date = datetime.utcnow()
        
        self.db.commit()
        
        logger.info("experiment_started", experiment_id=experiment_id)
        
        return experiment
    
    def analyze_experiment(self, experiment_id: int) -> ExperimentResult:
        """
        Analyze a running or completed experiment.
        
        Args:
            experiment_id: Experiment to analyze
        
        Returns:
            ExperimentResult with statistical analysis
        """
        experiment = self.db.get(Experiment, experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        design = experiment.design or {}
        
        # Get control results
        control_creative_id = design.get("control", {}).get("creative_id")
        control_result = self._get_variant_metrics(
            control_creative_id, experiment.start_date, "control"
        )
        
        # Get variant results
        variant_results = []
        for variant in design.get("variants", []):
            creative_id = variant.get("creative_id")
            name = variant.get("name", "variant")
            result = self._get_variant_metrics(creative_id, experiment.start_date, name)
            variant_results.append(result)
        
        # Find best variant
        all_results = [control_result] + variant_results
        best_variant = max(all_results, key=lambda x: x.cvr if x.leads > 0 else 0)
        
        # Calculate statistical significance
        winner = None
        lift = 0.0
        p_value = 1.0
        confidence_interval = (0.0, 0.0)
        is_significant = False
        
        if control_result.leads > 0 and any(v.leads > 0 for v in variant_results):
            for variant in variant_results:
                if variant.leads == 0:
                    continue
                
                # Z-test for proportions (CVR)
                p_value_v, lift_v, ci = self._calculate_significance(
                    control_result.conversions, control_result.leads,
                    variant.conversions, variant.leads
                )
                
                if p_value_v < p_value:
                    p_value = p_value_v
                    lift = lift_v
                    confidence_interval = ci
                    
                    if p_value < (1 - experiment.confidence_level):
                        is_significant = True
                        if lift > 0:
                            winner = variant.variant_name
                        else:
                            winner = "control"
        
        # Check sample size sufficiency
        min_sample = experiment.minimum_sample_size
        sample_sufficient = all(
            r.impressions >= min_sample for r in all_results
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            experiment, is_significant, winner, lift, sample_sufficient
        )
        
        # Calculate days running
        days_running = 0
        if experiment.start_date:
            days_running = (datetime.utcnow() - experiment.start_date).days
        
        # Update experiment results
        experiment.results = {
            "analyzed_at": datetime.utcnow().isoformat(),
            "winner": winner,
            "lift": lift,
            "p_value": p_value,
            "confidence_interval": list(confidence_interval),
            "is_significant": is_significant,
            "recommendation": recommendation
        }
        self.db.commit()
        
        return ExperimentResult(
            experiment_id=experiment_id,
            experiment_name=experiment.name,
            status=experiment.status.value,
            control=control_result,
            variants=variant_results,
            winner=winner,
            winning_variant=best_variant if winner else None,
            lift=lift,
            p_value=p_value,
            confidence_interval=confidence_interval,
            is_significant=is_significant,
            sample_size_sufficient=sample_sufficient,
            recommendation=recommendation,
            days_running=days_running
        )
    
    def _get_variant_metrics(
        self,
        creative_id: Optional[int],
        start_date: Optional[datetime],
        variant_name: str
    ) -> VariantResult:
        """Get performance metrics for a variant."""
        if not creative_id:
            return VariantResult(
                variant_name=variant_name,
                creative_id=None,
                impressions=0, clicks=0, leads=0, conversions=0,
                spend=0, ctr=0, cvr=0, cpl=0
            )
        
        # Find ads using this creative
        ads = self.db.execute(
            select(Ad.id).where(Ad.creative_id == creative_id)
        ).scalars().all()
        
        if not ads:
            return VariantResult(
                variant_name=variant_name,
                creative_id=creative_id,
                impressions=0, clicks=0, leads=0, conversions=0,
                spend=0, ctr=0, cvr=0, cpl=0
            )
        
        # Get metrics
        query = select(
            func.sum(MarketingMetric.impressions).label('impressions'),
            func.sum(MarketingMetric.clicks).label('clicks'),
            func.sum(MarketingMetric.leads).label('leads'),
            func.sum(MarketingMetric.closed_won).label('conversions'),
            func.sum(MarketingMetric.spend).label('spend')
        ).where(MarketingMetric.ad_id.in_(ads))
        
        if start_date:
            query = query.where(MarketingMetric.date >= start_date.date())
        
        metrics = self.db.execute(query).first()
        
        impressions = metrics.impressions or 0
        clicks = metrics.clicks or 0
        leads = metrics.leads or 0
        conversions = metrics.conversions or 0
        spend = float(metrics.spend or 0)
        
        return VariantResult(
            variant_name=variant_name,
            creative_id=creative_id,
            impressions=impressions,
            clicks=clicks,
            leads=leads,
            conversions=conversions,
            spend=spend,
            ctr=clicks / impressions if impressions > 0 else 0,
            cvr=conversions / leads if leads > 0 else 0,
            cpl=spend / leads if leads > 0 else 0
        )
    
    def _calculate_significance(
        self,
        control_conversions: int,
        control_trials: int,
        variant_conversions: int,
        variant_trials: int
    ) -> Tuple[float, float, Tuple[float, float]]:
        """
        Calculate statistical significance using Z-test for proportions.
        
        Returns:
            (p_value, lift, confidence_interval)
        """
        if control_trials == 0 or variant_trials == 0:
            return 1.0, 0.0, (0.0, 0.0)
        
        # Conversion rates
        p1 = control_conversions / control_trials
        p2 = variant_conversions / variant_trials
        
        if p1 == 0:
            return 1.0, 0.0, (0.0, 0.0)
        
        # Lift
        lift = (p2 - p1) / p1
        
        # Pooled proportion
        p_pooled = (control_conversions + variant_conversions) / (control_trials + variant_trials)
        
        # Standard error
        se = np.sqrt(p_pooled * (1 - p_pooled) * (1/control_trials + 1/variant_trials))
        
        if se == 0:
            return 1.0, lift, (0.0, 0.0)
        
        # Z-statistic
        z = (p2 - p1) / se
        
        # Two-tailed p-value
        p_value = 2 * (1 - stats.norm.cdf(abs(z)))
        
        # 95% confidence interval for difference
        z_95 = 1.96
        diff = p2 - p1
        ci_lower = diff - z_95 * se
        ci_upper = diff + z_95 * se
        
        return p_value, lift, (ci_lower, ci_upper)
    
    def _generate_recommendation(
        self,
        experiment: Experiment,
        is_significant: bool,
        winner: Optional[str],
        lift: float,
        sample_sufficient: bool
    ) -> str:
        """Generate actionable recommendation."""
        if not sample_sufficient:
            return "Continue experiment - insufficient sample size"
        
        stop_rules = experiment.stop_rules or {}
        max_days = stop_rules.get("max_duration_days", 14)
        
        days_running = 0
        if experiment.start_date:
            days_running = (datetime.utcnow() - experiment.start_date).days
        
        if is_significant:
            if winner == "control":
                return f"Stop experiment - Control wins with {abs(lift):.1%} advantage"
            elif winner:
                return f"Stop experiment - {winner} wins with {lift:.1%} lift. Deploy to all traffic."
        
        if days_running >= max_days:
            return "Stop experiment - Maximum duration reached. No significant winner."
        
        # Check futility
        if abs(lift) < experiment.mde / 2 and days_running > max_days / 2:
            return "Consider stopping - Unlikely to reach minimum detectable effect"
        
        return f"Continue experiment - Day {days_running}/{max_days}"
    
    def stop_experiment(
        self,
        experiment_id: int,
        reason: str = "manual"
    ) -> Experiment:
        """Stop an experiment."""
        experiment = self.db.get(Experiment, experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment.status = ExperimentStatus.STOPPED
        experiment.stop_date = datetime.utcnow()
        
        results = experiment.results or {}
        results["stop_reason"] = reason
        experiment.results = results
        
        self.db.commit()
        
        logger.info("experiment_stopped", experiment_id=experiment_id, reason=reason)
        
        return experiment
    
    def complete_experiment(
        self,
        experiment_id: int,
        apply_winner: bool = False
    ) -> Experiment:
        """
        Complete an experiment and optionally apply the winner.
        
        Args:
            experiment_id: Experiment to complete
            apply_winner: If True, promote winning creative to all traffic
        
        Returns:
            Updated Experiment
        """
        experiment = self.db.get(Experiment, experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        # Final analysis
        result = self.analyze_experiment(experiment_id)
        
        experiment.status = ExperimentStatus.COMPLETED
        experiment.stop_date = datetime.utcnow()
        
        if apply_winner and result.winner and result.is_significant:
            self._apply_winning_variant(experiment, result)
            
            results = experiment.results or {}
            results["winner_applied"] = True
            results["applied_at"] = datetime.utcnow().isoformat()
            experiment.results = results
        
        self.db.commit()
        
        logger.info("experiment_completed",
                   experiment_id=experiment_id,
                   winner=result.winner,
                   applied=apply_winner)
        
        return experiment
    
    def _apply_winning_variant(
        self,
        experiment: Experiment,
        result: ExperimentResult
    ) -> None:
        """Apply winning variant to all traffic."""
        if not result.winning_variant or not result.winning_variant.creative_id:
            return
        
        winning_creative_id = result.winning_variant.creative_id
        design = experiment.design or {}
        
        # Get all creative IDs in experiment
        all_creative_ids = [design.get("control", {}).get("creative_id")]
        for variant in design.get("variants", []):
            all_creative_ids.append(variant.get("creative_id"))
        
        # Pause non-winning creatives
        for creative_id in all_creative_ids:
            if creative_id and creative_id != winning_creative_id:
                self.db.execute(
                    update(Creative)
                    .where(Creative.id == creative_id)
                    .values(status=CreativeStatus.ARCHIVED)
                )
        
        # Ensure winning creative is active
        self.db.execute(
            update(Creative)
            .where(Creative.id == winning_creative_id)
            .values(status=CreativeStatus.ACTIVE)
        )
    
    def check_stopping_rules(self, experiment_id: int) -> Dict[str, Any]:
        """
        Check if experiment should be stopped based on rules.
        
        Returns:
            Dict with should_stop, reason, and current metrics
        """
        experiment = self.db.get(Experiment, experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        result = self.analyze_experiment(experiment_id)
        stop_rules = experiment.stop_rules or {}
        
        should_stop = False
        reasons = []
        
        # Check significance
        if stop_rules.get("early_stop_on_significance", True):
            if result.is_significant:
                should_stop = True
                reasons.append(f"Statistical significance reached (p={result.p_value:.4f})")
        
        # Check max duration
        max_days = stop_rules.get("max_duration_days", 14)
        if result.days_running >= max_days:
            should_stop = True
            reasons.append(f"Maximum duration ({max_days} days) reached")
        
        # Check futility
        futility_threshold = stop_rules.get("futility_threshold", 0.1)
        if result.sample_size_sufficient and abs(result.lift) < experiment.mde / 3:
            if result.days_running > max_days / 2:
                should_stop = True
                reasons.append("Futility - unlikely to reach MDE")
        
        return {
            "should_stop": should_stop,
            "reasons": reasons,
            "days_running": result.days_running,
            "is_significant": result.is_significant,
            "current_lift": result.lift,
            "winner": result.winner
        }
    
    def get_active_experiments(self) -> List[Experiment]:
        """Get all running experiments."""
        return self.db.execute(
            select(Experiment).where(
                Experiment.status == ExperimentStatus.RUNNING
            )
        ).scalars().all()
    
    def run_experiment_checks(self) -> List[Dict[str, Any]]:
        """
        Run stopping rule checks on all active experiments.
        
        This should be called periodically (e.g., daily).
        
        Returns:
            List of experiments that should be stopped
        """
        active = self.get_active_experiments()
        should_stop = []
        
        for experiment in active:
            check = self.check_stopping_rules(experiment.id)
            if check["should_stop"]:
                should_stop.append({
                    "experiment_id": experiment.id,
                    "experiment_name": experiment.name,
                    **check
                })
        
        return should_stop

