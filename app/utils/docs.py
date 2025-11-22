from langchain_core.documents import Document
from app.config import IngestionConfig
from ftfy import fix_text
from pathlib import Path
from datetime import datetime, timezone
from url_normalize import url_normalize
import json
import os


BASE_DIR = Path(__file__).resolve().parents[2]
DOC_DIR = BASE_DIR / "artifacts" / "documents"


#  TODO: add min chunk length filtering


def process_pdf_docs(docs: list[Document], config: IngestionConfig):
    """
    Process a list of pdf documents:
    Clean text, remove unneeded metadata, add extra metadata for RAG
    """
    processed_docs = []
    keep_fields = [
        "source",
        "filetype",
        "languages",
        "last_modified",
        "filename",
        "page_number",
    ]

    for chunk_index, doc in enumerate(docs):
        #  TODO:
        # filter by categories
        ## TableChunk -> keep text_as_html, is_continuation -> make into df
        ### if is_continuation missing
        #### get next doc with TableChunk
        ##### if has is_continuation
        ###### make into df, append to above
        #### save as csv -> embed -> profit
        if doc.metadata["category"] == "CompositeElement":
            doc.metadata = {k: v for k, v in doc.metadata.items() if k in keep_fields}
            doc.metadata["doc_title"] = doc.metadata["filename"]
            doc.metadata["doc_id"] = doc.metadata["filename"]
            doc.metadata["chunk_id"] = f"{doc.metadata['doc_id']}::{chunk_index}"
            doc.metadata["chunk_index"] = chunk_index
            doc.metadata["tags"] = []
            doc.metadata["ingested_at"] = datetime.now(timezone.utc).isoformat()
            doc.metadata["tenant_id"] = "default"
            doc.metadata["pipeline_version"] = config.pipeline_version
            doc.page_content = _clean_text(doc.page_content)
            processed_docs.append(doc)

    return processed_docs


def _clean_text(text: str):
    """
    Clean a string
    """
    clean_text = fix_text(text)
    return clean_text


def process_web_docs(docs: list[Document], config: IngestionConfig):
    """
    Process a list of web documents:
    Clean text, remove unneeded metadata, add extra metadata for RAG
    """
    #  TODO:  keep category "image_url", use for enrichment
    keep_categories = ["NarrativeText", "Title"]
    filtered_docs = [doc for doc in docs if doc.metadata["category"] in keep_categories]

    processed_docs = []
    keep_fields = [
        "filetype",
        "languages",
        "url",
    ]

    title = None
    for chunk_index, doc in enumerate(filtered_docs):
        if doc.metadata.get("category") == "Title":
            title = doc.page_content
        doc.metadata["doc_title"] = title
        doc.metadata = {k: v for k, v in doc.metadata.items() if k in keep_fields}
        doc.metadata["doc_id"] = url_normalize(doc.metadata["url"])
        doc.metadata["source"] = doc.metadata["doc_id"]
        doc.metadata["chunk_id"] = f"{doc.metadata['doc_id']}::{chunk_index}"
        doc.metadata["chunk_index"] = chunk_index
        doc.metadata["tags"] = []
        doc.metadata["ingested_at"] = datetime.now(timezone.utc).isoformat()
        doc.metadata["tenant_id"] = "default"
        doc.metadata["pipeline_version"] = config.pipeline_version
        doc.page_content = _clean_text(doc.page_content)
        processed_docs.append(doc)

    return processed_docs


def load_docs(doc_dir: Path = DOC_DIR, filename: str | None = None):
    """
    Load document object pertaining to file filename.
    If no filename is given, load all documents in /artifacts/documents

    Return a list of documents.
    """

    #  TODO: implement loading only docs from filename

    docs = []
    for dir in doc_dir.glob("*/"):
        with open(dir / "documents.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                docs.append(Document(**data))
    return docs


def save_docs(documents: list[Document], path: str | None = None):
    """
    Save documents to a jsonl file
    """

    path = DOC_DIR if not path else path
    filename = f"{path}/documents.jsonl"
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, "w", encoding="utf-8") as f:
        for doc in documents:
            json.dump({"page_content": doc.page_content, "metadata": doc.metadata}, f)
            f.write("\n")
