from langchain_core.documents import Document
from app.utils.vector_stores import VS_REGISTRY
from app.config import get_settings
from app.utils.paths import DOC_DIR
from langchain_openai import OpenAIEmbeddings
import json


docs = []

i = 0

for dir in DOC_DIR.iterdir():
    with open(dir / "documents.jsonl", "r") as f:
        for line in f:
            doc_dir = json.loads(line)
            doc = Document(**doc_dir)
            docs.append(doc)
            i += 1

config = get_settings().rag.vector_stores["opensearch"]
embeddings = OpenAIEmbeddings(model=config.embedding_model)
opensearch_vs = VS_REGISTRY["opensearch"]["create"]
opensearch_vs(docs, config)
print(f"Loaded {i} documents into opensearch")
