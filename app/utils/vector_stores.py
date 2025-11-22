from typing import Callable
from langchain_community.vectorstores import FAISS, OpenSearchVectorSearch
from app.config import VectorStoreConfig
from app.utils.opensearch import get_opensearch_langchain_kwargs
import os

VectorStoreBuilder = Callable[..., object]


def _load_opensearch(path, embeddings, **kw):
    base_kw = {"opensearch_url": os.getenv("OPENSEARCH_COLLECTION_ENDPOINT")}
    merged_kw = {**base_kw, **kw}
    return OpenSearchVectorSearch.load(path, embeddings, **merged_kw)


def _create_opensearch(docs, embeddings, cfg: VectorStoreConfig):

    connection_kwargs = get_opensearch_langchain_kwargs()

    vector_store = OpenSearchVectorSearch.from_documents(
        docs,
        embeddings,
        opensearch_url=os.getenv("OPENSEARCH_COLLECTION_ENDPOINT"),
        index_name=cfg.kwargs["index_name"],
        vector_field=cfg.kwargs["vector_field"],
        text_field=cfg.kwargs["text_field"],
        engine=cfg.kwargs["engine"],
        space_type=cfg.kwargs["space_type"],
        ef_construction=cfg.kwargs["ef_construction"],
        m=cfg.kwargs["m"],
        bulk_size=6000,
        **connection_kwargs,
    )

    return vector_store


VS_REGISTRY: dict[str, dict[str, VectorStoreBuilder]] = {
    "faiss": {
        "create": lambda docs, embeddings, path: FAISS.from_documents(
            docs, embeddings
        ).save_local(path),
        "load": lambda path, embeddings, **kw: FAISS.load_local(path, embeddings, **kw),
    },
    "opensearch": {
        "create": _create_opensearch,
        "load": _load_opensearch,
    },
}
