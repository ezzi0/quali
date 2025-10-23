"""Test agent tools"""
import pytest
from app.services.tools import normalize_budget


def test_normalize_budget_simple():
    """Test budget normalization with simple input"""
    result = normalize_budget("100k to 200k AED")

    assert result["min"] == 100000
    assert result["max"] == 200000
    assert result["currency"] == "AED"


def test_normalize_budget_single_value():
    """Test budget normalization with single value"""
    result = normalize_budget("150000 AED")

    assert result["min"] == 0
    assert result["max"] == 150000
    assert result["currency"] == "AED"


def test_normalize_budget_usd():
    """Test budget normalization with USD"""
    result = normalize_budget("$50k to $100k")

    assert result["min"] == 50000
    assert result["max"] == 100000
    assert result["currency"] == "USD"


def test_normalize_budget_no_numbers():
    """Test budget normalization with no numbers"""
    result = normalize_budget("not sure yet")

    assert result["min"] is None
    assert result["max"] is None
