from app.config import IngestionConfig
from app.utils.docs import process_pdf_docs, save_docs
from app.utils.vector_stores import VS_REGISTRY
from app.utils.loaders import LOADER_REGISTRY
import os
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from app.utils.paths import ART_DIR, DOC_DIR


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def ingest_pdf(file_path: Path, config: IngestionConfig):
    """
    Create and store a vector store index for the PDF file_path, along with
    the corresponding Documents and a manifest.
    """

    VS_DIR = ART_DIR / config.vector_store.type

    loader_builder = LOADER_REGISTRY[config.pdf.loader.type]["pdf"]
    loader = loader_builder(file_path, **config.pdf.loader.params)

    docs = []
    for doc in loader.lazy_load():
        docs.append(doc)

    processed_docs = process_pdf_docs(docs, config)
    art_dest_dir = f"{VS_DIR}/{file_path.stem}"
    doc_dest_dir = f"{DOC_DIR}/{file_path.stem}"

    manifest = {
        "vector_store": config.vector_store.type,
        "embedding_model": config.vector_store.embedding_model,
        "loader_name": config.pdf.loader.type,
        "loader_params": config.pdf.loader.params,
        "source_file": file_path.name,
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

    print(f"[pdf_ingestor] Saved {config.vector_store.type} vector store to {VS_DIR}")
    print(f"[pdf_ingestor] number of pdf docs: {len(processed_docs)}")
