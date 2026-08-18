class MultiOmicsIntegrator:
    """
    Integrates mutation and expression results to find
    convergent cancer driver genes.
    """
    def __init__(self, mut_summary: dict, exp_summary: dict):
        self.mut = mut_summary
        self.exp = exp_summary

    def find_convergent_genes(self) -> dict:
        mut_genes = set(self.mut.get('top_10_genes', []))
        up_genes = set(self.exp.get('top_upregulated', []))
        down_genes = set(self.exp.get('top_downregulated', []))
        all_deg = up_genes | down_genes
        return {
            'mutated_AND_upregulated': sorted(mut_genes & up_genes),
            'mutated_AND_downregulated': sorted(mut_genes & down_genes),
            'mutated_only': sorted(mut_genes - all_deg),
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
