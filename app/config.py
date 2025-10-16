import os
import yaml


def load_config():
    cfg_path = os.getcwd() + "/config.yaml"

    with open(cfg_path, "r") as f:
        conf = yaml.safe_load(f)

    return conf


cfg = load_config()

EMBEDDING_MODEL = cfg["embedding_model"]
VECTOR_STORE = cfg["vector_store"]
LOADER_NAME = cfg["loader_name"]
LOADER_PARAMS = cfg["loader_params"]
