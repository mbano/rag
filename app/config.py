import yaml
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field

PROJECT_ROOT = Path(__file__).resolve().parents[0]
DEFAULT_CONFIG_PATH = PROJECT_ROOT.with_name("config.yaml")


@dataclass
class VectorStoreConfig:
    type: str
    embedding_model: str


@dataclass
class LLMConfig:
    model_name: str
    model_provider: str


@dataclass
class AnalyzeQueryConfig:
    llm_key: str
    temperature: float = 0.0
    prompt: str | None = None


@dataclass
class GenerateConfig:
    llm_key: str
    temperature: float = 0.0
    prompt: str | None = None


@dataclass
class RetrieveConfig:
    dense_vector_store_key: str
    dense_params: dict[str, Any] = field(default_factory=dict)
    sparse_type: str = field(default_factory="none")
    sparse_params: dict[str, Any] = field(default_factory=dict)
    ensemble_weights: list[float] = field(default_factory=lambda: [0.5, 0.5])
    reranker_type: str = field(default_factory="none")
    reranker_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class NodesConfig:
    analyze_query: AnalyzeQueryConfig
    retrieve: RetrieveConfig
    generate: GenerateConfig


@dataclass
class RagConfig:
    vector_stores: dict[str, VectorStoreConfig]
    llms: dict[str, LLMConfig]
    nodes: NodesConfig


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> RagConfig:
    path = Path(path)
    raw = yaml.safe_load(path.read_text())

    vector_stores: dict[str, VectorStoreConfig] = {}
    for key, cfg in (raw.get("vector_stores") or {}).items():
        vector_stores[key] = VectorStoreConfig(
            type=cfg["type"],
            embedding_model=cfg["embedding_model"],
        )

    llms: dict[str, LLMConfig] = {}
    for key, cfg in (raw.get("llms") or {}).items():
        llms[key] = LLMConfig(
            model_name=cfg["model_name"],
            model_provider=cfg["model_provider"],
        )

    aq_raw = raw["nodes"]["analyze_query"]
    aq_llm_key = aq_raw["llm"]
    aq_params = aq_raw.get("params") or {}

    analyze_query = AnalyzeQueryConfig(
        llm_key=aq_llm_key,
        temperature=aq_params.get("temperature", 0.0),
        prompt=aq_raw.get("prompt"),
    )

    r_raw = raw["nodes"]["retrieve"]
    dense_raw = r_raw["dense"]
    sparse_raw = r_raw["sparse"]
    ensemble_raw = r_raw.get("ensemble") or {}
    reranker_raw = r_raw["reranker"]

    retrieve = RetrieveConfig(
        dense_vector_store_key=dense_raw["vector_store"],
        dense_params=dense_raw.get("params") or {},
        sparse_type=sparse_raw["type"],
        sparse_params=sparse_raw.get("params") or {},
        ensemble_weights=ensemble_raw.get("weights", [0.5, 0.5]),
        reranker_type=reranker_raw["type"],
        reranker_params=reranker_raw.get("params") or {},
    )

    g_raw = raw["nodes"]["generate"]
    gen_llm_key = g_raw["llm"]
    gen_params = g_raw.get("params") or {}

    generate = GenerateConfig(
        llm_key=gen_llm_key,
        temperature=gen_params.get("temperature", 0.0),
        prompt=g_raw.get("prompt"),
    )

    nodes = NodesConfig(
        analyze_query=analyze_query,
        retrieve=retrieve,
        generate=generate,
    )

    return RagConfig(
        vector_stores=vector_stores,
        llms=llms,
        nodes=nodes,
    )
