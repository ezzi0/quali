"""Tests for budget optimizer service"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.services.marketing.budget_optimizer import BudgetOptimizerService, AdSetPerformance
from app.models import Campaign, AdSet, MarketingMetric, CampaignPlatform, CampaignObjective


@pytest.fixture
def sample_campaign_with_adsets(db: Session):
    """Create a campaign with ad sets and performance data"""
    # Create campaign
    campaign = Campaign(
        name="Test Campaign",
        platform=CampaignPlatform.META,
        objective=CampaignObjective.LEAD_GENERATION,
        status="active",
        budget_daily=100.0
    )
    db.add(campaign)
    db.flush()
    
    # Create ad sets with different performance
    # High performer
    adset1 = AdSet(
        campaign_id=campaign.id,
        name="High Performer",
        status="active",
        budget_daily=40.0
    )
    db.add(adset1)
    db.flush()
    
    # Add metrics for high performer
    for i in range(7):
        metric = MarketingMetric(
            date=(datetime.utcnow() - timedelta(days=i)).date(),
            campaign_id=campaign.id,
            ad_set_id=adset1.id,
            platform="meta",
            channel="facebook",
            impressions=1000,
            clicks=80,
            spend=40.0,
            leads=10,
            closed_won=2
        )
        db.add(metric)
    
    # Low performer
    adset2 = AdSet(
        campaign_id=campaign.id,
        name="Low Performer",
        status="active",
        budget_daily=60.0
    )
    db.add(adset2)
    db.flush()
    
    # Add metrics for low performer
    for i in range(7):
        metric = MarketingMetric(
            date=(datetime.utcnow() - timedelta(days=i)).date(),
            campaign_id=campaign.id,
            ad_set_id=adset2.id,
            platform="meta",
            channel="facebook",
            impressions=1000,
            clicks=30,
            spend=60.0,
            leads=2,
            closed_won=0
        )
        db.add(metric)
    
    db.commit()
    return campaign


def test_budget_optimizer_generates_recommendations(db: Session, sample_campaign_with_adsets):
    """Test that optimizer generates budget recommendations"""
    service = BudgetOptimizerService(db)
    
    recommendations = service.optimize_campaign_budget(
        campaign_id=sample_campaign_with_adsets.id,
        lookback_days=7
    )
    
    # Should generate recommendations
    assert len(recommendations) > 0
    
    # Each recommendation should have required fields
    for rec in recommendations:
        assert rec.ad_set_id
        assert rec.name
        assert rec.current_budget > 0
        assert rec.recommended_budget > 0
        assert rec.rationale
        assert 0 <= rec.confidence <= 1


def test_budget_shifts_from_low_to_high_performer(db: Session, sample_campaign_with_adsets):
    """Test that budget shifts from low to high performer"""
    service = BudgetOptimizerService(db)
    
    recommendations = service.optimize_campaign_budget(
        campaign_id=sample_campaign_with_adsets.id,
        lookback_days=7
    )
    
    # Find recommendations for each ad set
    high_perf_rec = next((r for r in recommendations if "High Performer" in r.name), None)
    low_perf_rec = next((r for r in recommendations if "Low Performer" in r.name), None)
    
    if high_perf_rec and low_perf_rec:
        # High performer should get budget increase
        assert high_perf_rec.change_amount > 0
        
        # Low performer should get budget decrease
        assert low_perf_rec.change_amount < 0


def test_volatility_cap_limits_changes(db: Session, sample_campaign_with_adsets):
    """Test that volatility cap limits budget changes"""
    service = BudgetOptimizerService(db)
    
    recommendations = service.optimize_campaign_budget(
        campaign_id=sample_campaign_with_adsets.id,
        lookback_days=7,
        volatility_cap=0.10  # Max 10% change
    )
    
    for rec in recommendations:
        # Change should not exceed volatility cap
        assert abs(rec.change_pct) <= 0.10


def test_thompson_sampling_allocates_budget():
    """Test Thompson Sampling allocation logic"""
    service = BudgetOptimizerService(None)
    
    # Create performance data
    perf_data = [
        AdSetPerformance(
            ad_set_id=1,
            name="High CVR",
            impressions=1000,
            clicks=100,
            spend=50.0,
            leads=20,
            conversions=5,  # 25% CVR
            budget_current=50.0,
            budget_floor=25.0,
            budget_ceiling=100.0
        ),
        AdSetPerformance(
            ad_set_id=2,
            name="Low CVR",
            impressions=1000,
            clicks=100,
            spend=50.0,
            leads=20,
            conversions=1,  # 5% CVR
            budget_current=50.0,
            budget_floor=25.0,
            budget_ceiling=100.0
        ),
    ]
    
    allocations = service._thompson_sampling(perf_data, total_budget=100.0)
    
    # High CVR should get more budget
    assert allocations[1] > allocations[2]
    
    # Total should equal budget
    assert abs(sum(allocations.values()) - 100.0) < 1.0


def test_apply_recommendations_updates_budgets(db: Session, sample_campaign_with_adsets):
    """Test that applying recommendations updates ad set budgets"""
    service = BudgetOptimizerService(db)
    
    recommendations = service.optimize_campaign_budget(
        campaign_id=sample_campaign_with_adsets.id,
        lookback_days=7
    )
    
    if recommendations:
        # Store original budgets
        original_budgets = {}
        for rec in recommendations:
            adset = db.get(AdSet, rec.ad_set_id)
            original_budgets[rec.ad_set_id] = float(adset.budget_daily)
        
        # Apply recommendations
        updated = service.apply_recommendations(recommendations, auto_approve=True)
        
        assert updated > 0
        
        # Verify budgets changed
        for rec in recommendations:
            adset = db.get(AdSet, rec.ad_set_id)
            assert float(adset.budget_daily) != original_budgets[rec.ad_set_id]
            assert float(adset.budget_daily) == rec.recommended_budget

