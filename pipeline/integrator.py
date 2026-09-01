class MultiOmicsIntegrator:
    """
    Integrates mutation and expression results to find
    convergent cancer driver genes.
    """
    def __init__(self, mut_summary: dict, exp_summary: dict):
        self.mut = mut_summary
        self.exp = exp_summary

    def find_convergent_genes(self) -> dict:
        # Instead of just top 20, use top 500 genes for a meaningful overlap space
        all_mut = self.mut.get('all_mutated_genes', self.mut.get('top_10_genes', []))
        mut_genes = set(all_mut[:500])
        
        up_genes = set(self.exp.get('top_upregulated', []))
        down_genes = set(self.exp.get('top_downregulated', []))
        all_deg = up_genes | down_genes
        
        # We also want to showcase priority ones for the UI (so it doesn't get flooded)
        # So for mut_only, we just take the absolute top ones
        mut_only = [g for g in all_mut if g not in all_deg]
        
        # Sort overlapping genes by mutation frequency implicitly (since we check against sorted lists)
        return {
            'mutated_AND_upregulated': [g for g in all_mut[:500] if g in up_genes],
            'mutated_AND_downregulated': [g for g in all_mut[:500] if g in down_genes],
            'mutated_only': mut_only[:50],
            'deg_only': sorted(all_deg - mut_genes),
            'total_mutation_genes': len(mut_genes),
            'total_deg_genes': len(all_deg),
        }

    def generate_hypothesis(self, convergent: dict) -> str:
        drivers = convergent.get('mutated_AND_upregulated', [])
        if drivers:
            genes_str = ', '.join(drivers[:3])
            return (f'Genes {genes_str} exhibit both somatic mutation and '
                    f'transcriptional upregulation, suggesting active oncogenic '
                    f'driver roles and high-priority therapeutic targets.')
        return ('No direct convergence found in the top-10 lists. Consider '
                'expanding the gene lists or checking pathway-level overlap.')

    def generate_report(self) -> dict:
        conv = self.find_convergent_genes()
        return {
            'convergent_genes': conv,
            'hypothesis': self.generate_hypothesis(conv),
            'priority_targets': conv['mutated_AND_upregulated'][:5],
            'mutation_summary': self.mut,
            'expression_summary': self.exp,
        }
