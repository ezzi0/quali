"""
End-to-End Marketing Flow Test

Tests the complete marketing workflow:
1. Discover personas from leads
2. Generate creatives
3. (Mock) Deploy campaigns
4. Track attribution
5. Optimize budgets
"""
import pytest
from sqlalchemy.orm import Session
from app.services.marketing.persona_discovery import PersonaDiscoveryService
from app.services.marketing.creative_generator import CreativeGeneratorService
from app.services.marketing.budget_optimizer import BudgetOptimizerService
from app.services.marketing.attribution import AttributionService
from app.models import (
    Lead, LeadProfile, Qualification, Contact,
    Campaign, AdSet, Ad, MarketingMetric, Creative,
    LeadSource, LeadStatus, CreativeFormat
)
from datetime import datetime, timedelta


@pytest.fixture
def complete_lead_dataset(db: Session):
    """Create a complete dataset of leads for E2E testing"""
    leads = []
    
    # Create 60 qualified leads across 2 segments
    for segment_id, (budget_range, areas, urgency) in enumerate([
        ([150000, 300000], ["Dubai Marina", "Downtown"], True),
        ([50000, 100000], ["JVC", "Sports City"], False),
    ]):
        for i in range(30):
            contact = Contact(
                name=f"User {segment_id}-{i}",
                email=f"user{segment_id}_{i}@example.com",
                phone=f"+97150{segment_id}{i:04d}"
            )
            db.add(contact)
            db.flush()
            
            lead = Lead(
                source=LeadSource.LEAD_AD if segment_id == 0 else LeadSource.WEB,
                status=LeadStatus.QUALIFIED,
                contact_id=contact.id
            )
            db.add(lead)
            db.flush()
            
            profile = LeadProfile(
                lead_id=lead.id,
                city="Dubai",
                areas=areas,
                property_type="apartment",
                beds=2 if segment_id == 0 else 1,
                budget_min=budget_range[0],
                budget_max=budget_range[1],
                move_in_date="immediately" if urgency else "3 months",
                preapproved=urgency
            )
            db.add(profile)
            
            qualification = Qualification(
                lead_id=lead.id,
                score=85 if urgency else 65,
                qualified=True,
                reasons=["Good fit"],
                missing_info=[],
                suggested_next_step="Follow up"
            )
            db.add(qualification)
            
            leads.append(lead)
    
    db.commit()
    return leads


def test_e2e_marketing_workflow(db: Session, complete_lead_dataset):
    """
    Test complete marketing workflow from persona discovery to optimization.
    """
    
    # STEP 1: Discover Personas
    print("\n=== STEP 1: Discover Personas ===")
    persona_service = PersonaDiscoveryService(db)
    personas = persona_service.discover_personas(
        min_cluster_size=20,
        method="kmeans"
    )
    
    assert len(personas) >= 2, "Should discover at least 2 personas"
    print(f"✓ Discovered {len(personas)} personas")
    
    for persona in personas:
        print(f"  - {persona.name}: {persona.sample_size} leads, confidence {persona.confidence_score}%")
    
    # STEP 2: Generate Creatives
    print("\n=== STEP 2: Generate Creatives ===")
    creative_service = CreativeGeneratorService(db)
    all_creatives = []
    
    for persona in personas[:2]:  # Top 2 personas
        creatives = creative_service.generate_creatives(
            persona_id=persona.id,
            format=CreativeFormat.IMAGE,
            count=2
        )
        all_creatives.extend(creatives)
        print(f"✓ Generated {len(creatives)} creatives for {persona.name}")
    
    assert len(all_creatives) > 0, "Should generate creatives"
    
    # Verify compliance checks
    for creative in all_creatives:
        assert "compliance_issues" in creative.risk_flags
        print(f"  - {creative.headline[:50]}... [Status: {creative.status.value}]")
    
    # STEP 3: Create Mock Campaign Structure
    print("\n=== STEP 3: Create Campaign Structure ===")
    
    campaign = Campaign(
        name="E2E Test Campaign",
        platform="meta",
        objective="lead_generation",
        status="active",
        budget_daily=100.0,
        platform_campaign_id="test_campaign_123"
    )
    db.add(campaign)
    db.flush()
    print(f"✓ Created campaign: {campaign.name}")
    
    # Create ad sets for each persona
    ad_sets = []
    for persona in personas[:2]:
        ad_set = AdSet(
            campaign_id=campaign.id,
            name=f"AdSet - {persona.name}",
            status="active",
            budget_daily=50.0,
            platform_adset_id=f"test_adset_{persona.id}"
        )
        db.add(ad_set)
        db.flush()
        ad_sets.append(ad_set)
        print(f"✓ Created ad set: {ad_set.name}")
    
    # Create ads
    ads_list = []
    for ad_set, creative in zip(ad_sets, all_creatives[:2]):
        ad = Ad(
            ad_set_id=ad_set.id,
            creative_id=creative.id,
            name=f"Ad - {creative.headline[:30]}",
            status="active",
            platform_ad_id=f"test_ad_{ad_set.id}",
            tracking_params={
                "utm_campaign": str(campaign.id),
                "utm_adset": str(ad_set.id)
            }
        )
        db.add(ad)
        db.flush()
        ads_list.append(ad)
        print(f"✓ Created ad: {ad.name}")
    
    db.commit()
    
    # STEP 4: Simulate Performance Data
    print("\n=== STEP 4: Simulate Performance Data ===")
    
    # Ad set 1: High performer
    for i in range(7):
        metric = MarketingMetric(
            date=(datetime.utcnow() - timedelta(days=i)).date(),
            campaign_id=campaign.id,
            ad_set_id=ad_sets[0].id,
            platform="meta",
            channel="facebook",
            impressions=1000,
            clicks=80,
            spend=50.0,
            leads=10,
            closed_won=2
        )
        db.add(metric)
    
    # Ad set 2: Low performer
    for i in range(7):
        metric = MarketingMetric(
            date=(datetime.utcnow() - timedelta(days=i)).date(),
            campaign_id=campaign.id,
            ad_set_id=ad_sets[1].id,
            platform="meta",
            channel="facebook",
            impressions=1000,
            clicks=30,
            spend=50.0,
            leads=2,
            closed_won=0
        )
        db.add(metric)
    
    db.commit()
    print("✓ Added 7 days of performance data")
    
    # STEP 5: Test Attribution
    print("\n=== STEP 5: Test Attribution ===")
    
    attribution_service = AttributionService(db)
    
    # Attribute a lead to our campaign
    test_lead = complete_lead_dataset[0]
    attribution_data = attribution_service.parse_attribution(
        url=f"https://example.com?utm_campaign={campaign.platform_campaign_id}&utm_adset={ad_sets[0].platform_adset_id}&fbclid=test123"
    )
    
    attribution_service.attribute_lead(test_lead.id, attribution_data)
    
    db.refresh(test_lead)
    assert test_lead.attribution_data is not None
    assert test_lead.attribution_data["internal_campaign_id"] == campaign.id
    print(f"✓ Attributed lead {test_lead.id} to campaign {campaign.id}")
    
    # STEP 6: Budget Optimization
    print("\n=== STEP 6: Budget Optimization ===")
    
    budget_service = BudgetOptimizerService(db)
    recommendations = budget_service.optimize_campaign_budget(
        campaign_id=campaign.id,
        lookback_days=7
    )
    
    assert len(recommendations) > 0, "Should generate budget recommendations"
    print(f"✓ Generated {len(recommendations)} budget recommendations")
    
    for rec in recommendations:
        change_dir = "increase" if rec.change_amount > 0 else "decrease"
        print(f"  - {rec.name}: {change_dir} by ${abs(rec.change_amount):.2f} ({abs(rec.change_pct)*100:.1f}%)")
        print(f"    Rationale: {rec.rationale}")
        print(f"    Confidence: {rec.confidence*100:.0f}%")
    
    # Verify high performer gets more budget
    high_perf_rec = next((r for r in recommendations if r.ad_set_id == ad_sets[0].id), None)
    if high_perf_rec:
        assert high_perf_rec.change_amount > 0, "High performer should get budget increase"
        print("✓ Budget optimizer correctly favors high performer")
    
    # STEP 7: Apply Budget Changes
    print("\n=== STEP 7: Apply Budget Changes ===")
    
    updated_count = budget_service.apply_recommendations(recommendations, auto_approve=True)
    assert updated_count > 0, "Should update ad set budgets"
    print(f"✓ Applied {updated_count} budget changes")
    
    # Verify changes persisted
    for rec in recommendations:
        ad_set = db.get(AdSet, rec.ad_set_id)
        assert float(ad_set.budget_daily) == rec.recommended_budget
    
    print("\n=== E2E TEST COMPLETE ===")
    print("✓ All steps passed successfully!")
    print(f"  - Personas discovered: {len(personas)}")
    print(f"  - Creatives generated: {len(all_creatives)}")
    print(f"  - Campaigns created: 1")
    print(f"  - Ad sets created: {len(ad_sets)}")
    print(f"  - Ads created: {len(ads_list)}")
    print(f"  - Leads attributed: 1")
    print(f"  - Budget recommendations: {len(recommendations)}")
    print(f"  - Budget changes applied: {updated_count}")

