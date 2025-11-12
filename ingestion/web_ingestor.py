from app.config import IngestionConfig, load_ingestion_config
from app.utils.docs import filter_web_docs, clean_web_doc, save_docs
from app.utils.urls import url_to_resource_name
from app.utils.vector_stores import VS_REGISTRY
from app.utils.loaders import LOADER_REGISTRY
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

BASE_DIR = Path(__file__).resolve().parents[1]
ART_DIR = BASE_DIR / "artifacts"
cfg = load_ingestion_config()
VS_DIR = ART_DIR / cfg.vector_store.type
DOC_DIR = ART_DIR / "documents"


def ingest_web(url, config: IngestionConfig):
    """
    Create and store a vector store index for the web page at url, along with
    the corresponding Documents and a manifest.
    """

    loader_builder = LOADER_REGISTRY[config.web.loader.type]["web"]
    loader = loader_builder(url, **config.web.loader.params)

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
        "vector_store": config.vector_store.type,
        "embedding_model": config.vector_store.embedding_model,
        "loader_name": config.web.loader.type,
        "loader_params": config.web.loader.params,
        "source_url": url,
        "last_indexed": datetime.now(timezone.utc).isoformat(),
    }

    embeddings = OpenAIEmbeddings(model=config.vector_store.embedding_model)
    vs_builder = VS_REGISTRY[config.vector_store.type]["create"]
    vs_builder(clean_docs, embeddings, art_dest_dir)

    with open(f"{art_dest_dir}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
        print(
            f"[web_ingestor] Saved {config.vector_store.type} vector store to {VS_DIR}"
        )
