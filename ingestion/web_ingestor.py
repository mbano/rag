from langchain_unstructured import UnstructuredLoader
from app.utils.docs import filter_web_docs, clean_web_doc, save_docs
from app.utils.urls import url_to_resource_name
from app.config import EMBEDDING_MODEL, VECTOR_STORE, LOADER_NAME
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

BASE_DIR = Path(__file__).resolve().parents[1]
ART_DIR = BASE_DIR / "artifacts"
VS_DIR = ART_DIR / VECTOR_STORE
DOC_DIR = ART_DIR / "documents"


def ingest_web(url, mode: str):
    """
    Create and store a vector store index for the web page at url, along with
    the corresponding Documents and a manifest.
    """

    loader = UnstructuredLoader(
        web_url=url,
    )

    docs = []
    for doc in loader.lazy_load():
        docs.append(doc)

    filtered_docs = filter_web_docs(docs)
    clean_docs = [clean_web_doc(doc) for doc in filtered_docs]

    resource_name = url_to_resource_name(url)
    art_dest_dir = f"{VS_DIR}/{resource_name}"
    doc_dest_dir = f"{DOC_DIR}/{resource_name}"

    save_docs(clean_docs, doc_dest_dir)

    manifest = {
        "embedding_model": EMBEDDING_MODEL,
        "loader_name": LOADER_NAME,
        "source_url": url,
        "last_indexed": datetime.now(timezone.utc).isoformat(),
    }

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    vector_store = FAISS.from_documents(clean_docs, embeddings)
    vector_store.save_local(art_dest_dir)

    with open(f"{art_dest_dir}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
        print(f"[web_ingestor] Saved FAISS index to {VS_DIR}")
