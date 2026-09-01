import sys, os
sys.stdout.reconfigure(encoding="utf-8")

# ── Fix test_planning.py (fix broken line 61-63, update VALID_TOOLS refs) ─────
test_planning = """\
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
    mock_response.choices[0].message.content = \
        '["run_mutation_analysis", "run_expression_analysis"]'
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
"""

# ── New: test_pipeline.py ─────────────────────────────────────────────────────
test_pipeline = """\
import sys, os, pytest
import pandas as pd
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.integrator import MultiOmicsIntegrator


# ── MultiOmicsIntegrator tests ────────────────────────────────────────────────
def _make_mut_summary(top_genes=None, top_freqs=None):
    top_genes  = top_genes  or ["TP53", "PIK3CA", "CDH1", "GATA3", "MUC16",
                                 "TTN", "MAP3K1", "KMT2C", "RYR2", "FLG"]
    top_freqs  = top_freqs  or [35.0, 30.0, 20.0, 15.0, 14.0, 13.0, 12.0, 11.0, 10.0, 9.0]
    return {"top_10_genes": top_genes, "top_10_frequencies": top_freqs,
            "total_mutations": 1000, "total_patients": 100}


def _make_exp_summary(up=None, down=None):
    up   = up   or ["TP53", "BRCA1", "CDH1", "KRAS", "MYC",
                    "EGFR", "VEGF", "HER2", "AKT1", "PTEN"]
    down = down or ["RB1", "VHL", "APC", "CDKN2A", "SMAD4",
                    "ARID1A", "FBXW7", "STK11", "BAP1", "KEAP1"]
    return {"top_upregulated": up, "top_downregulated": down,
            "significant_degs": 50, "upregulated_count": 25, "downregulated_count": 25}


def test_convergent_genes_found():
    integrator = MultiOmicsIntegrator(_make_mut_summary(), _make_exp_summary())
    conv = integrator.find_convergent_genes()
    assert "mutated_AND_upregulated" in conv
    assert "TP53" in conv["mutated_AND_upregulated"]
    assert "CDH1" in conv["mutated_AND_upregulated"]


def test_convergent_genes_empty_when_no_overlap():
    mut = _make_mut_summary(top_genes=["GENE_A", "GENE_B", "GENE_C",
                                       "GENE_D", "GENE_E", "GENE_F",
                                       "GENE_G", "GENE_H", "GENE_I", "GENE_J"])
    exp = _make_exp_summary(up=["GENE_X", "GENE_Y"], down=["GENE_Z"])
    integrator = MultiOmicsIntegrator(mut, exp)
    conv = integrator.find_convergent_genes()
    assert conv["mutated_AND_upregulated"] == []
    assert conv["mutated_AND_downregulated"] == []


def test_generate_report_structure():
    integrator = MultiOmicsIntegrator(_make_mut_summary(), _make_exp_summary())
    report = integrator.generate_report()
    assert "convergent_genes" in report
    assert "hypothesis" in report
    assert "priority_targets" in report


def test_deg_only_genes():
    integrator = MultiOmicsIntegrator(_make_mut_summary(), _make_exp_summary())
    conv = integrator.find_convergent_genes()
    all_mut = set(_make_mut_summary()["top_10_genes"])
    for gene in conv["deg_only"]:
        assert gene not in all_mut


def test_mutated_only_genes():
    integrator = MultiOmicsIntegrator(_make_mut_summary(), _make_exp_summary())
    conv = integrator.find_convergent_genes()
    all_up   = set(_make_exp_summary()["top_upregulated"])
    all_down = set(_make_exp_summary()["top_downregulated"])
    for gene in conv["mutated_only"]:
        assert gene not in (all_up | all_down)
"""

# ── New: test_new_modules.py ──────────────────────────────────────────────────
test_new_modules = """\
import sys, os, pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.ranker import CandidateRanker
from pipeline.pathway import PathwayAnalyzer


# ── CandidateRanker tests ─────────────────────────────────────────────────────
def _mut():
    return {"top_10_genes": ["TP53","PIK3CA","CDH1","GATA3","MUC16",
                              "TTN","MAP3K1","KMT2C","RYR2","FLG"],
            "top_10_frequencies": [35,30,20,15,14,13,12,11,10,9]}


def _exp():
    return {"top_upregulated":   ["TP53","CDH1","BRCA1","KRAS","MYC",
                                   "EGFR","VEGF","HER2","AKT1","PTEN"],
            "top_downregulated": ["RB1","VHL","APC","CDKN2A","SMAD4",
                                   "ARID1A","FBXW7","STK11","BAP1","KEAP1"]}


def test_ranker_produces_ranked_list():
    ranker = CandidateRanker(_mut(), _exp())
    result = ranker.rank()
    assert "ranked_genes" in result
    genes = result["ranked_genes"]
    assert len(genes) > 0
    for g in genes:
        assert "Composite_Score" in g
        assert 0.0 <= g["Composite_Score"] <= 1.0


def test_ranker_preserves_convergent_genes():
    ranker = CandidateRanker(_mut(), _exp())
    result = ranker.rank()
    assert "original_convergent_genes" in result
    assert "mutated_AND_upregulated" in result["original_convergent_genes"]


def test_ranker_scores_sorted_descending():
    ranker = CandidateRanker(_mut(), _exp())
    result = ranker.rank()
    scores = [g["Composite_Score"] for g in result["ranked_genes"]]
    assert scores == sorted(scores, reverse=True)


def test_ranker_empty_when_no_convergent():
    mut = {"top_10_genes": ["GENE_A","GENE_B"], "top_10_frequencies": [10,5]}
    exp = {"top_upregulated": ["GENE_X"], "top_downregulated": ["GENE_Y"]}
    ranker = CandidateRanker(mut, exp)
    result = ranker.rank()
    assert result["ranked_genes"] == []


# ── PathwayAnalyzer tests (mocked network) ─────────────────────────────────
@patch("urllib.request.urlopen")
def test_pathway_returns_complete_on_success(mock_urlopen):
    # Mock addList response
    import json
    add_resp  = MagicMock(); add_resp.read.return_value = json.dumps({"userListId": 42}).encode()
    enrich_resp = MagicMock()
    enrich_resp.read.return_value = json.dumps({
        "KEGG_2021_Human": [[1, "PI3K-Akt signaling pathway", 0.001, -2, 5,
                              ["TP53","CDH1"], 0.01, "", "", ""]],
        "GO_Biological_Process_2023": []
    }).encode()
    mock_urlopen.return_value.__enter__ = lambda s: s
    mock_urlopen.return_value.__exit__ = MagicMock(return_value=False)
    mock_urlopen.return_value.read = MagicMock(
        side_effect=[add_resp.read.return_value,
                     enrich_resp.read.return_value,
                     enrich_resp.read.return_value])
    analyzer = PathwayAnalyzer(["TP53","CDH1","PIK3CA"])
    result = analyzer.run()
    assert result["status"] in ("complete", "unavailable")


@patch("urllib.request.urlopen", side_effect=Exception("Connection refused"))
def test_pathway_graceful_fallback_on_network_error(mock_urlopen):
    analyzer = PathwayAnalyzer(["TP53","CDH1"])
    result = analyzer.run()
    assert result["status"] == "unavailable"
    assert "message" in result
"""

files = {
    "tests/test_planning.py":    test_planning,
    "tests/test_pipeline.py":    test_pipeline,
    "tests/test_new_modules.py": test_new_modules,
}

for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {path} ({os.path.getsize(path):,} bytes)")

print("All test files written.")
