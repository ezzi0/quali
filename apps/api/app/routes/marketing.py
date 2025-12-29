"""Marketing API routes"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..deps import get_db
from ..auth import require_staff_user
from ..logging import get_logger
from ..models import Persona, Creative, Campaign, CreativeFormat, Experiment
from ..services.marketing.persona_discovery import PersonaDiscoveryService
from ..services.marketing.creative_generator import CreativeGeneratorService
from ..services.marketing.budget_optimizer import BudgetOptimizerService
from ..services.marketing.attribution import AttributionService
from ..services.marketing.platform_selector import PlatformSelectorService
from ..services.marketing.cross_platform_optimizer import CrossPlatformOptimizer
from ..services.marketing.learning_service import LearningService
from ..services.marketing.lead_persona_matcher import LeadPersonaMatcherService
from ..services.marketing.audience_sync import AudienceSyncService
from ..services.marketing.experiment_runner import ExperimentRunnerService
from ..agents.marketing_agent import MarketingAgent

logger = get_logger(__name__)

router = APIRouter()


# Request/Response models
class PersonaDiscoveryRequest(BaseModel):
    """Request for persona discovery"""
    min_cluster_size: int = 25
    method: str = "hdbscan"


class PersonaDiscoveryResponse(BaseModel):
    """Response for persona discovery"""
    personas: List[dict]
    count: int


class CreativeGenerationRequest(BaseModel):
    """Request for creative generation"""
    persona_id: int
    format: CreativeFormat
    count: int = 3
    property_context: Optional[dict] = None


class CreativeGenerationResponse(BaseModel):
    """Response for creative generation"""
    creatives: List[dict]
    count: int


class BudgetOptimizationRequest(BaseModel):
    """Request for budget optimization"""
    campaign_id: int
    lookback_days: int = 7
    volatility_cap: float = 0.20
    auto_apply: bool = False


class BudgetOptimizationResponse(BaseModel):
    """Response for budget optimization"""
    recommendations: List[dict]
    count: int
    applied: int


class AttributionRequest(BaseModel):
    """Request for attribution"""
    lead_id: int
    url: Optional[str] = None
    utm_params: Optional[dict] = None
    fbclid: Optional[str] = None
    gclid: Optional[str] = None


class PlatformSelectionRequest(BaseModel):
    """Request for platform selection"""
    persona_id: int
    total_budget: float
    objective: str = "lead_generation"


class CrossPlatformOptimizationRequest(BaseModel):
    """Request for cross-platform budget optimization"""
    persona_id: int
    total_budget: float
    lookback_days: int = 14
    platforms: Optional[List[str]] = None


class LeadMatchRequest(BaseModel):
    """Request for lead-to-persona matching"""
    lead_id: int
    auto_assign: bool = True
    min_score: float = 50.0


class LearningCycleRequest(BaseModel):
    """Request for running a learning cycle"""
    lookback_days: int = 7
    auto_apply: bool = False


class ExperimentCreateRequest(BaseModel):
    """Request to create an experiment"""
    name: str
    persona_id: int
    control_creative_id: int
    variant_creative_ids: List[int]
    hypothesis: str
    confidence_level: float = 0.95
    min_sample_size: int = 1000
    max_duration_days: int = 14


class FullWorkflowRequest(BaseModel):
    """Request for running the full marketing workflow"""
    total_budget: float
    platforms: Optional[List[str]] = None
    auto_deploy: bool = False
    run_learning: bool = True


# ===== Existing Endpoints =====

@router.post("/personas/discover", response_model=PersonaDiscoveryResponse)
async def discover_personas(
    request: PersonaDiscoveryRequest,
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """
    Discover marketing personas from lead data.
    
    Runs clustering analysis on qualified leads and generates
    persona profiles with LLM labeling.
    """
    try:
        service = PersonaDiscoveryService(db)
        personas = service.discover_personas(
            min_cluster_size=request.min_cluster_size,
            method=request.method
        )
        
        return PersonaDiscoveryResponse(
            personas=[
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "sample_size": p.sample_size,
                    "confidence_score": float(p.confidence_score) if p.confidence_score else 0,
                    "rules": p.rules,
                    "characteristics": p.characteristics,
                    "messaging": p.messaging
                }
                for p in personas
            ],
            count=len(personas)
        )
    
    except Exception as e:
        logger.error("persona_discovery_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/creatives/generate", response_model=CreativeGenerationResponse)
async def generate_creatives(
    request: CreativeGenerationRequest,
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """
    Generate ad creatives for a persona.
    
    Uses AI to create multiple creative variants with compliance checks.
    """
    try:
        service = CreativeGeneratorService(db)
        creatives = service.generate_creatives(
            persona_id=request.persona_id,
            format=request.format,
            count=request.count,
            property_context=request.property_context
        )
        
        return CreativeGenerationResponse(
            creatives=[
                {
                    "id": c.id,
                    "name": c.name,
                    "format": c.format.value,
                    "status": c.status.value,
                    "headline": c.headline,
                    "primary_text": c.primary_text,
                    "description": c.description,
                    "call_to_action": c.call_to_action,
                    "risk_flags": c.risk_flags
                }
                for c in creatives
            ],
            count=len(creatives)
        )
    
    except Exception as e:
        logger.error("creative_generation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/budget/optimize", response_model=BudgetOptimizationResponse)
async def optimize_budget(
    request: BudgetOptimizationRequest,
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """
    Optimize budget allocation across ad sets within a campaign.
    
    Uses Thompson Sampling to recommend budget changes based on performance.
    """
    try:
        service = BudgetOptimizerService(db)
        recommendations = service.optimize_campaign_budget(
            campaign_id=request.campaign_id,
            lookback_days=request.lookback_days,
            volatility_cap=request.volatility_cap
        )
        
        applied = 0
        if request.auto_apply and recommendations:
            applied = await service.apply_recommendations(
                recommendations,
                auto_approve=True,
                push_to_platform=True
            )
        
        return BudgetOptimizationResponse(
            recommendations=[
                {
                    "ad_set_id": r.ad_set_id,
                    "name": r.name,
                    "current_budget": r.current_budget,
                    "recommended_budget": r.recommended_budget,
                    "change_amount": r.change_amount,
                    "change_pct": r.change_pct,
                    "rationale": r.rationale,
                    "confidence": r.confidence
                }
                for r in recommendations
            ],
            count=len(recommendations),
            applied=applied
        )
    
    except Exception as e:
        logger.error("budget_optimization_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/attribution/track")
async def track_attribution(
    request: AttributionRequest,
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """
    Track attribution for a lead.
    
    Parses UTM parameters and platform click IDs to attribute leads
    to marketing campaigns.
    """
    try:
        service = AttributionService(db)
        
        # Parse attribution data
        attribution_data = service.parse_attribution(
            url=request.url,
            utm_params=request.utm_params,
            fbclid=request.fbclid,
            gclid=request.gclid
        )
        
        # Attribute to lead
        service.attribute_lead(request.lead_id, attribution_data)
        
        return {
            "success": True,
            "lead_id": request.lead_id,
            "attribution": attribution_data
        }
    
    except Exception as e:
        logger.error("attribution_tracking_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ===== New Endpoints: Platform Selection =====

@router.post("/platforms/select")
async def select_platforms(
    request: PlatformSelectionRequest,
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """
    Select optimal platforms for a persona.
    
    Analyzes historical performance and persona characteristics to
    recommend the best advertising platforms.
    """
    try:
        service = PlatformSelectorService(db)
        recommendation = service.select_platforms_for_persona(
            persona_id=request.persona_id,
            total_budget=request.total_budget,
            objective=request.objective
        )
        
        return {
            "persona_id": recommendation.persona_id,
            "persona_name": recommendation.persona_name,
            "primary_platform": recommendation.primary_platform,
            "strategy": recommendation.strategy,
            "platforms": [
                {
                    "platform": p.platform,
                    "score": p.score,
                    "confidence": p.confidence,
                    "recommended_budget_pct": p.recommended_budget_pct,
                    "rationale": p.rationale
                }
                for p in recommendation.platforms
            ]
        }
    
    except Exception as e:
        logger.error("platform_selection_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/platforms/performance")
async def get_platform_performance(
    lookback_days: int = 30,
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """Get aggregated performance summary for all platforms."""
    try:
        service = PlatformSelectorService(db)
        summary = service.get_platform_performance_summary(lookback_days)
        return {"platforms": summary, "lookback_days": lookback_days}
    except Exception as e:
        logger.error("platform_performance_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ===== New Endpoints: Cross-Platform Optimization =====

@router.post("/budget/optimize-cross-platform")
async def optimize_cross_platform_budget(
    request: CrossPlatformOptimizationRequest,
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """
    Optimize budget allocation across multiple platforms.
    
    Uses performance data to reallocate budget between platforms
    for optimal results.
    """
    try:
        service = CrossPlatformOptimizer(db)
        recommendation = service.optimize_cross_platform_budget(
            persona_id=request.persona_id,
            total_budget=request.total_budget,
            lookback_days=request.lookback_days,
            include_platforms=request.platforms
        )
        
        return {
            "persona_id": recommendation.persona_id,
            "persona_name": recommendation.persona_name,
            "total_budget": recommendation.total_budget,
            "strategy": recommendation.overall_strategy,
            "confidence": recommendation.confidence,
            "expected_improvement": recommendation.expected_improvement,
            "allocations": [
                {
                    "platform": a.platform,
                    "current_budget": a.current_budget,
                    "recommended_budget": a.recommended_budget,
                    "change_amount": a.change_amount,
                    "change_pct": a.change_pct,
                    "performance_score": a.performance_score,
                    "rationale": a.rationale
                }
                for a in recommendation.platform_allocations
            ]
        }
    
    except Exception as e:
        logger.error("cross_platform_optimization_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ===== New Endpoints: Lead Matching =====

@router.post("/leads/match")
async def match_lead_to_personas(
    request: LeadMatchRequest,
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """
    Match a lead to marketing personas.
    
    Analyzes lead profile to find best matching personas
    and optionally assigns the best match.
    """
    try:
        service = LeadPersonaMatcherService(db)
        matches = service.match_lead_to_personas(
            lead_id=request.lead_id,
            auto_assign=request.auto_assign,
            min_score=request.min_score
        )
        
        return {
            "lead_id": request.lead_id,
            "matches": [
                {
                    "persona_id": m.persona_id,
                    "persona_name": m.persona_name,
                    "match_score": m.match_score,
                    "confidence": m.confidence,
                    "is_strong_match": m.is_strong_match,
                    "match_factors": m.match_factors
                }
                for m in matches
            ],
            "count": len(matches),
            "assigned": matches[0].persona_id if matches and request.auto_assign and matches[0].is_strong_match else None
        }
    
    except Exception as e:
        logger.error("lead_matching_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leads/distribution")
async def get_lead_distribution(
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """Get distribution of leads across personas."""
    try:
        service = LeadPersonaMatcherService(db)
        distribution = service.get_persona_lead_distribution()
        return {"distribution": distribution}
    except Exception as e:
        logger.error("lead_distribution_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ===== New Endpoints: Learning =====

@router.post("/learning/run-cycle")
async def run_learning_cycle(
    request: LearningCycleRequest,
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """
    Run a learning and adaptation cycle.
    
    Analyzes campaign performance, identifies top/bottom performers,
    generates insights, and optionally applies optimizations.
    """
    try:
        service = LearningService(db)
        result = service.run_learning_cycle(
            lookback_days=request.lookback_days,
            auto_apply=request.auto_apply
        )
        
        return {
            "cycle_id": result.cycle_id,
            "timestamp": result.timestamp.isoformat(),
            "personas_analyzed": result.personas_analyzed,
            "creatives_analyzed": result.creatives_analyzed,
            "actions_taken": len(result.actions_taken),
            "improvements": result.improvements,
            "insights": [
                {
                    "persona_id": i.persona_id,
                    "persona_name": i.persona_name,
                    "conversion_rate": i.conversion_rate,
                    "avg_cpl": i.avg_cpl,
                    "best_platform": i.best_platform,
                    "recommended_adjustments": i.recommended_adjustments
                }
                for i in result.insights
            ]
        }
    
    except Exception as e:
        logger.error("learning_cycle_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/summary")
async def get_learning_summary(
    days: int = 30,
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """Get learning summary over a period."""
    try:
        service = LearningService(db)
        summary = service.get_learning_summary(days)
        return summary
    except Exception as e:
        logger.error("learning_summary_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ===== New Endpoints: Experiments =====

@router.post("/experiments/create")
async def create_experiment(
    request: ExperimentCreateRequest,
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """
    Create a new A/B test experiment.
    
    Tests multiple creative variants against a control to find winners.
    """
    try:
        service = ExperimentRunnerService(db)
        experiment = service.create_experiment(
            name=request.name,
            persona_id=request.persona_id,
            control_creative_id=request.control_creative_id,
            variant_creative_ids=request.variant_creative_ids,
            hypothesis=request.hypothesis,
            confidence_level=request.confidence_level,
            min_sample_size=request.min_sample_size,
            max_duration_days=request.max_duration_days
        )
        
        return {
            "experiment_id": experiment.id,
            "name": experiment.name,
            "status": experiment.status.value,
            "created_at": experiment.created_at.isoformat()
        }
    
    except Exception as e:
        logger.error("experiment_creation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/experiments/{experiment_id}/start")
async def start_experiment(
    experiment_id: int,
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """Start a draft experiment."""
    try:
        service = ExperimentRunnerService(db)
        experiment = service.start_experiment(experiment_id)
        return {
            "experiment_id": experiment.id,
            "status": experiment.status.value,
            "start_date": experiment.start_date.isoformat() if experiment.start_date else None
        }
    except Exception as e:
        logger.error("experiment_start_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiments/{experiment_id}/analyze")
async def analyze_experiment(
    experiment_id: int,
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """Analyze a running or completed experiment."""
    try:
        service = ExperimentRunnerService(db)
        result = service.analyze_experiment(experiment_id)
        
        return {
            "experiment_id": result.experiment_id,
            "experiment_name": result.experiment_name,
            "status": result.status,
            "days_running": result.days_running,
            "winner": result.winner,
            "lift": result.lift,
            "p_value": result.p_value,
            "is_significant": result.is_significant,
            "sample_size_sufficient": result.sample_size_sufficient,
            "recommendation": result.recommendation,
            "control": {
                "variant_name": result.control.variant_name,
                "impressions": result.control.impressions,
                "leads": result.control.leads,
                "conversions": result.control.conversions,
                "cvr": result.control.cvr
            },
            "variants": [
                {
                    "variant_name": v.variant_name,
                    "impressions": v.impressions,
                    "leads": v.leads,
                    "conversions": v.conversions,
                    "cvr": v.cvr
                }
                for v in result.variants
            ]
        }
    
    except Exception as e:
        logger.error("experiment_analysis_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/experiments/{experiment_id}/complete")
async def complete_experiment(
    experiment_id: int,
    apply_winner: bool = False,
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """Complete an experiment and optionally apply the winner."""
    try:
        service = ExperimentRunnerService(db)
        experiment = service.complete_experiment(experiment_id, apply_winner)
        return {
            "experiment_id": experiment.id,
            "status": experiment.status.value,
            "results": experiment.results
        }
    except Exception as e:
        logger.error("experiment_completion_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiments")
async def list_experiments(
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """List all experiments."""
    from sqlalchemy import select
    
    query = select(Experiment)
    if status:
        query = query.where(Experiment.status == status)
    query = query.limit(limit).order_by(Experiment.created_at.desc())
    
    experiments = db.execute(query).scalars().all()
    
    return {
        "experiments": [
            {
                "id": e.id,
                "name": e.name,
                "status": e.status.value,
                "hypothesis": e.hypothesis,
                "start_date": e.start_date.isoformat() if e.start_date else None,
                "stop_date": e.stop_date.isoformat() if e.stop_date else None
            }
            for e in experiments
        ]
    }


# ===== New Endpoints: Full Workflow =====

@router.post("/workflow/run")
async def run_full_workflow(
    request: FullWorkflowRequest,
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """
    Run the complete marketing workflow.
    
    Discovers personas, generates creatives, selects platforms,
    deploys campaigns, and runs learning cycles.
    """
    try:
        agent = MarketingAgent(db, dry_run=not request.auto_deploy)
        result = await agent.run_full_workflow(
            total_budget=request.total_budget,
            platforms=request.platforms,
            auto_deploy=request.auto_deploy,
            run_learning=request.run_learning
        )
        return result
    
    except Exception as e:
        logger.error("full_workflow_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_marketing_dashboard(
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """
    Get comprehensive marketing dashboard data.
    
    Returns summary metrics, platform performance, learning insights,
    and lead distribution.
    """
    try:
        agent = MarketingAgent(db, dry_run=True)
        return agent.get_marketing_dashboard()
    except Exception as e:
        logger.error("dashboard_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ===== Existing List Endpoints =====

@router.get("/personas")
async def list_personas(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """List all personas"""
    from sqlalchemy import select
    
    query = select(Persona)
    
    if status:
        query = query.where(Persona.status == status)
    
    query = query.limit(limit).offset(offset).order_by(Persona.created_at.desc())
    
    personas = db.execute(query).scalars().all()
    
    return {
        "personas": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "status": p.status.value,
                "sample_size": p.sample_size,
                "confidence_score": float(p.confidence_score) if p.confidence_score else 0,
                "created_at": p.created_at.isoformat()
            }
            for p in personas
        ],
        "total": len(personas),
        "limit": limit,
        "offset": offset
    }


@router.get("/campaigns")
async def list_campaigns(
    status: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """List all campaigns"""
    from sqlalchemy import select
    
    query = select(Campaign)
    
    if status:
        query = query.where(Campaign.status == status)
    if platform:
        query = query.where(Campaign.platform == platform)
    
    query = query.limit(limit).offset(offset).order_by(Campaign.created_at.desc())
    
    campaigns = db.execute(query).scalars().all()
    
    return {
        "campaigns": [
            {
                "id": c.id,
                "name": c.name,
                "platform": c.platform.value,
                "objective": c.objective.value,
                "status": c.status.value,
                "budget_total": float(c.budget_total) if c.budget_total else None,
                "budget_daily": float(c.budget_daily) if c.budget_daily else None,
                "spend_total": float(c.spend_total),
                "created_at": c.created_at.isoformat()
            }
            for c in campaigns
        ],
        "total": len(campaigns),
        "limit": limit,
        "offset": offset
    }


@router.get("/creatives")
async def list_creatives(
    persona_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """List all creatives"""
    from sqlalchemy import select
    
    query = select(Creative)
    
    if persona_id:
        query = query.where(Creative.persona_id == persona_id)
    if status:
        query = query.where(Creative.status == status)
    
    query = query.limit(limit).offset(offset).order_by(Creative.created_at.desc())
    
    creatives = db.execute(query).scalars().all()
    
    return {
        "creatives": [
            {
                "id": c.id,
                "name": c.name,
                "format": c.format.value,
                "status": c.status.value,
                "persona_id": c.persona_id,
                "headline": c.headline,
                "risk_flags": c.risk_flags,
                "created_at": c.created_at.isoformat()
            }
            for c in creatives
        ],
        "total": len(creatives),
        "limit": limit,
        "offset": offset
    }
