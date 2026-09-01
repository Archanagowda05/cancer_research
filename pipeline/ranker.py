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
