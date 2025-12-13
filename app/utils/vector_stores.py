from typing import Callable
from langchain_community.vectorstores import FAISS, OpenSearchVectorSearch
from app.config import VectorStoreConfig
from app.utils.opensearch import get_opensearch_langchain_kwargs
from langchain_openai import OpenAIEmbeddings
import os
import json
from enum import StrEnum
from app.utils.paths import BASE_DIR


class VectorStoreType(StrEnum):
    FAISS = "faiss"
    OPENSEARCH = "opensearch"


VectorStoreBuilder = Callable[..., object]


def _load_opensearch(cfg: VectorStoreConfig, **kwargs):
    embeddings = OpenAIEmbeddings(model=cfg.embedding_model)
    opensearch_url = os.getenv("OPENSEARCH_COLLECTION_ENDPOINT")
    index_name = cfg.kwargs["index_name"]

    connection_kwargs = get_opensearch_langchain_kwargs()
    vs_kwargs = {
        "engine": cfg.kwargs["engine"],
        **connection_kwargs,
    }
    return OpenSearchVectorSearch(
        opensearch_url=opensearch_url,
        index_name=index_name,
        embedding_function=embeddings,
        **vs_kwargs,
    )


def _create_opensearch(docs, cfg: VectorStoreConfig, **kwargs):

    embeddings = OpenAIEmbeddings(model=cfg.embedding_model)

    connection_kwargs = get_opensearch_langchain_kwargs()

    vector_store = OpenSearchVectorSearch.from_documents(
        docs,
        embeddings,
        opensearch_url=os.getenv("OPENSEARCH_COLLECTION_ENDPOINT"),
        index_name=cfg.kwargs["index_name"],
        engine=cfg.kwargs["engine"],
        space_type=cfg.kwargs["space_type"],
        ef_construction=cfg.kwargs["ef_construction"],
        m=cfg.kwargs["m"],
        bulk_size=6000,
        **connection_kwargs,
    )

    return vector_store


def _load_vector_store_from_manifest(cfg: VectorStoreConfig, VS_DIR):
    """
    Load FAISS index from disk using the manifest.json to get the embedding model.
    This keeps the embedding model in sync with the index, independent of config.
    """

    with open(VS_DIR / "manifest.json", "r") as f:
        manifest = json.load(f)
    embedding_model = manifest["embedding_model"]
    embeddings = OpenAIEmbeddings(model=embedding_model)

    if cfg.type == "faiss":
        vector_store = FAISS.load_local(
            str(VS_DIR),
            embeddings,
            allow_dangerous_deserialization=cfg.kwargs[
                "allow_dangerous_deserialization"
            ],
        )
        return vector_store
    raise ValueError(
        f"Loading vector store from manifest not supported for {cfg.type} vector store."
    )


def _load_faiss(cfg: VectorStoreConfig, **kwargs):
    """
    Load a FAISS vector store. If no path to an index is provided,
    uses the merged index at BASE_DIR / "artifacts" / "faiss".
    """

    FAISS_DIR = BASE_DIR / "artifacts" / "faiss"
    path = kwargs.get("path") or FAISS_DIR

    if (path / "manifest.json").exists():
        return _load_vector_store_from_manifest(cfg, path)
    else:
        embeddings = OpenAIEmbeddings(model=cfg.embedding_model)
    print(f"Manifest does not exist, returning default {cfg.type} vector store.")

    #  override embedding model if specified in kwargs
    if kwargs.get("embedding_model", None):
        embeddings = OpenAIEmbeddings(model=kwargs["embedding_model"])

    return FAISS.load_local(path, embeddings, **kwargs)


def _create_faiss(docs, cfg: VectorStoreConfig, **kwargs):
    """
    Create a FAISS index from a list of documents and an embedding model.
    """
    embeddings = OpenAIEmbeddings(model=cfg.embedding_model)
    vector_store = FAISS.from_documents(docs, embeddings)
    save_dir = kwargs.get("save_dir", None)
    return vector_store.save_local(save_dir)


VS_REGISTRY: dict[str, dict[str, VectorStoreBuilder]] = {
    VectorStoreType.FAISS: {
        "create": _create_faiss,
        "load": _load_faiss,
    },
    VectorStoreType.OPENSEARCH: {
        "create": _create_opensearch,
        "load": _load_opensearch,
    },
}
