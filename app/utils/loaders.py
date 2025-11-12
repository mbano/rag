from typing import Callable
from langchain_unstructured import UnstructuredLoader

LoaderBuilder = Callable[..., object]

LOADER_REGISTRY: dict[str, dict[str, LoaderBuilder]] = {
    "unstructured": {
        "pdf": lambda path, **kw: UnstructuredLoader(file_path=path, **kw),
        "web": lambda path, **kw: UnstructuredLoader(web_url=path, **kw),
    }
}
