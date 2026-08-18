import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_PATHS = {
    'BRCA': {
        'mutations': os.path.join(BASE_DIR, 'data/raw/BRCA/data_mutations.txt'),
        'expression': os.path.join(BASE_DIR, 'data/raw/BRCA/data_mrna_seq_v2_rsem.txt'),
        'clinical': os.path.join(BASE_DIR, 'data/raw/BRCA/data_clinical_sample.txt'),
    },
    'SKCM': {
        'mutations': os.path.join(BASE_DIR, 'data/raw/SKCM/data_mutations.txt'),
        'expression': os.path.join(BASE_DIR, 'data/raw/SKCM/data_mrna_seq_v2_rsem.txt'),
        'clinical': os.path.join(BASE_DIR, 'data/raw/SKCM/data_clinical_sample.txt'),
    }
}

PROCESSED_DIR = os.path.join(BASE_DIR, 'data/processed')
os.makedirs(PROCESSED_DIR, exist_ok=True)
