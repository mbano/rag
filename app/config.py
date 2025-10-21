import yaml
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_config():
    cfg_path = PROJECT_ROOT / "config.yaml"
    with open(cfg_path, "r") as f:
        conf = yaml.safe_load(f)
    return conf


cfg = load_config()

EMBEDDING_MODEL = cfg["embedding_model"]
VECTOR_STORE = cfg["vector_store"]
LOADER_NAME = cfg["loader_name"]
LOADER_PARAMS = cfg["loader_params"]
RETRIEVER_PARAMS = cfg["retriever_params"]
RERANKER_PARAMS = cfg["reranker_params"]
SPARSE_RETRIEVER_PARAMS = cfg["sparse_retriever_params"]
