import sys, os, pytest
from unittest.mock import patch, MagicMock
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.orchestrator import (
    planner_node, validator_node, route_after_validation,
    DEFAULT_PLAN, VALID_TOOLS
)


@patch("agent.orchestrator.client.chat.completions.create")
def test_planner_node_valid_json(mock_create):
    mock_response = MagicMock()
    mock_response.choices[0].message.content =         '["run_mutation_analysis", "run_expression_analysis"]'
    mock_create.return_value = mock_response
    state = {"goal": "test", "cancer_type": "BRCA", "retry_count": 0}
    result = planner_node(state)
    assert result["plan"] == ["run_mutation_analysis", "run_expression_analysis"]


@patch("agent.orchestrator.client.chat.completions.create")
def test_planner_node_invalid_json(mock_create):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "This is not json"
    mock_create.return_value = mock_response
    state = {"goal": "test", "cancer_type": "BRCA", "retry_count": 0}
    result = planner_node(state)
    assert "plan" in result
    assert result["plan"] == []


def test_validator_node_valid():
    state = {"plan": ["run_mutation_analysis"], "retry_count": 0}
    result = validator_node(state)
    assert result["plan_valid"] is True
    assert result["retry_count"] == 0


def test_validator_node_invalid_tool():
    state = {"plan": ["run_mutation_analysis", "fake_tool"], "retry_count": 0}
    result = validator_node(state)
    assert result["plan_valid"] is False
    assert result["retry_count"] == 1


def test_validator_accepts_new_tools():
    for tool in ["run_clinical_analysis", "run_pathway_analysis", "run_biomarker_analysis"]:
        state = {"plan": [tool], "retry_count": 0}
        result = validator_node(state)
        assert result["plan_valid"] is True, f"{tool} should be accepted"


def test_valid_tools_contains_all_six():
    expected = {
        "run_mutation_analysis", "run_expression_analysis", "run_integration",
        "run_clinical_analysis", "run_pathway_analysis", "run_biomarker_analysis"
    }
    assert expected == VALID_TOOLS


def test_route_after_validation_proceed():
    state = {"plan_valid": True, "retry_count": 0}
    assert route_after_validation(state) == "mutation_node"


def test_route_after_validation_retry():
    state = {"plan_valid": False, "retry_count": 1}
    assert route_after_validation(state) == "planner_node"


def test_route_after_validation_fallback():
    state = {"plan_valid": False, "retry_count": 2, "plan": ["bad_tool"]}
    result = route_after_validation(state)
    # After our fix, route returns "fallback_node" (not mutation_node)
    # and does NOT mutate state directly
    assert result == "fallback_node"


def test_default_plan_is_original_three_tools():
    assert DEFAULT_PLAN == [
        "run_mutation_analysis",
        "run_expression_analysis",
        "run_integration"
    ]
