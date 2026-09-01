import json, urllib.request, urllib.parse, urllib.error, time, warnings
warnings.filterwarnings("ignore")


import requests

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
        genes_str = "\n".join(self.genes)
        payload = {'list': (None, genes_str), 'description': (None, 'MultiOmicsAgentGeneList')}
        try:
            res = requests.post(f"{self.ENRICHR_BASE}/addList", files=payload, timeout=self.TIMEOUT)
            res.raise_for_status()
            return str(res.json()["userListId"])
        except Exception as e:
            print(f"[PathwayAnalyzer] WARNING: submit failed: {e}")
            return None

    def _get_enrichment(self, list_id, library):
        url = f"{self.ENRICHR_BASE}/enrich?userListId={list_id}&backgroundType={library}"
        try:
            res = requests.get(url, timeout=self.TIMEOUT)
            res.raise_for_status()
            terms = res.json().get(library, [])
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
