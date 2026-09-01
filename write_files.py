import sys, os
sys.stdout.reconfigure(encoding="utf-8")

# ── FILE 1: pipeline/clinical.py ─────────────────────────────────────────────
clinical = """\
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")


class ClinicalAnalyzer:
    SURVIVAL_COLS = {"OS_STATUS", "OS_MONTHS", "DFS_STATUS", "DFS_MONTHS"}
    CONTINUOUS_COLS = ["TMB_NONSYNONYMOUS", "ANEUPLOIDY_SCORE",
                       "MSI_SENSOR_SCORE", "MSI_SCORE_MANTIS"]
    CATEGORICAL_COLS = ["GRADE", "SAMPLE_TYPE", "TUMOR_TYPE"]

    def __init__(self, clinical_path: str):
        print(f"Loading clinical data from {clinical_path}...")
        self.df = pd.read_csv(clinical_path, sep="\\t", comment="#", low_memory=False)
        print(f"Loaded {len(self.df):,} clinical records, {len(self.df.columns)} columns")
        self._available_cols = set(self.df.columns)

    def check_survival_data(self) -> dict:
        found = self._available_cols & self.SURVIVAL_COLS
        if found:
            return {"available": True, "columns": sorted(found)}
        return {"available": False, "message": (
            "Survival columns (OS_STATUS, OS_MONTHS) are not present in this dataset. "
            "Kaplan-Meier / log-rank survival analysis cannot be performed on the available data."
        )}

    def summarise_continuous(self) -> dict:
        result = {}
        for col in self.CONTINUOUS_COLS:
            if col in self._available_cols:
                s = pd.to_numeric(self.df[col], errors="coerce").dropna()
                if len(s) > 0:
                    result[col] = {"n": int(len(s)), "mean": round(float(s.mean()), 4),
                                   "median": round(float(s.median()), 4), "std": round(float(s.std()), 4),
                                   "min": round(float(s.min()), 4), "max": round(float(s.max()), 4)}
        return result

    def summarise_categorical(self) -> dict:
        result = {}
        for col in self.CATEGORICAL_COLS:
            if col in self._available_cols:
                result[col] = self.df[col].value_counts(dropna=False).to_dict()
        return result

    def plot_distributions(self, save_path: str = None):
        available = [c for c in self.CONTINUOUS_COLS if c in self._available_cols]
        if not available:
            return
        n = len(available)
        fig, axes = plt.subplots(1, n, figsize=(5 * n, 4))
        if n == 1:
            axes = [axes]
        for ax, col in zip(axes, available):
            s = pd.to_numeric(self.df[col], errors="coerce").dropna()
            ax.hist(s, bins=40, color="#5B86E5", edgecolor="white", alpha=0.85)
            ax.set_title(col.replace("_", " "), fontsize=11)
            ax.set_xlabel("Value"); ax.set_ylabel("Count")
            ax.axvline(s.median(), color="#E53E3E", linestyle="--", linewidth=1.5,
                       label=f"Median={s.median():.1f}")
            ax.legend(fontsize=8)
        plt.suptitle("Clinical Variable Distributions", fontsize=13, fontweight="bold")
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

    def summarise(self) -> dict:
        return {"total_samples": len(self.df),
                "survival_status": self.check_survival_data(),
                "continuous_variables": self.summarise_continuous(),
                "categorical_variables": self.summarise_categorical()}
"""

# ── FILE 2: pipeline/pathway.py ──────────────────────────────────────────────
pathway = """\
import json, urllib.request, urllib.parse, urllib.error, time, warnings
warnings.filterwarnings("ignore")


class PathwayAnalyzer:
    ENRICHR_BASE = "https://maayanlab.cloud/Enrichr"
    LIBRARIES = ["KEGG_2021_Human", "GO_Biological_Process_2023"]
    TIMEOUT = 15

    def __init__(self, gene_list: list):
        self.genes = [g for g in gene_list if isinstance(g, str) and g.strip()]
        print(f"[PathwayAnalyzer] {len(self.genes)} genes received.")

    def _add_list(self):
        if not self.genes:
            return None
        payload = urllib.parse.urlencode(
            {"list": "\\n".join(self.genes), "description": "MultiOmicsAgentGeneList"}
        ).encode()
        try:
            req = urllib.request.Request(f"{self.ENRICHR_BASE}/addList",
                                         data=payload, method="POST")
            with urllib.request.urlopen(req, timeout=self.TIMEOUT) as r:
                return str(json.loads(r.read())["userListId"])
        except Exception as e:
            print(f"[PathwayAnalyzer] WARNING: submit failed: {e}")
            return None

    def _get_enrichment(self, list_id, library):
        url = f"{self.ENRICHR_BASE}/enrich?userListId={list_id}&backgroundType={library}"
        try:
            with urllib.request.urlopen(url, timeout=self.TIMEOUT) as r:
                terms = json.loads(r.read()).get(library, [])
                return [{"term": t[1], "pvalue": round(float(t[2]), 6),
                         "adjusted_pvalue": round(float(t[6]), 6),
                         "overlap_genes": t[5] if isinstance(t[5], list) else []}
                        for t in terms[:10] if len(t) >= 7 and float(t[6]) < 0.05]
        except Exception as e:
            print(f"[PathwayAnalyzer] WARNING: {library} failed: {e}")
            return []

    def run(self) -> dict:
        print("[PathwayAnalyzer] Submitting to Enrichr...")
        lid = self._add_list()
        if lid is None:
            return {"status": "unavailable",
                    "message": "Enrichr API unreachable. Pathway analysis skipped.",
                    "results": {}}
        time.sleep(0.5)
        enrichment = {}
        for lib in self.LIBRARIES:
            print(f"  Querying {lib}...")
            terms = self._get_enrichment(lid, lib)
            enrichment[lib] = terms if terms else "No significant enrichment found (adj.p < 0.05)"
        top5 = {lib: [t["term"] for t in v[:5]] if isinstance(v, list) else v
                for lib, v in enrichment.items()}
        print("[PathwayAnalyzer] Done.")
        return {"status": "complete", "genes_submitted": self.genes,
                "results": enrichment, "top_5_terms": top5}
"""

# ── FILE 3: pipeline/ranker.py ───────────────────────────────────────────────
ranker = """\
import numpy as np, pandas as pd, warnings
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
warnings.filterwarnings("ignore")


class CandidateRanker:
    def __init__(self, mut_summary: dict, exp_summary: dict, pathway_result: dict = None):
        self.mut = mut_summary
        self.exp = exp_summary
        self.pathway = pathway_result or {}

    def _mut_scores(self, genes):
        g2f = dict(zip(self.mut.get("top_10_genes", []), self.mut.get("top_10_frequencies", [])))
        return {g: g2f.get(g, 0.0) for g in genes}

    def _exp_scores(self, genes):
        up, dn = self.exp.get("top_upregulated", []), self.exp.get("top_downregulated", [])
        n = max(len(up), len(dn), 1)
        return {g: (n - up.index(g)) / n if g in up
                else (n - dn.index(g)) / n if g in dn
                else 0.0 for g in genes}

    def _path_scores(self, genes):
        s = {g: 0 for g in genes}
        if self.pathway.get("status") != "complete":
            return s
        for terms in self.pathway.get("results", {}).values():
            if not isinstance(terms, list):
                continue
            for t in terms:
                for gene in t.get("overlap_genes", []):
                    if gene in s:
                        s[gene] += 1
        return s

    @staticmethod
    def _norm(d):
        if not d: return d
        lo, hi = min(d.values()), max(d.values())
        if hi == lo: return {k: 1.0 for k in d}
        return {k: (v - lo) / (hi - lo) for k, v in d.items()}

    def rank(self) -> dict:
        from pipeline.integrator import MultiOmicsIntegrator
        conv = MultiOmicsIntegrator(self.mut, self.exp).find_convergent_genes()
        candidates = sorted(
            set(conv.get("mutated_AND_upregulated", []))
            | set(conv.get("mutated_AND_downregulated", []))
        )
        if not candidates:
            print("[CandidateRanker] No convergent genes to rank.")
            return {"ranked_genes": [], "note": "No convergent genes found.",
                    "original_convergent_genes": conv}
        print(f"[CandidateRanker] Ranking {len(candidates)} gene(s)...")
        mn = self._norm(self._mut_scores(candidates))
        en = self._norm(self._exp_scores(candidates))
        pn = self._norm(self._path_scores(candidates))
        mr = self._mut_scores(candidates)
        pr = self._path_scores(candidates)
        rows = [{"Gene": g, "Mutation_Score": round(mn[g], 4),
                 "Expression_Score": round(en[g], 4), "Pathway_Score": round(pn[g], 4),
                 "Composite_Score": round(np.mean([mn[g], en[g], pn[g]]), 4),
                 "Mutation_Freq_%": round(mr[g], 2), "Pathway_Hits": pr[g]}
                for g in candidates]
        df = pd.DataFrame(rows).sort_values("Composite_Score", ascending=False)
        return {"ranked_genes": df.to_dict(orient="records"),
                "top_candidate": df.iloc[0]["Gene"] if len(df) else None,
                "scoring_methodology": (
                    "Composite = mean(Mutation, Expression, Pathway scores), "
                    "each min-max normalised to [0,1]. Original convergent gene "
                    "logic (Mutated cap DEG) is preserved alongside this ranking."
                ),
                "original_convergent_genes": conv}

    def plot_ranking(self, ranking_result: dict, save_path: str = None):
        rows = ranking_result.get("ranked_genes", [])
        if not rows: return
        df = pd.DataFrame(rows)
        genes, x, w = df["Gene"].tolist(), np.arange(len(df)), 0.25
        fig, ax = plt.subplots(figsize=(max(8, len(genes) * 1.5), 5))
        ax.bar(x - w, df["Mutation_Score"],   w, label="Mutation",   color="#5B86E5")
        ax.bar(x,     df["Expression_Score"], w, label="Expression", color="#E53E3E")
        ax.bar(x + w, df["Pathway_Score"],    w, label="Pathway",    color="#38A169")
        ax.set_xticks(x); ax.set_xticklabels(genes, rotation=30, ha="right")
        ax.set_ylabel("Normalised Score (0-1)")
        ax.set_title("Evidence-Based Gene Candidate Ranking")
        ax.legend(); ax.set_ylim(0, 1.15)
        plt.tight_layout()
        if save_path: plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
"""

# ── FILE 4: pipeline/biomarker.py ────────────────────────────────────────────
biomarker = """\
import numpy as np, warnings
warnings.filterwarnings("ignore")
try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import StratifiedKFold, cross_validate
    from sklearn.preprocessing import StandardScaler
    _SK = True
except ImportError:
    _SK = False


class BiomarkerExplorer:
    DISCLAIMER = (
        "RESEARCH DISCLAIMER: This module performs research-level biomarker "
        "exploration only. No clinical diagnostic capability is claimed or implied. "
        "Results must not be used for clinical decision-making."
    )
    MIN_PER_CLASS = 20
    MAX_RATIO = 5.0

    def __init__(self, expression_log_df, clinical_df):
        self.expr = expression_log_df
        self.clinical = clinical_df

    def _guard(self):
        if not _SK:
            return False, "scikit-learn not installed. Run: pip install scikit-learn"
        if self.expr is None or self.expr.empty:
            return False, "Expression data not provided."
        if "SAMPLE_TYPE" not in self.clinical.columns:
            return False, "SAMPLE_TYPE column not found in clinical data."
        labels = self.clinical.set_index("SAMPLE_ID")["SAMPLE_TYPE"]
        n_p = int((labels == "Primary").sum())
        n_m = int(labels.str.contains("Metastasis", na=False).sum())
        if n_p < self.MIN_PER_CLASS:
            return False, f"Insufficient Primary samples ({n_p} < {self.MIN_PER_CLASS})."
        if n_m < self.MIN_PER_CLASS:
            return False, f"Insufficient Metastasis samples ({n_m} < {self.MIN_PER_CLASS})."
        ratio = max(n_p, n_m) / max(min(n_p, n_m), 1)
        if ratio > self.MAX_RATIO:
            return False, f"Class imbalance too high ({ratio:.1f}:1). Analysis skipped."
        return True, "ok"

    def _prepare(self):
        labels = self.clinical.set_index("SAMPLE_ID")["SAMPLE_TYPE"]
        p = [s for s in labels[labels == "Primary"].index if s in self.expr.columns]
        m = [s for s in labels[labels.str.contains("Metastasis", na=False)].index
             if s in self.expr.columns]
        sel = p + m
        y = np.array([0]*len(p) + [1]*len(m))
        top = self.expr[sel].var(axis=1).nlargest(200).index
        return self.expr.loc[top, sel].T.values, y, len(p), len(m)

    @staticmethod
    def _cv(model, X, y):
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        sc = cross_validate(model, X, y, cv=cv,
                            scoring=["accuracy","precision_macro","recall_macro",
                                     "f1_macro","roc_auc"],
                            error_score="raise")
        return {k.replace("test_","").replace("_macro",""): round(sc[f"test_{k.replace('test_','')}"].mean(), 4)
                for k in ["accuracy","precision_macro","recall_macro","f1_macro","roc_auc"]}

    def run(self) -> dict:
        print("[BiomarkerExplorer] Checking feasibility...")
        ok, msg = self._guard()
        if not ok:
            print(f"  -> {msg}")
            return {"status": "skipped", "reason": msg, "disclaimer": self.DISCLAIMER}
        print("[BiomarkerExplorer] Preparing data...")
        X, y, np_, nm = self._prepare()
        if len(np.unique(y)) < 2:
            return {"status": "skipped", "reason": "Only one class after alignment.",
                    "disclaimer": self.DISCLAIMER}
        Xs = StandardScaler().fit_transform(X)
        print("[BiomarkerExplorer] Logistic Regression (5-fold CV)...")
        lr_m = self._cv(LogisticRegression(max_iter=1000, random_state=42), Xs, y)
        print("[BiomarkerExplorer] Random Forest (5-fold CV)...")
        rf_m = self._cv(RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1), X, y)
        print("[BiomarkerExplorer] Done.")
        return {"status": "complete",
                "task": "Binary classification: Primary (0) vs Metastasis (1)",
                "sample_counts": {"primary": np_, "metastasis": nm},
                "features": "Top 200 most variable log2-RSEM genes",
                "validation": "5-fold stratified cross-validation",
                "logistic_regression": lr_m, "random_forest": rf_m,
                "disclaimer": self.DISCLAIMER}
"""

files = {
    "pipeline/clinical.py":   clinical,
    "pipeline/pathway.py":    pathway,
    "pipeline/ranker.py":     ranker,
    "pipeline/biomarker.py":  biomarker,
}

for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {path} ({os.path.getsize(path):,} bytes)")

print("All 4 pipeline modules written successfully.")
