import sys, os
sys.stdout.reconfigure(encoding="utf-8")

readme = """\
# AI Multi-Omics Cancer Research Agent

An end-to-end, goal-driven AI agent for integrated multi-omics cancer data analysis.

## Project Objectives

1. To design a goal-driven AI Multi-Omics Agent for structured cancer data analysis.
2. To implement adaptive workflow orchestration for analytical coordination.
3. To automate the integration of mutation and gene expression data to find convergent driver genes.
4. To validate the framework using real-world Breast (BRCA) and Skin (SKCM) cancer datasets.

## Architecture

```
Research Goal
     |
AI Planner (Llama 3.2 via Ollama)
     |
Hybrid Validation Loop (Validator + Retry + Fallback)
     |
Execution Nodes (LangGraph orchestrated):
  Mutation Analysis -> Expression Analysis -> Multi-Omics Integration
  -> Evidence Ranking -> Clinical Analysis -> Pathway Analysis -> Biomarker Exploration
     |
Traceability Logger
     |
AI Synthesizer (Llama 3.2 via Ollama)
     |
Biological Research Report
```

## Datasets

- TCGA Breast Invasive Carcinoma (BRCA) via cBioPortal
- TCGA Skin Cutaneous Melanoma (SKCM) via cBioPortal
- Data files: `data/raw/BRCA/` and `data/raw/SKCM/`

## Setup

### 1. Install Ollama and pull the model

```bash
# Install Ollama from https://ollama.com
ollama pull llama3.2:3b
```

### 2. Create virtual environment and install dependencies

```bash
python -m venv venv
venv\\Scripts\\activate        # Windows
source venv/bin/activate      # Linux/macOS
pip install -r requirements.txt
```

### 3. Run the agent

```bash
# Default: BRCA with driver gene identification goal
python run_agent.py

# SKCM analysis
python run_agent.py --cancer_type SKCM --goal "Identify convergent driver genes in skin cancer"

# With pathway enrichment
python run_agent.py --goal "Identify convergent driver genes and investigate associated pathways"

# Full analysis with all modules
python run_agent.py --goal "Run full multi-omics analysis with clinical and biomarker exploration"

# See all options
python run_agent.py --help
```

## Outputs

All outputs are saved to `data/processed/`:

| File | Description |
|------|-------------|
| `{CT}_mutations_{ts}.png` | Top mutated genes bar chart |
| `{CT}_volcano_{ts}.png` | Differential expression volcano plot |
| `{CT}_ranking_{ts}.png` | Evidence-based gene ranking chart |
| `{CT}_clinical_{ts}.png` | Clinical variable distributions |
| `{CT}_run_log_{ts}.json` | Traceability log (goal, plan, thresholds, results) |

`{CT}` = cancer type (BRCA/SKCM), `{ts}` = Unix timestamp

## Pipeline Tools

| Tool | Type | Description |
|------|------|-------------|
| `run_mutation_analysis` | Deterministic | Mutation frequency, variant types, TMB |
| `run_expression_analysis` | Deterministic | t-test, log2FC, BH correction |
| `run_integration` | Deterministic | Convergent genes: Mutated ∩ (Up ∪ Down) |
| `run_clinical_analysis` | Deterministic | TMB/MSI/aneuploidy distributions |
| `run_pathway_analysis` | Deterministic | Enrichr KEGG+GO enrichment |
| `run_biomarker_analysis` | Deterministic | LR+RF biomarker classification |

LLM (Llama 3.2) is used ONLY for: intent parsing (Planner) and report writing (Synthesizer).

## Running Tests

```bash
pytest tests/ -v
```

## Notes

- Survival analysis (Kaplan-Meier) is not available: the clinical files do not contain OS_STATUS/OS_MONTHS columns.
- Pathway analysis requires internet access to the Enrichr API.
- Biomarker analysis requires scikit-learn and sufficient class balance.
- All modules degrade gracefully when data or dependencies are unavailable.
"""

requirements = """\
# Core data science
pandas>=1.5.0
numpy>=1.23.0
scipy>=1.9.0
matplotlib>=3.6.0

# Machine learning (optional - for biomarker module)
scikit-learn>=1.1.0

# AI / LLM / Agent
openai>=1.0.0
langgraph>=0.1.0

# Testing
pytest>=7.0.0
"""

files = {
    "README.md":        readme,
    "requirements.txt": requirements,
}
for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {path} ({os.path.getsize(path):,} bytes)")

print("Documentation written.")
