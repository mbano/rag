from langchain_unstructured import UnstructuredLoader
from pathlib import Path
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from dotenv import load_dotenv
import json
import os
from app.config import EMBEDDING_MODEL, VECTOR_STORE, LOADER_NAME, LOADER_PARAMS
from datetime import datetime, timezone
from app.utils.urls import url_to_resource_name
from app.utils.docs import clean_pdf_doc, filter_web_docs, clean_web_doc

# local fallback
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "pdf"
ART_DIR = BASE_DIR / "artifacts"
VS_DIR = ART_DIR / VECTOR_STORE
DOC_DIR = ART_DIR / "documents"


def ingest(file_path, mode: str):

    #  TODO: make mode enum or pydantic class

    if mode == "pdf":
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

        _save_docs(clean_docs, doc_dest_dir)

        manifest = {
            "embedding_model": EMBEDDING_MODEL,
            "loader_name": LOADER_NAME,
            "source_file": file_path.name,
            "last_indexed": datetime.now(timezone.utc).isoformat(),
        }
        manifest.update(LOADER_PARAMS["pdf"])

    if mode == "web":
        url = file_path
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

        _save_docs(clean_docs, doc_dest_dir)

        manifest = {
            "embedding_model": EMBEDDING_MODEL,
            "loader_name": LOADER_NAME,
            "source_url": file_path,
            "last_indexed": datetime.now(timezone.utc).isoformat(),
        }

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    vector_store = FAISS.from_documents(clean_docs, embeddings)
    vector_store.save_local(art_dest_dir)

    with open(f"{art_dest_dir}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
        print(f"Saved FAISS index to {VS_DIR}")


def _save_docs(documents: list[Document], path: str | None = None):

    path = DOC_DIR if not path else path
    filename = f"{path}/documents.jsonl"
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, "w", encoding="utf-8") as f:
        for doc in documents:
            json.dump({"page_content": doc.page_content, "metadata": doc.metadata}, f)
            f.write("\n")


def _check_for_vs(file_name):

    for vs_path in Path(VS_DIR).glob("*"):
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

    for vs_path in Path(VS_DIR).glob("*/"):
        vector_store = FAISS.load_local(
            vs_path,
            embeddings,
            allow_dangerous_deserialization=True,
        )
        vector_stores.append(vector_store)

        with open(vs_path / "manifest.json", "r") as f:
            manifest = json.load(f)
            source = manifest.get("source_file")
            source = manifest.get("source_url") if not source else source
            file_names.append(source)

    main_vs = vector_stores[0]
    for vs in vector_stores[1:]:
        main_vs.merge_from(vs)
    main_vs.save_local(VS_DIR)

    manifest = {
        "embedding_model": EMBEDDING_MODEL,
        "vector_store": VECTOR_STORE,
        "loader_name": LOADER_NAME,
        "source_files": file_names,
        "last_indexed": datetime.now(timezone.utc).isoformat(),
    }
    manifest.update(LOADER_PARAMS)
    with open(Path(VS_DIR) / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)


def update_vector_stores():

    added_vs = False
    data_subdirs = [path for path in Path(DATA_DIR).iterdir() if path.is_dir()]

    for dir in data_subdirs:
        if dir.stem == "pdf":
            for file_path in dir.iterdir():
                pdf_name = file_path.stem
                has_vs = _check_for_vs(pdf_name)
                if not has_vs:
                    ingest(file_path, "pdf")
                    added_vs = True
        if dir.stem == "web":
            # get each url and transform to resource name
            with open(dir / "urls.json", "r") as f:
                urls = json.load(f)["urls"]
            resource_names = [url_to_resource_name(url) for url in urls]
            for url, resource_name in zip(urls, resource_names):
                has_vs = _check_for_vs(resource_name)
                if not has_vs:
                    ingest(url, "web")
                    added_vs = True

    if added_vs:
        _merge_vector_stores()
        print("Merged existing vector stores.")
    else:
        print("No new documents to add.")


update_vector_stores()
