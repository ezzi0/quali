"""Marketing API routes"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..deps import get_db
from ..auth import verify_optional_secret
from ..logging import get_logger
from ..models import Persona, Creative, Campaign, CreativeFormat
from ..services.marketing.persona_discovery import PersonaDiscoveryService
from ..services.marketing.creative_generator import CreativeGeneratorService
from ..services.marketing.budget_optimizer import BudgetOptimizerService
from ..services.marketing.attribution import AttributionService

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


@router.post("/personas/discover", response_model=PersonaDiscoveryResponse)
async def discover_personas(
    request: PersonaDiscoveryRequest,
    db: Session = Depends(get_db),
    _auth: None = Depends(verify_optional_secret),
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
    _auth: None = Depends(verify_optional_secret),
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
    _auth: None = Depends(verify_optional_secret),
):
    """
    Optimize budget allocation across ad sets.
    
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
            applied = service.apply_recommendations(recommendations, auto_approve=True)
        
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
    _auth: None = Depends(verify_optional_secret),
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


@router.get("/personas")
async def list_personas(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _auth: None = Depends(verify_optional_secret),
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
    _auth: None = Depends(verify_optional_secret),
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
    _auth: None = Depends(verify_optional_secret),
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

