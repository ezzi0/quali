"""Test lead scoring logic"""
import pytest
from app.services.scoring import LeadScorer


def test_score_high_quality_lead():
    """Test scoring for a high-quality lead"""
    scorer = LeadScorer()

    profile = {
        "city": "Dubai",
        "areas": ["Dubai Marina", "JBR"],
        "property_type": "apartment",
        "beds": 2,
        "min_size_m2": 100,
        "budget_min": 100000,
        "budget_max": 200000,
        "move_in_date": "immediate",
        "preapproved": True,
    }

    top_matches = [
        {"price": 150000, "location": "Dubai Marina"},
        {"price": 160000, "location": "JBR"},
        {"price": 140000, "location": "Dubai Marina"},
    ]

    contact = {
        "email": "test@example.com",
        "phone": "+971501234567",
    }

    score, reasons = scorer.score_lead(profile, top_matches, contact)

    assert score >= 60, f"High-quality lead should score >= 60, got {score}"
    assert len(reasons) > 0, "Should provide reasons"


def test_score_low_quality_lead():
    """Test scoring for a low-quality lead"""
    scorer = LeadScorer()

    profile = {
        "budget_min": 50000,
        "budget_max": 60000,
    }

    top_matches = []

    contact = {}

    score, reasons = scorer.score_lead(profile, top_matches, contact)

    assert score < 60, f"Low-quality lead should score < 60, got {score}"
    assert len(reasons) > 0, "Should provide reasons"
