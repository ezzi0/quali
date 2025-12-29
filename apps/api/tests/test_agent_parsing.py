"""Tests for agent argument parsing helpers (no network)"""
from app.services.agent import QualificationAgent


class DummyDB:
    """Minimal placeholder for agent constructor."""
    pass


def test_parse_tool_arguments_valid_json_object():
    agent = QualificationAgent(db=DummyDB())
    args, err = agent._parse_tool_arguments('{"lead_id": 1, "foo": "bar"}')

    assert err is None
    assert args["lead_id"] == 1
    assert args["foo"] == "bar"


def test_parse_tool_arguments_rejects_non_object():
    agent = QualificationAgent(db=DummyDB())
    args, err = agent._parse_tool_arguments('["not", "an", "object"]')

    assert args is None
    assert "must be a JSON object" in err


def test_parse_tool_arguments_invalid_json():
    agent = QualificationAgent(db=DummyDB())
    args, err = agent._parse_tool_arguments('{"lead_id": 1,,}')

    assert args is None
    assert "Invalid tool arguments" in err
