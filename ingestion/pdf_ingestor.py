from app.config import IngestionConfig
from app.utils.docs import clean_pdf_doc, save_docs
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


def ingest_pdf(file_path: Path, config: IngestionConfig):
    """
    Create and store a vector store index for the PDF file_path, along with
    the corresponding Documents and a manifest.
    """

    VS_DIR = ART_DIR / config.vector_store.type
    DOC_DIR = ART_DIR / "documents"

    loader_builder = LOADER_REGISTRY[config.pdf.loader.type]["pdf"]
    loader = loader_builder(file_path, **config.pdf.loader.params)

    docs = []
    for doc in loader.lazy_load():
        docs.append(doc)

    clean_docs = [clean_pdf_doc(doc) for doc in docs]
    art_dest_dir = f"{VS_DIR}/{file_path.stem}"
    doc_dest_dir = f"{DOC_DIR}/{file_path.stem}"

    save_docs(clean_docs, doc_dest_dir)

    manifest = {
        "vector_store": config.vector_store.type,
        "embedding_model": config.vector_store.embedding_model,
        "loader_name": config.pdf.loader.type,
        "loader_params": config.pdf.loader.params,
        "source_file": file_path.name,
        "last_indexed": datetime.now(timezone.utc).isoformat(),
    }

    embeddings = OpenAIEmbeddings(model=config.vector_store.embedding_model)
    vs_builder = VS_REGISTRY[config.vector_store.type]["create"]
    vs_builder(clean_docs, embeddings, art_dest_dir)

    with open(f"{art_dest_dir}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
        print(
            f"[pdf_ingestor] Saved {config.vector_store.type} vector store to {VS_DIR}"
        )
