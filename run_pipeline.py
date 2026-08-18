import sys
import os
from pipeline.mutation import MutationAnalyzer
from pipeline.expression import ExpressionAnalyzer
from pipeline.integrator import MultiOmicsIntegrator
from config import DATA_PATHS

def main():
    print("=== Testing Breast Cancer (BRCA) Pipeline ===")
    
    # 1. Mutation Analysis
    print("\nStep 1: Running Mutation Analysis...")
    mut_analyzer = MutationAnalyzer(DATA_PATHS['BRCA']['mutations'])
    mut_summary = mut_analyzer.summarize()
    print(f"-> Top mutated gene: {mut_summary['top_10_genes'][0]} ({mut_summary['top_10_frequencies'][0]}%)")
    
    # 2. Expression Analysis
    print("\nStep 2: Running Expression Analysis...")
    exp_analyzer = ExpressionAnalyzer(DATA_PATHS['BRCA']['expression'])
    results_df = exp_analyzer.run_differential_expression(top_n=500)
    exp_summary = exp_analyzer.summarize(results_df)
    print(f"-> Top upregulated gene: {exp_summary['top_upregulated'][0]}")
    
    # 3. Integration
    print("\nStep 3: Running Multi-Omics Integration...")
    integrator = MultiOmicsIntegrator(mut_summary, exp_summary)
    report = integrator.generate_report()
    
    print("\n=== Final Biological Hypothesis ===")
    print(report['hypothesis'])

if __name__ == "__main__":
    main()
