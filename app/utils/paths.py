from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
ART_DIR = BASE_DIR / "artifacts"
DOC_DIR = BASE_DIR / "artifacts" / "documents"
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "pdf"
WEB_DIR = DATA_DIR / "web"
