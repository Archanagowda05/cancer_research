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
        self.df = pd.read_csv(clinical_path, sep="\t", comment="#", low_memory=False)
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
