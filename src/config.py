import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BUREAU_REPORTS_DIR = DATA_DIR / "Bureau_Reports"
GST_RETURNS_DIR = DATA_DIR / "GST_3B_Returns"
EXCEL_PARAM_FILE = DATA_DIR / "Bureau parameters - Report.xlsx"

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
LLM_MODEL_NAME = "mistral"
LLM_PROVIDER = "ollama"

CHROMA_PERSIST_DIR = BASE_DIR / "chroma_db"
