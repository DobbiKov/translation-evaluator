import os

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
SOURCE_DIR = os.path.join(DATA_DIR, 'source')
LLM_TRANSLATED_DIR = os.path.join(DATA_DIR, 'llm_translated')
HUMAN_REFERENCE_DIR = os.path.join(DATA_DIR, 'human_reference') 

REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Ensure directories exist
for d in [DATA_DIR, SOURCE_DIR, LLM_TRANSLATED_DIR, HUMAN_REFERENCE_DIR, REPORTS_DIR, LOGS_DIR]:
    os.makedirs(d, exist_ok=True)

LANG_PAIRS = [
    {'source': 'fr', 'target': 'en'},
]

# Document formats to process
DOC_FORMATS = ['markdown'] 

# NL Metrics to run
RUN_BLEU = True
RUN_TER = True
RUN_BERT_SCORE = True
RUN_COMET = False 

# Structural checks to run
RUN_AST_COMPARISON = True
RUN_PATTERN_MATCHING = True # For specific elements like equations, code blocks
RUN_REF_INTEGRITY = True # Check cross-references and citations

# Rendering/Layout checks
RUN_VISUAL_DIFF = False
PDF_DPI = 300 # DPI for rendering PDFs to images

# Path to Pandoc executable (if not in PATH)
PANDOC_PATH = 'pandoc' 
