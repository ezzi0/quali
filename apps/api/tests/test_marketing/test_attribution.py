"""Tests for attribution service"""
import pytest
from sqlalchemy.orm import Session
from app.services.marketing.attribution import AttributionService
from app.models import Lead, Contact, Campaign, AdSet, Ad, LeadSource


@pytest.fixture
def sample_campaign_structure(db: Session):
    """Create campaign structure for attribution testing"""
    campaign = Campaign(
        name="Test Campaign",
        platform="meta",
        objective="lead_generation",
        status="active",
        platform_campaign_id="123456789"
    )
    db.add(campaign)
    db.flush()
    
    ad_set = AdSet(
        campaign_id=campaign.id,
        name="Test Ad Set",
        status="active",
        budget_daily=50.0,
        platform_adset_id="987654321"
    )
    db.add(ad_set)
    db.flush()
    
    from app.models import Creative, CreativeFormat
    creative = Creative(
        name="Test Creative",
        format=CreativeFormat.IMAGE,
        status="approved",
        headline="Test Headline",
        primary_text="Test Text"
    )
    db.add(creative)
    db.flush()
    
    ad = Ad(
        ad_set_id=ad_set.id,
        creative_id=creative.id,
        name="Test Ad",
        status="active",
        platform_ad_id="111222333"
    )
    db.add(ad)
    db.flush()
    
    db.commit()
    return {"campaign": campaign, "ad_set": ad_set, "ad": ad}


def test_parse_attribution_from_url():
    """Test parsing attribution from URL"""
    service = AttributionService(None)
    
    url = "https://example.com/landing?utm_source=facebook&utm_medium=cpc&utm_campaign=summer&utm_id=123&fbclid=abc123"
    
    attribution = service.parse_attribution(url=url)
    
    assert attribution["source"] == "facebook"
    assert attribution["medium"] == "cpc"
    assert attribution["campaign"] == "summer"
    assert attribution["campaign_id"] == "123"
    assert attribution["platform"] == "meta"
    assert attribution["click_id"] == "abc123"


def test_parse_attribution_google():
    """Test parsing Google Ads attribution"""
    service = AttributionService(None)
    
    url = "https://example.com?utm_source=google&utm_medium=cpc&gclid=xyz789"
    
    attribution = service.parse_attribution(url=url)
    
    assert attribution["source"] == "google"
    assert attribution["platform"] == "google"
    assert attribution["click_id"] == "xyz789"


def test_attribute_lead_stores_data(db: Session):
    """Test that attributing a lead stores data"""
    # Create lead
    contact = Contact(name="Test User", email="test@example.com")
    db.add(contact)
    db.flush()
    
    lead = Lead(
        source=LeadSource.WEB,
        status="new",
        contact_id=contact.id
    )
    db.add(lead)
    db.commit()
    
    # Attribute lead
    service = AttributionService(db)
    attribution_data = {
        "source": "facebook",
        "medium": "cpc",
        "campaign": "test",
        "platform": "meta",
        "click_id": "abc123"
    }
    
    service.attribute_lead(lead.id, attribution_data)
    
    # Verify attribution stored
    db.refresh(lead)
    assert lead.attribution_data is not None
    assert lead.attribution_data["source"] == "facebook"
    assert lead.attribution_data["platform"] == "meta"


def test_attribute_lead_links_to_campaign(db: Session, sample_campaign_structure):
    """Test that attribution links to internal campaign"""
    # Create lead
    contact = Contact(name="Test User", email="test@example.com")
    db.add(contact)
    db.flush()
    
    lead = Lead(
        source=LeadSource.WEB,
        status="new",
        contact_id=contact.id
    )
    db.add(lead)
    db.commit()
    
    # Attribute with platform IDs
    service = AttributionService(db)
    attribution_data = {
        "campaign_id": "123456789",
        "ad_set_id": "987654321",
        "ad_id": "111222333",
        "platform": "meta"
    }
    
    service.attribute_lead(lead.id, attribution_data)
    
    # Verify internal IDs linked
    db.refresh(lead)
    assert lead.attribution_data["internal_campaign_id"] == sample_campaign_structure["campaign"].id
    assert lead.attribution_data["internal_ad_set_id"] == sample_campaign_structure["ad_set"].id
    assert lead.attribution_data["internal_ad_id"] == sample_campaign_structure["ad"].id


def test_prepare_offline_conversions_meta(db: Session):
    """Test preparing Meta offline conversions"""
    # Create lead with attribution and contact
    contact = Contact(
        name="John Doe",
        email="john@example.com",
        phone="+971501234567"
    )
    db.add(contact)
    db.flush()
    
    lead = Lead(
        source=LeadSource.WEB,
        status="qualified",
        contact_id=contact.id,
        attribution_data={
            "platform": "meta",
            "click_id": "fbclid123",
            "fbp": "fb.1.123456789.987654321"
        }
    )
    db.add(lead)
    
    from app.models import LeadProfile
    profile = LeadProfile(
        lead_id=lead.id,
        city="Dubai",
        budget_max=250000
    )
    db.add(profile)
    db.commit()
    
    # Prepare conversions
    service = AttributionService(db)
    conversions = service.prepare_offline_conversions(platform="meta")
    
    assert len(conversions) > 0
    
    conversion = conversions[0]
    assert conversion["event_name"] == "Lead"
    assert conversion["user_data"]["em"] == "john@example.com"
    assert conversion["user_data"]["ph"] == "+971501234567"
    assert conversion["custom_data"]["value"] == 250000


def test_prepare_offline_conversions_filters_platform(db: Session):
    """Test that offline conversions filter by platform"""
    # Create leads from different platforms
    for platform in ["meta", "google", "tiktok"]:
        contact = Contact(name=f"User {platform}")
        db.add(contact)
        db.flush()
        
        lead = Lead(
            source=LeadSource.WEB,
            contact_id=contact.id,
            attribution_data={
                "platform": platform,
                "click_id": f"click_{platform}"
            }
        )
        db.add(lead)
    
    db.commit()
    
    # Get only Meta conversions
    service = AttributionService(db)
    meta_conversions = service.prepare_offline_conversions(platform="meta")
    
    # Should only have Meta conversion
    assert len(meta_conversions) == 1

