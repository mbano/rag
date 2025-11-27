from app.config import IngestionConfig
from app.utils.docs import process_web_docs, save_docs
from app.utils.urls import url_to_resource_name
from app.utils.vector_stores import VS_REGISTRY
from app.utils.loaders import LOADER_REGISTRY
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from app.utils.paths import ART_DIR, DOC_DIR

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def ingest_web(url, config: IngestionConfig):
    """
    Create and store a vector store index for the web page at url, along with
    the corresponding Documents and a manifest.
    """

    VS_DIR = ART_DIR / config.vector_store.type

    loader_builder = LOADER_REGISTRY[config.web.loader.type]["web"]
    loader = loader_builder(url, **config.web.loader.params)

    docs = []
    for doc in loader.lazy_load():
        docs.append(doc)

    processed_docs = process_web_docs(docs, config)

    resource_name = url_to_resource_name(url)
    art_dest_dir = f"{VS_DIR}/{resource_name}"
    doc_dest_dir = f"{DOC_DIR}/{resource_name}"

    manifest = {
        "vector_store": config.vector_store.type,
        "embedding_model": config.vector_store.embedding_model,
        "loader_name": config.web.loader.type,
        "loader_params": config.web.loader.params,
        "source_url": url,
        "last_indexed": datetime.now(timezone.utc).isoformat(),
    }

    save_docs(
        processed_docs,
        manifest,
        config.vector_store,
        doc_save_dir=doc_dest_dir,
        manifest_save_dir=art_dest_dir,
    )

    vs_builder = VS_REGISTRY[config.vector_store.type]["create"]
    vs_builder(processed_docs, config.vector_store, save_dir=art_dest_dir)

    print(f"[web_ingestor] Saved {config.vector_store.type} vector store to {VS_DIR}")
    print(f"[web_ingestor] number of web docs: {len(processed_docs)}")
