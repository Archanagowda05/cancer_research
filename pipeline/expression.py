import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

class ExpressionAnalyzer:
    """
    Differential Gene Expression analysis on TCGA RNA-seq data.
    Uses a median-split strategy since most public TCGA datasets
    lack matched normal samples.
    """
    def __init__(self, expression_path: str):
        raw = pd.read_csv(expression_path, sep='\t', index_col=0)
        # Fix: Drop duplicate gene symbols which cause 2D arrays and crash the t-test
        raw = raw[~raw.index.duplicated(keep='first')]
        self.expr = raw.apply(pd.to_numeric, errors='coerce').dropna(how='all')
        self.expr_log = np.log2(self.expr + 1) # standard RNA-seq variance stabilization
        print(f'Loaded {len(self.expr):,} genes x {self.expr.shape[1]:,} samples')

    def run_differential_expression(self, top_n=500) -> pd.DataFrame:
        # Work on the most variable genes for speed
        gene_var = self.expr_log.var(axis=1).sort_values(ascending=False)
        subset = self.expr_log.loc[gene_var.head(top_n).index]

        sample_means = subset.mean(axis=0)
        high_samples = sample_means[sample_means >= sample_means.median()].index
        low_samples = sample_means[sample_means < sample_means.median()].index

        results = []
        for gene in subset.index:
            high_vals = subset.loc[gene, high_samples].dropna()
            low_vals = subset.loc[gene, low_samples].dropna()
            if len(high_vals) < 3 or len(low_vals) < 3:
                continue
            t_stat, p_val = stats.ttest_ind(high_vals, low_vals)
            lfc = high_vals.mean() - low_vals.mean()
            results.append({'Gene': gene, 'log2FoldChange': lfc, 'pvalue': p_val})

        df = pd.DataFrame(results).sort_values('pvalue')
        n = len(df)
        # Benjamini-Hochberg style adjustment for multiple testing
        df['padj'] = (df['pvalue'] * n / (df.reset_index().index + 1)).clip(upper=1.0)
        df['significant'] = (df['padj'] < 0.05) & (df['log2FoldChange'].abs() > 1.0)
        return df.sort_values('padj')

    def get_top_degs(self, results_df, direction='up', n=20) -> list:
        sig = results_df[results_df['significant']]
        if direction == 'up':
            return sig.nlargest(n, 'log2FoldChange')['Gene'].tolist()
        return sig.nsmallest(n, 'log2FoldChange')['Gene'].tolist()

    def plot_volcano(self, results_df, save_path=None):
        fig, ax = plt.subplots(figsize=(10, 7))
        colors = results_df['significant'].map({True: '#E53E3E', False: '#A0AEC0'})
        ax.scatter(results_df['log2FoldChange'],
                   -np.log10(results_df['pvalue'].clip(lower=1e-300)),
                   c=colors, alpha=0.6, s=15, linewidths=0)
        ax.axvline(1.0, color='gray', linestyle='--', alpha=0.5)
        ax.axvline(-1.0, color='gray', linestyle='--', alpha=0.5)
        ax.axhline(-np.log10(0.05), color='gray', linestyle='--', alpha=0.5)
        ax.set_xlabel('log2 Fold Change')
        ax.set_ylabel('-log10(p-value)')
        ax.set_title('Volcano Plot - Differential Gene Expression')
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

    def summarize(self, results_df) -> dict:
        sig = results_df[results_df['significant']]
        return {
            'total_genes_tested': len(results_df),
            'significant_degs': len(sig),
            'upregulated_count': int((sig['log2FoldChange'] > 0).sum()),
            'downregulated_count': int((sig['log2FoldChange'] < 0).sum()),
            'top_upregulated': self.get_top_degs(results_df, 'up', 10),
            'top_downregulated': self.get_top_degs(results_df, 'down', 10),
        }
