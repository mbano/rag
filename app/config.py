from functools import lru_cache
import yaml
import os
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field
from dotenv import load_dotenv
from app.utils.paths import BASE_DIR

load_dotenv()
DEFAULT_CONFIG_PATH = BASE_DIR / "config.yaml"

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
    vector_stores: dict[str, VectorStoreConfig]
    llms: dict[str, LLMConfig]
    nodes: NodesConfig


def _load_rag_config(path) -> RagConfig:
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
    r_vs_key = dense_raw["vector_store"]
    vs_retrieval_kwargs = raw["vector_stores"][r_vs_key]["retrieval_kwargs"]

    r_merged_params = {
        **vs_retrieval_kwargs,
        **(r_raw.get("params") or {}),
    }

    retrieve = RetrieveConfig(
        dense_vector_store_key=dense_raw["vector_store"],
        dense_params=r_merged_params,
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
    pipeline_version: str
    vector_store: VectorStoreConfig
    pdf: PdfSourceConfig | None
    web: WebSourceConfig | None
    sql: SqlSourceConfig | None


def _load_ingestion_config(path) -> IngestionConfig:
    path = Path(path)
    raw = yaml.safe_load(path.read_text())

    pipeline_version = raw["ingestion"]["pipeline_version"]

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
        pipeline_version=pipeline_version,
        vector_store=vector_store,
        pdf=pdf,
        web=web,
        sql=sql,
    )


#  evaluation
#  TODO: add eval metrics


@dataclass
class EvalConfig:
    llm: LLMConfig
    ref_dataset: str
    eval_dataset: str
    ragas_metrics: list[str]


def _load_eval_config(path) -> IngestionConfig:
    path = Path(path)
    raw = yaml.safe_load(path.read_text())

    llm_key = raw["evaluation"]["llm"]
    llm = LLMConfig(
        model_name=raw["llms"][llm_key]["model_name"],
        model_provider=raw["llms"][llm_key]["model_provider"],
    )
    eval_raw = raw["evaluation"]
    ref_dataset = eval_raw["ref_dataset"]
    eval_dataset = eval_raw["eval_dataset"]
    ragas_metrics = eval_raw["ragas_metrics"]

    return EvalConfig(
        llm=llm,
        ref_dataset=ref_dataset,
        eval_dataset=eval_dataset,
        ragas_metrics=ragas_metrics,
    )


@dataclass
class InitConfig:
    download_index: bool


def _load_init_config(path) -> InitConfig:
    path = Path(path)
    raw = yaml.safe_load(path.read_text())

    init_raw = raw["init"]
    download_index = init_raw["download_index"]

    return InitConfig(download_index=download_index)


#  settings


@dataclass
class Settings:
    rag: RagConfig
    ingestion: IngestionConfig
    evaluation: EvalConfig
    init: InitConfig


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> Settings:
    rag = _load_rag_config(path)
    ingestion = _load_ingestion_config(path)
    evaluation = _load_eval_config(path)
    init = _load_init_config(path)

    return Settings(
        rag=rag,
        ingestion=ingestion,
        evaluation=evaluation,
        init=init,
    )


@lru_cache()
def get_settings():
    CONFIG_PATH = os.environ.get("CONFIG_PATH", DEFAULT_CONFIG_PATH)
    return load_config(CONFIG_PATH)
