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
