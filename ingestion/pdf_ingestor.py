from langchain_unstructured import UnstructuredLoader
from app.config import EMBEDDING_MODEL, VECTOR_STORE, LOADER_NAME, LOADER_PARAMS
from app.utils.docs import clean_pdf_doc, save_docs
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


def ingest_pdf(file_path):
    """
    Create and store a vector store index for the PDF file_path, along with
    the corresponding Documents and a manifest.
    """

    loader = UnstructuredLoader(
        file_path=file_path,
        **LOADER_PARAMS["pdf"],
    )

    docs = []
    for doc in loader.lazy_load():
        docs.append(doc)

    clean_docs = [clean_pdf_doc(doc) for doc in docs]
    art_dest_dir = f"{VS_DIR}/{file_path.stem}"
    doc_dest_dir = f"{DOC_DIR}/{file_path.stem}"

    save_docs(clean_docs, doc_dest_dir)

    manifest = {
        "embedding_model": EMBEDDING_MODEL,
        "loader_name": LOADER_NAME,
        "source_file": file_path.name,
        "last_indexed": datetime.now(timezone.utc).isoformat(),
    }
    manifest.update(LOADER_PARAMS["pdf"])

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    vector_store = FAISS.from_documents(clean_docs, embeddings)
    vector_store.save_local(art_dest_dir)

    with open(f"{art_dest_dir}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
        print(f"[pdf_ingestor] Saved FAISS index to {VS_DIR}")
