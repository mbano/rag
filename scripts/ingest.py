from langchain_unstructured import UnstructuredLoader
from pathlib import Path
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import json
import os
from app.config import EMBEDDING_MODEL, VECTOR_STORE, LOADER_NAME, LOADER_PARAMS
from datetime import datetime, timezone

# local fallback
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "pdf"
ART_DIR = BASE_DIR / "artifacts" / VECTOR_STORE


def ingest(file_path):

    dest_dir = f"{ART_DIR}/{file_path.stem}"

    loader = UnstructuredLoader(
        file_path=file_path,
        **LOADER_PARAMS,
    )

    docs = []

    for doc in loader.lazy_load():
        docs.append(doc)

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    vector_store = FAISS.from_documents(docs, embeddings)
    vector_store.save_local(dest_dir)

    #  manifest
    manifest = {
        "embedding_model": EMBEDDING_MODEL,
        "loader_name": LOADER_NAME,
        "source_file": file_path.name,
        "last_indexed": datetime.now(timezone.utc).isoformat(),
    }
    manifest.update(LOADER_PARAMS)
    with open(f"{dest_dir}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
        print(f"Saved FAISS index to {ART_DIR}")


def _check_for_vs(file_name):

    for vs_path in Path(ART_DIR).glob("*"):
        if vs_path.stem == file_name:
            index_faiss_path = vs_path / "index.faiss"
            index_pkl_path = vs_path / "index.pkl"
            manifest_path = vs_path / "manifest.json"
            return all(
                p.exists() for p in [index_faiss_path, index_pkl_path, manifest_path]
            )
    return False


def _merge_vector_stores():
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    vector_stores = []
    file_names = []

    for index_path in Path(ART_DIR).glob("*/"):
        vector_store = FAISS.load_local(
            index_path,
            embeddings,
            allow_dangerous_deserialization=True,
        )
        vector_stores.append(vector_store)

        with open(f"{index_path}/manifest.json", "r") as f:
            manifest = json.load(f)
        file_names.append(manifest["source_file"])

    main_vs = vector_stores[0]
    for vs in vector_stores[1:]:
        main_vs.merge_from(vs)
    main_vs.save_local(ART_DIR)

    manifest = {
        "embedding_model": EMBEDDING_MODEL,
        "vector_store": VECTOR_STORE,
        "loader_name": LOADER_NAME,
        "source_files": file_names,
        "last_indexed": datetime.now(timezone.utc).isoformat(),
    }
    manifest.update(LOADER_PARAMS)
    with open(Path(ART_DIR) / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)


def update_pdf_vector_stores():

    added_vs = False

    for file_path in Path(PDF_DIR).glob("*.pdf"):
        pdf_name = file_path.stem
        has_index = _check_for_vs(pdf_name)
        if not has_index:
            ingest(file_path)
            print(f"Added document: {pdf_name}")
            added_vs = True

    if added_vs:
        _merge_vector_stores()
        print("Merged existing vector stores.")
    else:
        print("No new documents to add.")


update_pdf_vector_stores()
