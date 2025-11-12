from typing import Callable
from langchain_community.vectorstores import FAISS

VectorStoreBuilder = Callable[..., object]

VS_REGISTRY: dict[str, dict[str, VectorStoreBuilder]] = {
    "faiss": {
        "create": lambda docs, embeddings, path: FAISS.from_documents(
            docs, embeddings
        ).save_local(path),
        "load": lambda path, embeddings, **kw: FAISS.load_local(path, embeddings, **kw),
    },
}
