import yaml
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field

PROJECT_ROOT = Path(__file__).resolve().parents[0]
DEFAULT_CONFIG_PATH = PROJECT_ROOT.with_name("config.yaml")

#  QA


@dataclass
class VectorStoreConfig:
    type: str
    embedding_model: str
    kwargs: dict[str, Any]


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
    vector_store: VectorStoreConfig
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
            kwargs=cfg["kwargs"],
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


#  Ingestion


@dataclass
class LoaderConfig:
    type: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class PdfSourceConfig:
    loader: LoaderConfig
    metadata: dict | None


@dataclass
class WebSourceConfig:
    loader: LoaderConfig
    metadata: dict | None


@dataclass
class SqlSourceConfig:
    loader: LoaderConfig | None
    metadata: dict | None


@dataclass
class IngestionConfig:
    vector_store: VectorStoreConfig
    pdf: PdfSourceConfig | None
    web: WebSourceConfig | None
    sql: SqlSourceConfig | None


def load_ingestion_config(path: str | Path = DEFAULT_CONFIG_PATH) -> IngestionConfig:
    path = Path(path)
    raw = yaml.safe_load(path.read_text())

    vs_key = raw["ingestion"]["vector_store"]
    vs_cfg = raw["vector_stores"][vs_key]
    vector_store = VectorStoreConfig(
        type=vs_cfg["type"],
        embedding_model=vs_cfg["embedding_model"],
        kwargs=vs_cfg["kwargs"],
    )

    pdf_loader_cfg = raw["ingestion"]["sources"]["pdf"]["loader"]
    pdf_loader_metadata = raw["ingestion"]["sources"]["pdf"]
    pdf = PdfSourceConfig(
        loader=LoaderConfig(**pdf_loader_cfg),
        metadata=pdf_loader_metadata,
    )

    web_loader_cfg = raw["ingestion"]["sources"]["web"]["loader"]
    web_loader_metadata = raw["ingestion"]["sources"]["web"]
    web = WebSourceConfig(
        loader=LoaderConfig(**web_loader_cfg),
        metadata=web_loader_metadata,
    )

    sql_loader_cfg = raw["ingestion"]["sources"]["sql"]["loader"]
    sql_loader_metadata = raw["ingestion"]["sources"]["sql"]
    sql = WebSourceConfig(
        loader=LoaderConfig(**sql_loader_cfg),
        metadata=sql_loader_metadata,
    )

    return IngestionConfig(
        vector_store=vector_store,
        pdf=pdf,
        web=web,
        sql=sql,
    )
