from langchain_core.documents import Document
from app.config import IngestionConfig, VectorStoreConfig
from app.utils.vector_stores import VectorStoreType
from app.utils.urls import url_to_resource_name
from ftfy import fix_text
from pathlib import Path
from datetime import datetime, timezone
from url_normalize import url_normalize
import json
import os
import boto3
from app.utils.paths import DOC_DIR
from typing import Any


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
            doc.metadata["doc_title"] = Path(doc.metadata["filename"]).stem
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

    for chunk_index, doc in enumerate(filtered_docs):
        doc.metadata = {k: v for k, v in doc.metadata.items() if k in keep_fields}
        doc.metadata["doc_title"] = url_to_resource_name(doc.metadata["url"])
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


def load_docs(
    config: VectorStoreConfig, filename: str | None = None, **kwargs
) -> list[Document]:
    """
    Load document object pertaining to file filename.
    If no filename is given, load all documents in /artifacts/documents

    Return a list of documents.
    """

    #  TODO: implement loading only docs from filename

    if config.type == VectorStoreType.FAISS:
        doc_dir = Path(kwargs.get("doc_dir", DOC_DIR))
        docs = []
        for dir in doc_dir.glob("*/"):
            with open(dir / "documents.jsonl", "r", encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line)
                    docs.append(Document(**data))

    elif config.type == VectorStoreType.OPENSEARCH:
        s3 = boto3.client("s3")
        bucket = os.getenv("AWS_S3_DOCS_BUCKET")
        resp = s3.get_object(Bucket=bucket, Key="documents/documents.jsonl")
        data = resp["Body"].read().decode("utf-8")
        lines = data.splitlines()
        docs = [Document(**json.loads(line)) for line in lines]

    print(f"[load_docs] number of docs loaded: {len(docs)}")
    return docs


def save_docs(
    documents: list[Document],
    manifest: dict[str, Any],
    config: VectorStoreConfig,
    **kwargs,
):
    """
    Save documents to a jsonl file and manifest to ART_DIR, or save to AWS_S3_DOCS_BUCKET
    """

    vs_type = config.type

    if vs_type == VectorStoreType.FAISS:
        path = kwargs.get("doc_save_dir", None)
        path = DOC_DIR if not path else path
        filename = f"{path}/documents.jsonl"
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, "w", encoding="utf-8") as f:
            for doc in documents:
                json.dump(
                    {"page_content": doc.page_content, "metadata": doc.metadata}, f
                )
                f.write("\n")

        path = kwargs.get("manifest_save_dir", None)
        with open(f"{path}/manifest.json", "w") as f:
            json.dump(
                manifest, f, indent=2, default=str, sort_keys=True, ensure_ascii=False
            )

    elif vs_type == VectorStoreType.OPENSEARCH:
        s3 = boto3.client("s3")
        bucket = os.getenv("AWS_S3_DOCS_BUCKET")

        try:
            resp = s3.get_object(
                Bucket="rag-app-chunkated-docs-bucket", Key="documents/documents.jsonl"
            )
            data = resp["Body"].read().decode("utf-8")
            lines = data.splitlines()
            docs_loaded = [json.loads(line) for line in lines]

        except s3.exceptions.NoSuchKey:
            docs_loaded = []

        doc_chunk_ids = set()
        for doc_dict in docs_loaded:
            doc_chunk_ids.add(doc_dict["metadata"]["chunk_id"])

        for doc in documents:
            if doc.metadata["chunk_id"] not in doc_chunk_ids:
                docs_loaded.append(
                    {"page_content": doc.page_content, "metadata": doc.metadata}
                )
                doc_chunk_ids.add(doc.metadata["chunk_id"])

        print(f"[save_docs] number of docs: {len(docs_loaded)}")

        body = "\n".join(json.dumps(doc) for doc in docs_loaded)
        s3.put_object(
            Body=body.encode("utf-8"), Bucket=bucket, Key="documents/documents.jsonl"
        )

        try:
            resp = s3.get_object(
                Bucket="rag-app-chunkated-docs-bucket", Key="manifests/manifests.json"
            )
            data = resp["Body"].read().decode("utf-8")
            manifests = json.loads(data)

        except s3.exceptions.NoSuchKey:
            manifests = {}

        filename = documents[0].metadata["doc_title"]
        pipeline_version = documents[0].metadata["pipeline_version"]
        previous_pipeline_version = manifests.get(filename, {}).get(
            "pipeline_version", None
        )
        if pipeline_version != previous_pipeline_version:
            manifests[filename] = manifest

        body = json.dumps(
            manifests, indent=2, default=str, sort_keys=True, ensure_ascii=False
        )
        s3.put_object(
            Body=body.encode("utf-8"), Bucket=bucket, Key="manifests/manifests.json"
        )
