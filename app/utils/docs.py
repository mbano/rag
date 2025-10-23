from langchain_core.documents import Document
from ftfy import fix_text
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parents[2]
DOC_DIR = BASE_DIR / "artifacts" / "documents"


#  TODO: add min chunk length filtering


def clean_pdf_doc(doc: Document):
    """
    Remove metadata fields useless for RAG
    remove special characters from text

    Assumes loader is UnstructuredLoader #  TODO: verify if categories depend on loader
    """
    # filter by categories
    ## TableChunk -> keep text_as_html, is_continuation -> make into df
    ### if is_continuation missing
    #### get next doc with TableChunk
    ##### if has is_continuation
    ###### make into df, append to above
    #### save as csv -> embed -> profit
    clean_doc = Document(page_content="")
    if doc.metadata["category"] == "CompositeElement":
        keep_fields = [
            "filename",
            "page_number",
        ]
        clean_doc.metadata = {k: v for k, v in doc.metadata.items() if k in keep_fields}
        clean_doc.page_content = _clean_text(doc.page_content)

    # if doc.metadata["category"] == "TableChunk":
    #     keep_fields = ["filename", "page_number", "text_as_html"]
    #     clean_doc.metadata = {k: v for k, v in doc.metadata.items() if k in keep_fields}
    #     clean_doc.page_content = None
    #     # pass to table -> csv function

    return clean_doc


def _clean_text(text: str):
    """
    Clean a string
    """
    clean_text = fix_text(text)
    return clean_text


def filter_web_docs(docs: list[Document]):
    """
    Keep only document with selected categories
    """
    #  TODO: add image category -> get text description -> enrich vs
    ##  stretch: make image available to user
    keep_categories = ["NarrativeText"]

    filtered_docs = [doc for doc in docs if doc.metadata["category"] in keep_categories]

    return filtered_docs


def clean_web_doc(doc: Document):
    """
    Remove metadata fields unneeded for RAG
    """
    clean_doc = Document(page_content="")
    keep_fields = ["url"]
    clean_doc.metadata = {k: v for k, v in doc.metadata.items() if k in keep_fields}
    clean_doc.page_content = _clean_text(doc.page_content)

    return clean_doc


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
