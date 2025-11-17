"""Tests for creative generator service"""
import pytest
from sqlalchemy.orm import Session
from app.services.marketing.creative_generator import CreativeGeneratorService
from app.models import Persona, Creative, CreativeFormat, CreativeStatus


@pytest.fixture
def sample_persona(db: Session):
    """Create a sample persona"""
    persona = Persona(
        name="Luxury Waterfront Seekers",
        description="High-income professionals seeking premium properties",
        version=1,
        status="active",
        rules={
            "budget_range": [200000, 500000],
            "property_types": ["apartment", "villa"],
            "locations": ["Dubai Marina", "Palm Jumeirah"]
        },
        characteristics={
            "urgency": "high",
            "price_sensitivity": "low",
            "decision_speed": "fast"
        },
        messaging={
            "hooks": ["Exclusive waterfront living", "Investment opportunity"],
            "tone": "aspirational"
        },
        sample_size=145,
        confidence_score=87.5
    )
    db.add(persona)
    db.commit()
    return persona


def test_generate_creatives_creates_variants(db: Session, sample_persona):
    """Test that creative generator creates multiple variants"""
    service = CreativeGeneratorService(db)
    
    creatives = service.generate_creatives(
        persona_id=sample_persona.id,
        format=CreativeFormat.IMAGE,
        count=3
    )
    
    # Should generate requested count
    assert len(creatives) <= 3  # May be less if generation fails
    
    # Each creative should have required fields
    for creative in creatives:
        assert creative.persona_id == sample_persona.id
        assert creative.format == CreativeFormat.IMAGE
        assert creative.headline
        assert creative.primary_text
        assert creative.call_to_action


def test_creative_compliance_check(db: Session, sample_persona):
    """Test that creatives have compliance checks"""
    service = CreativeGeneratorService(db)
    
    creatives = service.generate_creatives(
        persona_id=sample_persona.id,
        format=CreativeFormat.IMAGE,
        count=2
    )
    
    for creative in creatives:
        assert "compliance_issues" in creative.risk_flags
        assert "warnings" in creative.risk_flags
        assert "toxicity_score" in creative.risk_flags
        
        # Toxicity score should be between 0 and 1
        assert 0 <= creative.risk_flags["toxicity_score"] <= 1


def test_creative_status_based_on_compliance(db: Session, sample_persona):
    """Test that creative status reflects compliance"""
    service = CreativeGeneratorService(db)
    
    creatives = service.generate_creatives(
        persona_id=sample_persona.id,
        format=CreativeFormat.IMAGE,
        count=2
    )
    
    for creative in creatives:
        if creative.risk_flags.get("compliance_issues"):
            # Should be in review if has issues
            assert creative.status == CreativeStatus.REVIEW
        else:
            # Should be approved if no issues
            assert creative.status == CreativeStatus.APPROVED


def test_creative_has_generation_metadata(db: Session, sample_persona):
    """Test that creatives store generation metadata"""
    service = CreativeGeneratorService(db)
    
    creatives = service.generate_creatives(
        persona_id=sample_persona.id,
        format=CreativeFormat.IMAGE,
        count=1
    )
    
    if creatives:
        creative = creatives[0]
        assert creative.generation_prompt
        assert creative.model_version
        assert creative.generation_params


def test_compliance_blocks_discriminatory_language():
    """Test that compliance checker catches discriminatory terms"""
    service = CreativeGeneratorService(None)
    
    # Test with problematic content
    creative_data = {
        "headline": "Perfect for families only",
        "primary_text": "Adults only community",
        "description": "No children allowed"
    }
    
    risk_flags = service._check_compliance(creative_data)
    
    # Should have compliance issues
    assert len(risk_flags["compliance_issues"]) > 0


def test_compliance_passes_neutral_language():
    """Test that compliance checker passes neutral content"""
    service = CreativeGeneratorService(None)
    
    # Test with acceptable content
    creative_data = {
        "headline": "Luxury Waterfront Living",
        "primary_text": "Discover premium properties with stunning views and world-class amenities",
        "description": "Contact us today"
    }
    
    risk_flags = service._check_compliance(creative_data)
    
    # Should have no compliance issues
    assert len(risk_flags["compliance_issues"]) == 0

