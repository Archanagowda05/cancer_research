import json
import os
import re
import time
from typing import TypedDict, Optional
from openai import OpenAI
from langgraph.graph import StateGraph, START, END

client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama',
)

MODEL = 'llama3.2:3b'

VALID_TOOLS = {
    "run_mutation_analysis",    # EXISTING
    "run_expression_analysis",  # EXISTING
    "run_integration",          # EXISTING
    "run_clinical_analysis",    # NEW optional
    "run_pathway_analysis",     # NEW optional
    "run_biomarker_analysis",   # NEW optional
}
# Default fallback plan = original 3-tool core (unchanged)
DEFAULT_PLAN = ["run_mutation_analysis", "run_expression_analysis", "run_integration"]

TOOL_DESCRIPTIONS = (
    "Available tools (use ONLY these exact names):\n"
    "  run_mutation_analysis    - Somatic mutation frequency, variant types, TMB\n"
    "  run_expression_analysis  - Differential expression: t-test, log2FC, BH correction\n"
    "  run_integration          - Convergent driver genes (requires mutation+expression first)\n"
    "  run_clinical_analysis    - Clinical variables: TMB, MSI, aneuploidy, grade, sample type\n"
    "  run_pathway_analysis     - Pathway enrichment on convergent genes (requires integration first)\n"
    "  run_biomarker_analysis   - ML classification Primary vs Metastasis (requires expression first)"
)

class AgentState(TypedDict):
    # Existing fields (unchanged)
    goal: str
    cancer_type: str
    plan: list
    plan_valid: bool
    retry_count: int
    mutation_result: Optional[dict]
    expression_result: Optional[dict]
    integration_result: Optional[dict]
    report: Optional[str]
    # New optional fields (additive)
    clinical_result: Optional[dict]
    pathway_result: Optional[dict]
    ranking_result: Optional[dict]
    biomarker_result: Optional[dict]
    run_log: Optional[dict]


def planner_node(state: AgentState) -> dict:
    goal = state.get("goal")
    cancer_type = state.get("cancer_type")
    
    base_prompt = f'''You are a bioinformatics agent.
Goal: {goal}
Cancer type: {cancer_type}

{TOOL_DESCRIPTIONS}

Rules:
  - run_integration MUST come after run_mutation_analysis and run_expression_analysis
  - run_pathway_analysis MUST come after run_integration
  - run_biomarker_analysis MUST come after run_expression_analysis
  - Only include tools relevant to the goal

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
        
        # --- NEW: Show the user what the AI is thinking ---
        print("\n[AI Planner Thinking...]")
        print(f"Raw Output from LLM:\n{raw}")

        match = re.search(r'\[.*\]', raw, re.DOTALL)
        raw_json = match.group(0) if match else raw
        steps = json.loads(raw_json)
        
        print(f"-> Extracted Plan: {steps}\n")
        
    except Exception as e:
        print(f"\n[AI Planner Error] Failed to parse plan: {e}")
        steps = [] # Invalid plan to fail validation
    
    return {"plan": steps}

def validator_node(state: AgentState) -> dict:
    print("\n" + "-"*50)
    print("🛡️ [VALIDATOR AGENT] Inspecting the Planner's Work...")
    plan = state.get("plan", [])
    retry_count = state.get("retry_count", 0)
    
    is_valid = True
    if not isinstance(plan, list) or len(plan) == 0:
        print("  -> ERROR: Plan is empty or not a valid JSON list.")
        is_valid = False
    elif not all(s in VALID_TOOLS for s in plan):
        print(f"  -> ERROR: Plan contains unknown tools. Only these are allowed: {VALID_TOOLS}")
        is_valid = False
        
    if not is_valid:
        retry_count += 1
        print(f"  -> Result: ❌ Plan REJECTED. Retry count is now {retry_count}.")
    else:
        print("  -> Result: ✅ Plan APPROVED! All tools are valid.")
    print("-"*50)
        
    return {"plan_valid": is_valid, "retry_count": retry_count}

def fallback_node(state: AgentState) -> dict:
    """Activated when the planner exceeds max retries. Sets the default safe plan."""
    print("  -> Fallback Node: Overriding with default plan:", DEFAULT_PLAN)
    return {"plan": DEFAULT_PLAN.copy(), "plan_valid": True}

def route_after_validation(state: AgentState) -> str:
    print("\n" + "-"*50)
    print("🔀 [ORCHESTRATOR] Routing tasks based on validation...")
    if state.get("plan_valid"):
        print("  -> Decision: Proceeding to Python Execution Phase.")
        print("-"*50 + "\n")
        return "mutation_node"
    
    if state.get("retry_count", 0) < 2:
        print("  -> Decision: Sending request BACK to AI Planner to fix the mistake.")
        print("-"*50 + "\n")
        return "planner_node"
    
    # Route to the fallback_node which will properly update state
    print("  -> Decision: Maximum retries reached. Activating safe fallback plan.")
    print("-"*50 + "\n")
    return "fallback_node"

def mutation_node(state: AgentState) -> dict:
    if "run_mutation_analysis" not in state.get("plan", []):
        return {}
    
    print("[Agent] Running Mutation Analysis...")
    from pipeline.mutation import MutationAnalyzer
    from config import DATA_PATHS
    
    cancer_type = state.get("cancer_type")
    analyzer = MutationAnalyzer(DATA_PATHS[cancer_type]['mutations'])
    summary = analyzer.summarize()
    
    # Save chart to disk with a timestamp to prevent overwriting
    timestamp = int(time.time())
    analyzer.plot_top_genes(save_path=f'data/processed/{cancer_type}_mutations_{timestamp}.png')
    
    return {"mutation_result": summary}

def expression_node(state: AgentState) -> dict:
    if "run_expression_analysis" not in state.get("plan", []):
        return {}
        
    print("[Agent] Running Expression Analysis...")
    from pipeline.expression import ExpressionAnalyzer
    from config import DATA_PATHS
    
    cancer_type = state.get("cancer_type")
    analyzer = ExpressionAnalyzer(DATA_PATHS[cancer_type]['expression'])
    results_df = analyzer.run_differential_expression()
    summary = analyzer.summarize(results_df)
    
    # Save chart to disk with a timestamp to prevent overwriting
    timestamp = int(time.time())
    analyzer.plot_volcano(results_df, save_path=f'data/processed/{cancer_type}_volcano_{timestamp}.png')
    
    return {"expression_result": summary}

def integrator_node(state: AgentState) -> dict:
    if "run_integration" not in state.get("plan", []):
        return {}
        
    print("[Agent] Running Multi-Omics Integration...")
    from pipeline.integrator import MultiOmicsIntegrator
    
    mut_summary = state.get("mutation_result")
    exp_summary = state.get("expression_result")
    
    # Skip if previous steps failed or weren't run
    if not mut_summary or not exp_summary:
        print("[Agent] Skipping integration (missing mutation or expression results)")
        return {}
        
    integrator = MultiOmicsIntegrator(mut_summary, exp_summary)
    report = integrator.generate_report()
    
    return {"integration_result": report}


def synthesizer_node(state: AgentState) -> dict:
    goal = state.get("goal")
    cancer_type = state.get("cancer_type")
    
    print("[Agent] Synthesizing final biological report...")
    
    mut_result      = state.get('mutation_result') or {}
    exp_result      = state.get('expression_result') or {}
    int_result      = state.get('integration_result') or {}
    ranking_result  = state.get('ranking_result') or {}
    clinical_result = state.get('clinical_result') or {}
    pathway_result  = state.get('pathway_result') or {}
    biomarker_result= state.get('biomarker_result') or {}

    # Build data context — only include sections for analyses that actually ran
    sections = []
    sections.append(f"RESEARCH QUESTION: {goal}")
    sections.append(f"DATASET: TCGA {cancer_type} via cBioPortal")

    if mut_result:
        sections.append("MUTATION RESULTS (COMPUTED RESULT):\n" +
                        json.dumps(mut_result, indent=2))
    if exp_result:
        sections.append("EXPRESSION RESULTS (COMPUTED RESULT):\n" +
                        json.dumps(exp_result, indent=2))
    if int_result:
        sections.append("CONVERGENT GENES (COMPUTED RESULT — Mutated genes INTERSECT DEGs):\n" +
                        json.dumps(int_result.get('convergent_genes', {}), indent=2))
    if ranking_result.get('ranked_genes'):
        sections.append("EVIDENCE RANKING (COMPUTED RESULT — additional layer, original logic preserved):\n" +
                        json.dumps(ranking_result.get('ranked_genes', [])[:5], indent=2))
    if pathway_result.get('status') == 'complete':
        sections.append("PATHWAY ENRICHMENT (COMPUTED RESULT — Enrichr API):\n" +
                        json.dumps(pathway_result.get('top_5_terms', {}), indent=2))
    elif pathway_result.get('status') in ('unavailable', 'skipped'):
        sections.append(f"PATHWAY ENRICHMENT: {pathway_result.get('message', 'Skipped')}")
    if clinical_result:
        surv = clinical_result.get('survival_status', {})
        sections.append("CLINICAL VARIABLES (COMPUTED RESULT):\n" +
                        json.dumps(clinical_result.get('continuous_variables', {}), indent=2) +
                        (f"\nSURVIVAL NOTE: {surv.get('message','')}" if not surv.get('available') else ""))
    if biomarker_result.get('status') == 'complete':
        sections.append("BIOMARKER EXPLORATION (COMPUTED RESULT — research only, no clinical claim):\n" +
                        json.dumps({'logistic_regression': biomarker_result.get('logistic_regression'),
                                    'random_forest': biomarker_result.get('random_forest'),
                                    'disclaimer': biomarker_result.get('disclaimer')}, indent=2))
    elif biomarker_result.get('status') == 'skipped':
        sections.append(f"BIOMARKER EXPLORATION: Skipped — {biomarker_result.get('reason','')}")

    summary_text = "\n\n".join(sections)

    prompt = f'''You are a cancer bioinformatics expert writing a structured research report.

Rules:
1. Clearly label COMPUTED RESULT, AI INTERPRETATION, and RESEARCH HYPOTHESIS separately.
2. Do NOT convert associations into clinical diagnoses or treatment recommendations.
3. Include a Limitations section acknowledging methodological constraints.
4. Only discuss analyses present in the data below.
5. Be specific about gene names from the data.
6. Keep under 400 words.

Report sections (include only if data is present):
  - Key Mutation Findings
  - Key Expression Findings
  - Convergent Driver Genes
  - Evidence Ranking (if available)
  - Pathway Insights (if available)
  - Clinical Variables (if available)
  - Biomarker Exploration (if available)
  - Limitations
  - Research Hypotheses

{summary_text}'''

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{'role': 'user', 'content': prompt}],
        temperature=0.2,
    )
    return {"report": response.choices[0].message.content}


# ─── NEW: Evidence-Based Candidate Ranker Node ────────────────────────────────
def ranker_node(state: AgentState) -> dict:
    integration_result = state.get("integration_result")
    mut_result = state.get("mutation_result")
    exp_result = state.get("expression_result")
    if not integration_result or not mut_result or not exp_result:
        return {}
    print("[Agent] Running Evidence-Based Candidate Ranking...")
    from pipeline.ranker import CandidateRanker
    ranker = CandidateRanker(mut_result, exp_result, state.get("pathway_result"))
    ranking = ranker.rank()
    cancer_type = state.get("cancer_type")
    ranker.plot_ranking(ranking, save_path=f'data/processed/{cancer_type}_ranking_{int(time.time())}.png')
    return {"ranking_result": ranking}


# ─── NEW: Clinical Analysis Node ──────────────────────────────────────────────
def clinical_node(state: AgentState) -> dict:
    if "run_clinical_analysis" not in state.get("plan", []):
        return {}
    print("[Agent] Running Clinical Variable Analysis...")
    from pipeline.clinical import ClinicalAnalyzer
    from config import DATA_PATHS
    cancer_type = state.get("cancer_type")
    analyzer = ClinicalAnalyzer(DATA_PATHS[cancer_type]['clinical'])
    summary = analyzer.summarise()
    analyzer.plot_distributions(save_path=f'data/processed/{cancer_type}_clinical_{int(time.time())}.png')
    return {"clinical_result": summary}


# ─── NEW: Pathway Analysis Node ───────────────────────────────────────────────
def pathway_node(state: AgentState) -> dict:
    if "run_pathway_analysis" not in state.get("plan", []):
        return {}
    print("[Agent] Running Pathway Enrichment Analysis...")
    from pipeline.pathway import PathwayAnalyzer
    int_result = state.get("integration_result", {})
    conv = int_result.get("convergent_genes", {})
    genes = list(
        set(conv.get("mutated_AND_upregulated", []))
        | set(conv.get("mutated_AND_downregulated", []))
    )
    if not genes:
        print("[Agent] No convergent genes available for pathway analysis.")
        return {"pathway_result": {"status": "skipped", "message": "No convergent genes found."}}
    analyzer = PathwayAnalyzer(genes)
    return {"pathway_result": analyzer.run()}


# ─── NEW: Biomarker Analysis Node ─────────────────────────────────────────────
def biomarker_node(state: AgentState) -> dict:
    if "run_biomarker_analysis" not in state.get("plan", []):
        return {}
    print("[Agent] Running Biomarker Exploration...")
    from pipeline.biomarker import BiomarkerExplorer
    from pipeline.expression import ExpressionAnalyzer
    from config import DATA_PATHS
    import pandas as pd
    cancer_type = state.get("cancer_type")
    if not state.get("expression_result"):
        return {"biomarker_result": {"status": "skipped", "reason": "Expression analysis not run."}}
    analyzer = ExpressionAnalyzer(DATA_PATHS[cancer_type]['expression'])
    clinical = pd.read_csv(DATA_PATHS[cancer_type]['clinical'], sep='\t', comment='#', low_memory=False)
    explorer = BiomarkerExplorer(analyzer.expr_log, clinical)
    return {"biomarker_result": explorer.run()}


# ─── NEW: Traceability Logger Node ────────────────────────────────────────────
def logger_node(state: AgentState) -> dict:
    import datetime
    cancer_type = state.get("cancer_type", "UNKNOWN")
    log = {
        "timestamp":        datetime.datetime.now().isoformat(timespec="seconds"),
        "goal":             state.get("goal"),
        "cancer_type":      cancer_type,
        "plan":             state.get("plan", []),
        "validation_status": "approved" if state.get("plan_valid") else "fallback",
        "retry_count":      state.get("retry_count", 0),
        "thresholds":       {"padj": 0.05, "lfc_abs": 1.0, "top_n_variable_genes": 500},
        "sample_counts": {
            "mutation_patients": (state.get("mutation_result") or {}).get("total_patients"),
            "expression_genes":  (state.get("expression_result") or {}).get("total_genes_tested"),
        },
        "results_summary": {
            "top_mutated_gene":     ((state.get("mutation_result") or {}).get("top_10_genes") or [None])[0],
            "convergent_genes_up":  (state.get("integration_result") or {})
                                       .get("convergent_genes", {}).get("mutated_AND_upregulated", []),
            "top_ranked_candidate": (state.get("ranking_result") or {}).get("top_candidate"),
            "pathway_status":       (state.get("pathway_result") or {}).get("status", "not_run"),
            "biomarker_status":     (state.get("biomarker_result") or {}).get("status", "not_run"),
            "survival_available":   (state.get("clinical_result") or {})
                                       .get("survival_status", {}).get("available", "not_run"),
        },
    }
    os.makedirs("data/processed", exist_ok=True)
    log_path = f"data/processed/{cancer_type}_run_log_{int(time.time())}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, default=str)
    print(f"[Traceability] Run log saved → {log_path}")
    return {"run_log": log}


# ─── LangGraph Workflow ────────────────────────────────────────────────────────

workflow = StateGraph(AgentState)

# Register nodes (all existing nodes preserved)
workflow.add_node("planner_node",    planner_node)
workflow.add_node("validator_node",  validator_node)
workflow.add_node("fallback_node",   fallback_node)
workflow.add_node("mutation_node",   mutation_node)
workflow.add_node("expression_node", expression_node)
workflow.add_node("integrator_node", integrator_node)
workflow.add_node("ranker_node",     ranker_node)      # NEW
workflow.add_node("clinical_node",   clinical_node)    # NEW
workflow.add_node("pathway_node",    pathway_node)     # NEW
workflow.add_node("biomarker_node",  biomarker_node)   # NEW
workflow.add_node("logger_node",     logger_node)      # NEW
workflow.add_node("synthesizer_node",synthesizer_node)

# Wire edges
workflow.add_edge(START, "planner_node")
workflow.add_edge("planner_node", "validator_node")
workflow.add_conditional_edges(
    "validator_node",
    route_after_validation,
    {"mutation_node": "mutation_node", "planner_node": "planner_node", "fallback_node": "fallback_node"}
)
workflow.add_edge("fallback_node",    "mutation_node")
workflow.add_edge("mutation_node",    "expression_node")
workflow.add_edge("expression_node",  "integrator_node")
workflow.add_edge("integrator_node",  "ranker_node")     # NEW
workflow.add_edge("ranker_node",      "clinical_node")   # NEW
workflow.add_edge("clinical_node",    "pathway_node")    # NEW
workflow.add_edge("pathway_node",     "biomarker_node")  # NEW
workflow.add_edge("biomarker_node",   "logger_node")     # NEW
workflow.add_edge("logger_node",      "synthesizer_node")
workflow.add_edge("synthesizer_node", END)

graph = workflow.compile()
