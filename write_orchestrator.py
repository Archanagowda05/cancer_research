import sys, os
sys.stdout.reconfigure(encoding="utf-8")

orchestrator = """\
import json
import re
import time
import datetime
from typing import TypedDict, Optional, List
from openai import OpenAI
from langgraph.graph import StateGraph, START, END

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)

MODEL = "llama3.2:3b"

# ─── Tool Registry ─────────────────────────────────────────────────────────────
# EXISTING tools (unchanged):
#   run_mutation_analysis, run_expression_analysis, run_integration
# NEW optional tools (additive):
#   run_clinical_analysis, run_pathway_analysis, run_biomarker_analysis
VALID_TOOLS = {
    "run_mutation_analysis",
    "run_expression_analysis",
    "run_integration",
    "run_clinical_analysis",
    "run_pathway_analysis",
    "run_biomarker_analysis",
}

# Default fallback plan matches original 3-tool core (unchanged)
DEFAULT_PLAN = ["run_mutation_analysis", "run_expression_analysis", "run_integration"]

TOOL_DESCRIPTIONS = (
    "Available tools (use only these names exactly):\\n"
    "  run_mutation_analysis    - Analyse somatic mutation frequency, variant types, TMB\\n"
    "  run_expression_analysis  - Differential gene expression: t-test, log2FC, BH correction\\n"
    "  run_integration          - Integrate mutation + expression to find convergent driver genes\\n"
    "                             (requires run_mutation_analysis AND run_expression_analysis)\\n"
    "  run_clinical_analysis    - Analyse clinical variables: TMB distribution, MSI, aneuploidy,\\n"
    "                             grade, sample type (no survival data available)\\n"
    "  run_pathway_analysis     - Pathway enrichment on convergent genes via Enrichr API\\n"
    "                             (requires run_integration to have run first)\\n"
    "  run_biomarker_analysis   - Research-level ML classification of Primary vs Metastasis\\n"
    "                             (requires run_expression_analysis to have run first)"
)


# ─── State ─────────────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    # Existing fields (unchanged)
    goal:               str
    cancer_type:        str
    plan:               list
    plan_valid:         bool
    retry_count:        int
    mutation_result:    Optional[dict]
    expression_result:  Optional[dict]
    integration_result: Optional[dict]
    report:             Optional[str]
    # New optional fields (additive)
    clinical_result:    Optional[dict]
    pathway_result:     Optional[dict]
    ranking_result:     Optional[dict]
    biomarker_result:   Optional[dict]
    run_log:            Optional[dict]


# ─── Helpers ───────────────────────────────────────────────────────────────────
def _ts() -> int:
    return int(time.time())

def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")

def _save_run_log(state: AgentState, cancer_type: str) -> None:
    log = state.get("run_log", {})
    if not log:
        return
    os.makedirs("data/processed", exist_ok=True)
    path = f"data/processed/{cancer_type}_run_log_{_ts()}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, default=str)
    print(f"[Traceability] Run log saved to {path}")


# ─── AI Planner Node ───────────────────────────────────────────────────────────
def planner_node(state: AgentState) -> dict:
    goal        = state.get("goal")
    cancer_type = state.get("cancer_type")

    base_prompt = (
        "You are a bioinformatics agent.\\n"
        f"Goal: {goal}\\n"
        f"Cancer type: {cancer_type}\\n\\n"
        f"{TOOL_DESCRIPTIONS}\\n\\n"
        "Return ONLY a JSON list of tool names in the order they should run.\\n"
        "Rules:\\n"
        "  - run_integration MUST come after run_mutation_analysis and run_expression_analysis\\n"
        "  - run_pathway_analysis MUST come after run_integration\\n"
        "  - run_biomarker_analysis MUST come after run_expression_analysis\\n"
        "  - Only include tools relevant to the goal\\n"
        "Example: [\\"run_mutation_analysis\\", \\"run_expression_analysis\\", \\"run_integration\\"]\\n"
        "Return ONLY the JSON list. No explanation."
    )

    prompt = base_prompt
    if state.get("retry_count", 0) > 0:
        prompt += "\\n\\nYour previous response was invalid. Return ONLY a valid JSON list this time, nothing else."

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        raw = response.choices[0].message.content.strip()
        print("\\n[AI Planner Thinking...]")
        print(f"Raw Output from LLM:\\n{raw}")
        match = re.search(r"\\[.*\\]", raw, re.DOTALL)
        raw_json = match.group(0) if match else raw
        steps = json.loads(raw_json)
        print(f"-> Extracted Plan: {steps}\\n")
    except Exception as e:
        print(f"\\n[AI Planner Error] Failed to parse plan: {e}")
        steps = []

    return {"plan": steps}


# ─── Validator Node (EXISTING — unchanged logic) ───────────────────────────────
def validator_node(state: AgentState) -> dict:
    print("\\n" + "-"*50)
    print("Shield [VALIDATOR AGENT] Inspecting the Planner's Work...")
    plan        = state.get("plan", [])
    retry_count = state.get("retry_count", 0)
    is_valid    = True

    if not isinstance(plan, list) or len(plan) == 0:
        print("  -> ERROR: Plan is empty or not a valid JSON list.")
        is_valid = False
    elif not all(s in VALID_TOOLS for s in plan):
        unknown = [s for s in plan if s not in VALID_TOOLS]
        print(f"  -> ERROR: Unknown tools: {unknown}. Allowed: {sorted(VALID_TOOLS)}")
        is_valid = False

    if not is_valid:
        retry_count += 1
        print(f"  -> Result: Plan REJECTED. Retry count is now {retry_count}.")
    else:
        print("  -> Result: Plan APPROVED! All tools are valid.")
    print("-"*50)
    return {"plan_valid": is_valid, "retry_count": retry_count}


# ─── Fallback Node (EXISTING — unchanged) ─────────────────────────────────────
def fallback_node(state: AgentState) -> dict:
    print("  -> Fallback Node: Overriding with default plan:", DEFAULT_PLAN)
    return {"plan": DEFAULT_PLAN.copy(), "plan_valid": True}


# ─── Routing (EXISTING — extended for new nodes) ──────────────────────────────
def route_after_validation(state: AgentState) -> str:
    print("\\n" + "-"*50)
    print("Arrow [ORCHESTRATOR] Routing tasks based on validation...")
    if state.get("plan_valid"):
        print("  -> Decision: Proceeding to Python Execution Phase.")
        print("-"*50 + "\\n")
        return "mutation_node"
    if state.get("retry_count", 0) < 2:
        print("  -> Decision: Sending request BACK to AI Planner.")
        print("-"*50 + "\\n")
        return "planner_node"
    print("  -> Decision: Maximum retries reached. Activating safe fallback plan.")
    print("-"*50 + "\\n")
    return "fallback_node"


# ─── EXISTING Execution Nodes (unchanged logic) ───────────────────────────────
def mutation_node(state: AgentState) -> dict:
    if "run_mutation_analysis" not in state.get("plan", []):
        return {}
    print("[Agent] Running Mutation Analysis...")
    from pipeline.mutation import MutationAnalyzer
    from config import DATA_PATHS
    cancer_type = state.get("cancer_type")
    analyzer    = MutationAnalyzer(DATA_PATHS[cancer_type]["mutations"])
    summary     = analyzer.summarize()
    analyzer.plot_top_genes(save_path=f"data/processed/{cancer_type}_mutations_{_ts()}.png")
    return {"mutation_result": summary}


def expression_node(state: AgentState) -> dict:
    if "run_expression_analysis" not in state.get("plan", []):
        return {}
    print("[Agent] Running Expression Analysis...")
    from pipeline.expression import ExpressionAnalyzer
    from config import DATA_PATHS
    cancer_type = state.get("cancer_type")
    analyzer    = ExpressionAnalyzer(DATA_PATHS[cancer_type]["expression"])
    results_df  = analyzer.run_differential_expression()
    summary     = analyzer.summarize(results_df)
    analyzer.plot_volcano(results_df, save_path=f"data/processed/{cancer_type}_volcano_{_ts()}.png")
    return {"expression_result": summary}


def integrator_node(state: AgentState) -> dict:
    if "run_integration" not in state.get("plan", []):
        return {}
    print("[Agent] Running Multi-Omics Integration...")
    from pipeline.integrator import MultiOmicsIntegrator
    mut_summary = state.get("mutation_result")
    exp_summary = state.get("expression_result")
    if not mut_summary or not exp_summary:
        print("[Agent] Skipping integration (missing mutation or expression results)")
        return {}
    integrator = MultiOmicsIntegrator(mut_summary, exp_summary)
    report     = integrator.generate_report()
    return {"integration_result": report}


# ─── NEW Execution Nodes (additive) ───────────────────────────────────────────
def ranker_node(state: AgentState) -> dict:
    """Always runs after integrator if integration was performed."""
    integration_result = state.get("integration_result")
    mut_result = state.get("mutation_result")
    exp_result = state.get("expression_result")
    if not integration_result or not mut_result or not exp_result:
        return {}
    print("[Agent] Running Evidence-Based Candidate Ranking...")
    from pipeline.ranker import CandidateRanker
    pathway_result = state.get("pathway_result")  # may be None, that is fine
    ranker  = CandidateRanker(mut_result, exp_result, pathway_result)
    ranking = ranker.rank()
    ranker.plot_ranking(
        ranking,
        save_path=f"data/processed/{state.get('cancer_type')}_ranking_{_ts()}.png"
    )
    return {"ranking_result": ranking}


def clinical_node(state: AgentState) -> dict:
    if "run_clinical_analysis" not in state.get("plan", []):
        return {}
    print("[Agent] Running Clinical Variable Analysis...")
    from pipeline.clinical import ClinicalAnalyzer
    from config import DATA_PATHS
    cancer_type = state.get("cancer_type")
    analyzer    = ClinicalAnalyzer(DATA_PATHS[cancer_type]["clinical"])
    summary     = analyzer.summarise()
    analyzer.plot_distributions(
        save_path=f"data/processed/{cancer_type}_clinical_{_ts()}.png"
    )
    return {"clinical_result": summary}


def pathway_node(state: AgentState) -> dict:
    if "run_pathway_analysis" not in state.get("plan", []):
        return {}
    print("[Agent] Running Pathway Enrichment Analysis...")
    from pipeline.pathway import PathwayAnalyzer
    integration_result = state.get("integration_result", {})
    convergent = integration_result.get("convergent_genes", {})
    # Combine all convergent gene sets
    candidate_genes = list(
        set(convergent.get("mutated_AND_upregulated", []))
        | set(convergent.get("mutated_AND_downregulated", []))
    )
    if not candidate_genes:
        print("[Agent] No convergent genes found for pathway analysis.")
        return {"pathway_result": {"status": "skipped",
                                   "message": "No convergent genes available."}}
    analyzer = PathwayAnalyzer(candidate_genes)
    result   = analyzer.run()
    return {"pathway_result": result}


def biomarker_node(state: AgentState) -> dict:
    if "run_biomarker_analysis" not in state.get("plan", []):
        return {}
    print("[Agent] Running Biomarker Exploration...")
    from pipeline.biomarker import BiomarkerExplorer
    from pipeline.expression import ExpressionAnalyzer
    from config import DATA_PATHS
    import pandas as pd
    cancer_type    = state.get("cancer_type")
    exp_summary    = state.get("expression_result")
    if not exp_summary:
        return {"biomarker_result": {"status": "skipped",
                                     "reason": "Expression analysis not run."}}
    # Load expression log matrix and clinical data
    analyzer   = ExpressionAnalyzer(DATA_PATHS[cancer_type]["expression"])
    clinical   = pd.read_csv(DATA_PATHS[cancer_type]["clinical"], sep="\\t",
                             comment="#", low_memory=False)
    explorer   = BiomarkerExplorer(analyzer.expr_log, clinical)
    result     = explorer.run()
    return {"biomarker_result": result}


# ─── Traceability Logger Node ──────────────────────────────────────────────────
def logger_node(state: AgentState) -> dict:
    """Records run metadata for reproducibility."""
    cancer_type = state.get("cancer_type", "UNKNOWN")
    log = {
        "timestamp":        _now(),
        "goal":             state.get("goal"),
        "cancer_type":      cancer_type,
        "plan":             state.get("plan", []),
        "validation_status": "approved" if state.get("plan_valid") else "fallback",
        "retry_count":      state.get("retry_count", 0),
        "nodes_executed":   [t for t in state.get("plan", [])],
        "thresholds": {"padj": 0.05, "lfc_abs": 1.0, "top_n_variable_genes": 500},
        "sample_counts": {
            "mutations":  state.get("mutation_result", {}).get("total_patients"),
            "expression": state.get("expression_result", {}).get("total_genes_tested"),
        },
        "results_summary": {
            "mutation_top_gene":    (state.get("mutation_result") or {}).get("top_10_genes", [None])[0],
            "convergent_genes":     (state.get("integration_result") or {})
                                        .get("convergent_genes", {})
                                        .get("mutated_AND_upregulated", []),
            "top_ranked_candidate": (state.get("ranking_result") or {}).get("top_candidate"),
            "pathway_status":       (state.get("pathway_result") or {}).get("status"),
            "biomarker_status":     (state.get("biomarker_result") or {}).get("status"),
            "clinical_survival_available": (
                (state.get("clinical_result") or {})
                .get("survival_status", {}).get("available", "not_run")
            ),
        },
        "warnings": [],
    }
    _save_run_log({"run_log": log}, cancer_type)
    return {"run_log": log}


# ─── AI Synthesizer Node (Enhanced) ───────────────────────────────────────────
def synthesizer_node(state: AgentState) -> dict:
    goal        = state.get("goal")
    cancer_type = state.get("cancer_type")
    print("[Agent] Synthesizing final biological report...")

    mut_result     = state.get("mutation_result") or {}
    exp_result     = state.get("expression_result") or {}
    int_result     = state.get("integration_result") or {}
    ranking_result = state.get("ranking_result") or {}
    clinical_result= state.get("clinical_result") or {}
    pathway_result = state.get("pathway_result") or {}
    biomarker_result= state.get("biomarker_result") or {}

    # Build the data context, adding sections only for analyses that ran
    sections = []

    sections.append(f"RESEARCH QUESTION: {goal}")
    sections.append(f"DATASET: TCGA {cancer_type} via cBioPortal")

    if mut_result:
        sections.append("MUTATION RESULTS (COMPUTED):\\n" + json.dumps(mut_result, indent=2))

    if exp_result:
        sections.append("EXPRESSION RESULTS (COMPUTED):\\n" + json.dumps(exp_result, indent=2))

    if int_result:
        sections.append("CONVERGENT GENES (COMPUTED — Mutated ∩ DEG):\\n"
                        + json.dumps(int_result.get("convergent_genes", {}), indent=2))

    if ranking_result.get("ranked_genes"):
        sections.append("EVIDENCE-BASED RANKING (COMPUTED — additional layer, not a replacement):\\n"
                        + json.dumps(ranking_result.get("ranked_genes", [])[:5], indent=2))

    if pathway_result.get("status") == "complete":
        sections.append("PATHWAY ENRICHMENT (COMPUTED — Enrichr API):\\n"
                        + json.dumps(pathway_result.get("top_5_terms", {}), indent=2))
    elif pathway_result.get("status") == "unavailable":
        sections.append(f"PATHWAY ENRICHMENT: {pathway_result.get('message', 'Unavailable')}")

    if clinical_result:
        surv_msg = clinical_result.get("survival_status", {}).get("message", "")
        sections.append("CLINICAL VARIABLES (COMPUTED):\\n"
                        + json.dumps(clinical_result.get("continuous_variables", {}), indent=2)
                        + (f"\\nSURVIVAL NOTE: {surv_msg}" if surv_msg else ""))

    if biomarker_result.get("status") == "complete":
        sections.append("BIOMARKER EXPLORATION (COMPUTED — research only, no clinical claim):\\n"
                        + json.dumps({
                            "logistic_regression": biomarker_result.get("logistic_regression"),
                            "random_forest":       biomarker_result.get("random_forest"),
                            "disclaimer":          biomarker_result.get("disclaimer"),
                        }, indent=2))
    elif biomarker_result.get("status") == "skipped":
        sections.append(f"BIOMARKER EXPLORATION: Skipped — {biomarker_result.get('reason', '')}")

    summary_text = "\\n\\n".join(sections)

    prompt = (
        "You are a cancer bioinformatics expert writing a structured research report.\\n\\n"
        "Rules for this report:\\n"
        "1. Clearly label COMPUTED RESULT, AI INTERPRETATION, and RESEARCH HYPOTHESIS separately.\\n"
        "2. Do NOT convert associations into clinical diagnoses or treatment recommendations.\\n"
        "3. Include a Limitations section acknowledging methodological constraints.\\n"
        "4. Only discuss analyses that are in the data below.\\n"
        "5. Be specific about gene names from the data.\\n"
        "6. Keep under 400 words.\\n\\n"
        "Report sections to include (only if data is present):\\n"
        "  - Key Mutation Findings\\n"
        "  - Key Expression Findings\\n"
        "  - Convergent Driver Genes\\n"
        "  - Pathway Insights (if available)\\n"
        "  - Evidence Ranking (if available)\\n"
        "  - Clinical Variables (if available)\\n"
        "  - Biomarker Exploration (if available)\\n"
        "  - Limitations\\n"
        "  - Research Hypotheses\\n\\n"
        + summary_text
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return {"report": response.choices[0].message.content}


# ─── LangGraph Workflow ────────────────────────────────────────────────────────
workflow = StateGraph(AgentState)

# Register all nodes
workflow.add_node("planner_node",    planner_node)
workflow.add_node("validator_node",  validator_node)
workflow.add_node("fallback_node",   fallback_node)
workflow.add_node("mutation_node",   mutation_node)
workflow.add_node("expression_node", expression_node)
workflow.add_node("integrator_node", integrator_node)
workflow.add_node("ranker_node",     ranker_node)     # NEW
workflow.add_node("clinical_node",   clinical_node)   # NEW
workflow.add_node("pathway_node",    pathway_node)    # NEW
workflow.add_node("biomarker_node",  biomarker_node)  # NEW
workflow.add_node("logger_node",     logger_node)     # NEW
workflow.add_node("synthesizer_node",synthesizer_node)

# Wire the graph
workflow.add_edge(START, "planner_node")
workflow.add_edge("planner_node", "validator_node")
workflow.add_conditional_edges(
    "validator_node",
    route_after_validation,
    {"mutation_node":  "mutation_node",
     "planner_node":   "planner_node",
     "fallback_node":  "fallback_node"}
)
workflow.add_edge("fallback_node",   "mutation_node")
workflow.add_edge("mutation_node",   "expression_node")
workflow.add_edge("expression_node", "integrator_node")
workflow.add_edge("integrator_node", "ranker_node")     # NEW: ranking always after integration
workflow.add_edge("ranker_node",     "clinical_node")   # NEW
workflow.add_edge("clinical_node",   "pathway_node")    # NEW
workflow.add_edge("pathway_node",    "biomarker_node")  # NEW
workflow.add_edge("biomarker_node",  "logger_node")     # NEW: log before synthesizing
workflow.add_edge("logger_node",     "synthesizer_node")
workflow.add_edge("synthesizer_node", END)

graph = workflow.compile()
"""

with open("agent/orchestrator.py", "w", encoding="utf-8") as f:
    f.write(orchestrator)
import os
print(f"Written: agent/orchestrator.py ({os.path.getsize('agent/orchestrator.py'):,} bytes)")
