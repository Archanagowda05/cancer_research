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
