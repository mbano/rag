from pathlib import Path
from langchain_core.documents import Document
from app.utils.vector_stores import VS_REGISTRY
from app.config import get_settings
from langchain_openai import OpenAIEmbeddings
import json


PROJECT_ROOT = Path(__file__).parents[1]
DOC_DIR = PROJECT_ROOT / "artifacts" / "documents"

docs = []

for dir in DOC_DIR.iterdir():
    with open(dir / "documents.jsonl", "r") as f:
        for line in f:
            doc_dir = json.loads(line)
            doc = Document(**doc_dir)
            docs.append(doc)

config = get_settings().rag.vector_stores["opensearch"]
embeddings = OpenAIEmbeddings(model=config.embedding_model)
opensearch_vs = VS_REGISTRY["opensearch"]["create"]
opensearch_vs(docs, embeddings, config)
