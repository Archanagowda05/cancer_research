import json
import re
from typing import TypedDict, Optional
from openai import OpenAI
from langgraph.graph import StateGraph, START, END

client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama',
)

MODEL = 'llama3.2:3b'

VALID_TOOLS = {"run_mutation_analysis", "run_expression_analysis", "run_integration"}
DEFAULT_PLAN = ["run_mutation_analysis", "run_expression_analysis", "run_integration"]

class AgentState(TypedDict):
    goal: str
    cancer_type: str
    plan: list
    plan_valid: bool
    retry_count: int
    mutation_result: Optional[dict]
    expression_result: Optional[dict]
    integration_result: Optional[dict]
    report: Optional[str]

def planner_node(state: AgentState) -> dict:
    goal = state.get("goal")
    cancer_type = state.get("cancer_type")
    
    base_prompt = f'''You are a bioinformatics agent.
Goal: {goal}
Cancer type: {cancer_type}
Available tools: run_mutation_analysis, run_expression_analysis, run_integration
Return ONLY a JSON list of tool names in the order they should run.
Example: ["run_mutation_analysis", "run_expression_analysis", "run_integration"]
Return ONLY the JSON list. No explanation.'''

    prompt = base_prompt
    if state.get("retry_count", 0) > 0:
        prompt += f"\n\nYour previous response was invalid. Return ONLY a valid JSON list this time, nothing else."

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0, 
        )
        raw = response.choices[0].message.content.strip()

        match = re.search(r'\[.*\]', raw, re.DOTALL)
        raw_json = match.group(0) if match else raw
        steps = json.loads(raw_json)
        
    except Exception as e:
        steps = [] # Invalid plan to fail validation
    
    return {"plan": steps}

def validator_node(state: AgentState) -> dict:
    plan = state.get("plan", [])
    retry_count = state.get("retry_count", 0)
    
    is_valid = True
    if not isinstance(plan, list) or len(plan) == 0:
        is_valid = False
    elif not all(s in VALID_TOOLS for s in plan):
        is_valid = False
        
    if not is_valid:
        retry_count += 1
        
    return {"plan_valid": is_valid, "retry_count": retry_count}

def route_after_validation(state: AgentState) -> str:
    if state.get("plan_valid"):
        return "mutation_node"
    
    if state.get("retry_count", 0) < 2:
        return "planner_node"
    
    # Fallback to the default 3-tool plan and proceed
    state["plan"] = DEFAULT_PLAN.copy()
    state["plan_valid"] = True
    return "mutation_node"

def mutation_node(state: AgentState) -> dict:
    return {}

def expression_node(state: AgentState) -> dict:
    return {}

def integrator_node(state: AgentState) -> dict:
    return {}

def synthesizer_node(state: AgentState) -> dict:
    return {}

workflow = StateGraph(AgentState)

workflow.add_node("planner_node", planner_node)
workflow.add_node("validator_node", validator_node)
workflow.add_node("mutation_node", mutation_node)
workflow.add_node("expression_node", expression_node)
workflow.add_node("integrator_node", integrator_node)
workflow.add_node("synthesizer_node", synthesizer_node)

workflow.add_edge(START, "planner_node")
workflow.add_edge("planner_node", "validator_node")
workflow.add_conditional_edges("validator_node", route_after_validation)
workflow.add_edge("mutation_node", "expression_node")
workflow.add_edge("expression_node", "integrator_node")
workflow.add_edge("integrator_node", "synthesizer_node")
workflow.add_edge("synthesizer_node", END)

graph = workflow.compile()
