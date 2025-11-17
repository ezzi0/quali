"""Tests for persona discovery service"""
import pytest
from sqlalchemy.orm import Session
from app.services.marketing.persona_discovery import PersonaDiscoveryService
from app.models import Lead, LeadProfile, Qualification, Contact, LeadSource, LeadStatus


@pytest.fixture
def sample_leads(db: Session):
    """Create sample leads for clustering"""
    leads = []
    
    # High-value buyers (Cluster 1)
    for i in range(30):
        contact = Contact(
            name=f"High Value Buyer {i}",
            email=f"hvb{i}@example.com",
            phone=f"+971500000{i:03d}"
        )
        db.add(contact)
        db.flush()
        
        lead = Lead(
            source=LeadSource.WEB,
            status=LeadStatus.QUALIFIED,
            contact_id=contact.id
        )
        db.add(lead)
        db.flush()
        
        profile = LeadProfile(
            lead_id=lead.id,
            city="Dubai",
            areas=["Dubai Marina", "Downtown"],
            property_type="apartment",
            beds=2,
            budget_min=150000,
            budget_max=300000,
            move_in_date="immediately",
            preapproved=True
        )
        db.add(profile)
        
        qualification = Qualification(
            lead_id=lead.id,
            score=85,
            qualified=True,
            reasons=["High budget", "Pre-approved", "Urgent"],
            missing_info=[],
            suggested_next_step="Schedule viewing"
        )
        db.add(qualification)
        
        leads.append(lead)
    
    # First-time buyers (Cluster 2)
    for i in range(30):
        contact = Contact(
            name=f"First Time Buyer {i}",
            email=f"ftb{i}@example.com",
            phone=f"+971510000{i:03d}"
        )
        db.add(contact)
        db.flush()
        
        lead = Lead(
            source=LeadSource.LEAD_AD,
            status=LeadStatus.QUALIFIED,
            contact_id=contact.id
        )
        db.add(lead)
        db.flush()
        
        profile = LeadProfile(
            lead_id=lead.id,
            city="Dubai",
            areas=["Jumeirah Village", "Dubai Sports City"],
            property_type="apartment",
            beds=1,
            budget_min=50000,
            budget_max=100000,
            move_in_date="3 months",
            preapproved=False
        )
        db.add(profile)
        
        qualification = Qualification(
            lead_id=lead.id,
            score=65,
            qualified=True,
            reasons=["Good budget fit", "Realistic timeline"],
            missing_info=["financing"],
            suggested_next_step="Discuss mortgage options"
        )
        db.add(qualification)
        
        leads.append(lead)
    
    db.commit()
    return leads


def test_persona_discovery_finds_clusters(db: Session, sample_leads):
    """Test that persona discovery identifies distinct clusters"""
    service = PersonaDiscoveryService(db)
    
    personas = service.discover_personas(
        min_cluster_size=20,
        min_samples=5,
        method="kmeans"  # Use kmeans for deterministic results
    )
    
    # Should find at least 2 personas
    assert len(personas) >= 2
    
    # Each persona should have required fields
    for persona in personas:
        assert persona.name
        assert persona.description
        assert persona.sample_size >= 20
        assert persona.rules
        assert persona.characteristics
        assert persona.messaging


def test_persona_has_budget_range(db: Session, sample_leads):
    """Test that personas have budget range rules"""
    service = PersonaDiscoveryService(db)
    personas = service.discover_personas(min_cluster_size=20, method="kmeans")
    
    for persona in personas:
        assert "budget_range" in persona.rules
        assert len(persona.rules["budget_range"]) == 2
        assert persona.rules["budget_range"][0] < persona.rules["budget_range"][1]


def test_persona_has_characteristics(db: Session, sample_leads):
    """Test that personas have behavioral characteristics"""
    service = PersonaDiscoveryService(db)
    personas = service.discover_personas(min_cluster_size=20, method="kmeans")
    
    for persona in personas:
        assert "urgency" in persona.characteristics
        assert persona.characteristics["urgency"] in ["high", "medium", "low"]
        
        assert "price_sensitivity" in persona.characteristics
        assert persona.characteristics["price_sensitivity"] in ["high", "medium", "low"]


def test_persona_has_messaging(db: Session, sample_leads):
    """Test that personas have messaging hooks"""
    service = PersonaDiscoveryService(db)
    personas = service.discover_personas(min_cluster_size=20, method="kmeans")
    
    for persona in personas:
        assert "hooks" in persona.messaging
        assert len(persona.messaging["hooks"]) > 0
        assert "tone" in persona.messaging


def test_persona_confidence_score(db: Session, sample_leads):
    """Test that confidence score reflects sample size"""
    service = PersonaDiscoveryService(db)
    personas = service.discover_personas(min_cluster_size=20, method="kmeans")
    
    for persona in personas:
        assert persona.confidence_score > 0
        # Larger samples should have higher confidence
        if persona.sample_size > 25:
            assert persona.confidence_score > 10


def test_insufficient_data_returns_empty(db: Session):
    """Test that insufficient data returns no personas"""
    # Create only 5 leads (below minimum)
    for i in range(5):
        contact = Contact(name=f"Test {i}", email=f"test{i}@example.com")
        db.add(contact)
        db.flush()
        
        lead = Lead(source=LeadSource.WEB, status=LeadStatus.NEW, contact_id=contact.id)
        db.add(lead)
    
    db.commit()
    
    service = PersonaDiscoveryService(db)
    personas = service.discover_personas(min_cluster_size=25)
    
    assert len(personas) == 0

