import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Add the project root to the python path so we can import the agent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.orchestrator import (
    planner_node, 
    validator_node, 
    route_after_validation, 
    DEFAULT_PLAN,
    VALID_TOOLS
)

@patch('agent.orchestrator.client.chat.completions.create')
def test_planner_node_valid_json(mock_create):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '["run_mutation_analysis", "run_expression_analysis"]'
    mock_create.return_value = mock_response
    
    state = {"goal": "test", "cancer_type": "BRCA", "retry_count": 0}
    result = planner_node(state)
    assert result["plan"] == ["run_mutation_analysis", "run_expression_analysis"]

@patch('agent.orchestrator.client.chat.completions.create')
def test_planner_node_invalid_json(mock_create):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = 'This is not json'
    mock_create.return_value = mock_response
    
    state = {"goal": "test", "cancer_type": "BRCA", "retry_count": 0}
    result = planner_node(state)
    assert "plan" in result
    assert result["plan"] == [] or not isinstance(result["plan"], list)

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

def test_route_after_validation():
    # 1. Proceed when valid
    state_valid = {"plan_valid": True, "retry_count": 0}
    assert route_after_validation(state_valid) == "mutation_node"
    
    # 2. Loop back when invalid and retry_count < 2
    state_invalid_retry = {"plan_valid": False, "retry_count": 1}
    assert route_after_validation(state_invalid_retry) == "planner_node"
    
    # 3. Fallback when retry_count >= 2
    state_fallback = {"plan_valid": False, "retry_count": 2, "plan": ["bad_tool"]}
    assert route_after_validation(state_fallback) == "mutation_node"
    assert state_fallback["plan"] == DEFAULT_PLAN
    assert state_fallback["plan_valid"] is True
