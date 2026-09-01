import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class MutationAnalyzer:
    """
    Analyzes somatic mutation data from a MAF-format .txt file.
    Input: path to data_mutations.txt (from cBioPortal)
    Output: summary dict with top genes, mutation types, TMB
    """
    def __init__(self, maf_path: str):
        print(f'Loading mutation data from {maf_path}...')
        # comment='#' skips header comment lines present in MAF files
        self.maf = pd.read_csv(maf_path, sep='\t', comment='#', low_memory=False)
        print(f'Loaded {len(self.maf):,} mutations across '
              f'{self.maf["Tumor_Sample_Barcode"].nunique():,} patients')

    def get_mutation_frequency(self, top_n=20) -> pd.DataFrame:
        """Count how many DISTINCT patients have >=1 mutation in each gene."""
        freq = (
            self.maf.groupby('Hugo_Symbol')['Tumor_Sample_Barcode']
            .nunique() # unique patients, not total mutation rows
            .sort_values(ascending=False)
            .head(top_n)
            .reset_index()
        )
        freq.columns = ['Gene', 'Patient_Count']
        total_patients = self.maf['Tumor_Sample_Barcode'].nunique()
        freq['Mutation_Frequency_%'] = (freq['Patient_Count'] / total_patients * 100).round(2)
        return freq

    def get_variant_classification(self) -> pd.Series:
        """Breakdown of mutation types (missense, nonsense, frameshift, ...)."""
        return self.maf['Variant_Classification'].value_counts()

    def get_tumor_mutation_burden(self) -> pd.Series:
        """TMB = number of mutation rows per patient."""
        return self.maf.groupby('Tumor_Sample_Barcode').size().rename('TMB')

    def plot_top_genes(self, top_n=20, save_path=None):
        freq = self.get_mutation_frequency(top_n)
        fig, ax = plt.subplots(figsize=(10, 8))
        colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(freq)))
        ax.barh(freq['Gene'][::-1], freq['Mutation_Frequency_%'][::-1], color=colors[::-1])
        ax.set_xlabel('% of Patients with Mutation')
        ax.set_title(f'Top {top_n} Most Mutated Genes')
        ax.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

    def summarize(self, top_n: int = 20) -> dict:
        freq = self.get_mutation_frequency(top_n)
        tmb = self.get_tumor_mutation_burden()
        
        # Get all mutated genes sorted by frequency for deep integration
        all_freq = self.maf['Hugo_Symbol'].value_counts()
        all_genes = all_freq.index.tolist()
        
        return {
            'total_mutations': len(self.maf),
            'total_patients': self.maf['Tumor_Sample_Barcode'].nunique(),
            'unique_genes_mutated': self.maf['Hugo_Symbol'].nunique(),
            'top_10_genes': freq['Gene'].tolist(),          # integrator compat key
            'all_mutated_genes': all_genes,                 # NEW: For deep convergence
            'top_10_frequencies': freq['Mutation_Frequency_%'].tolist(),
            'top_genes': [{'gene': r['Gene'], 'freq': r['Mutation_Frequency_%'],
                           'count': int(r['Patient_Count'])}
                          for _, r in freq.iterrows()],     # richer format for UI/API
            'variant_types': self.get_variant_classification().to_dict(),
            'median_tmb': float(tmb.median().round(2)),
            'mean_tmb': float(tmb.mean().round(2)),
            'tmb_per_patient': tmb.clip(upper=100).tolist(),  # capped list for histogram
        }

if __name__ == '__main__':
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import DATA_PATHS
    
    # Needs data to run standalone
    # analyzer = MutationAnalyzer(DATA_PATHS['BRCA']['mutations'])
    # results = analyzer.summarize()
    # print('\n=== BRCA Mutation Summary ===')
    # for key, value in results.items():
    #     print(f'  {key}: {value}')
    # analyzer.plot_top_genes(save_path='data/processed/BRCA_top_genes.png')
