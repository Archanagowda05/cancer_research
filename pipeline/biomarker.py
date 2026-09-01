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
