from typing import Any
from langsmith import Client
from langsmith.utils import LangSmithError
from app.rag_pipeline import build_graph
from app.config import get_settings, RagConfig, EvalConfig
from pathlib import Path
from dotenv import load_dotenv
import json
from langchain.smith import RunEvalConfig, run_on_dataset
from ragas.integrations.langchain import EvaluatorChain
from importlib import import_module
from app.utils.paths import DOC_DIR

from app.utils.paths import EVAL_DATASETS_DIR


load_dotenv()


def load_metrics(metric_names: list[str]) -> list[Any]:
    metrics_mod = import_module("ragas.metrics")
    metrics = []

    for name in metric_names:
        try:
            cls = getattr(metrics_mod, name)
        except AttributeError as e:
            raise ValueError(f"Unknown RAGAS metric '{name}' in config") from e
        metrics.append(cls())

    return metrics


def eval_rag_langsmith(
    rag_cfg: RagConfig,
    eval_cfg: EvalConfig,
    eval_dataset: str | Path = None,
    **kwargs,
) -> None:
    """
    Run RAGAS metrics defined in config.yaml on eval_dataset.

    If argument eval_dataset is missing, uses eval_dataset defined in config.yaml

    Use argument vs_dir=Path/to/local/vectorstore/index to use only that index to answer.
    Otherwise uses merged vectorstore defined in config.yaml (local).
    """

    metrics = load_metrics(eval_cfg.ragas_metrics)

    client = Client()
    eval_dataset = eval_dataset or eval_cfg.eval_dataset
    eval_dataset_path = EVAL_DATASETS_DIR / Path(eval_dataset).stem / eval_dataset

    dataset = []
    with eval_dataset_path.open("r") as f:
        for line in f:
            dataset.append(json.loads(line))

    try:
        ls_dataset = client.read_dataset(dataset_name=eval_dataset)
        print(f"[langsmith_eval] Using existing dataset: {eval_dataset}")
    except LangSmithError:
        ls_dataset = client.create_dataset(dataset_name=eval_dataset)
        for sample in dataset:
            client.create_example(
                inputs={"question": sample["question"]},
                outputs={"ground_truth": sample["ground_truth"]},
                dataset_id=ls_dataset.id,
            )
        print(f"[langsmith_eval] Created a new dataset: {ls_dataset.name}")

    eval_chains = [EvaluatorChain(metric=m) for m in metrics]
    ls_evaluation_config = RunEvalConfig(
        custom_evaluators=eval_chains, prediction_key="response"
    )

    run_on_dataset(
        client,
        eval_dataset,
        build_graph(
            rag_cfg,
            eval_mode=True,
            doc_dir=DOC_DIR,
            **kwargs,
        ),
        evaluation=ls_evaluation_config,
        concurrency_level=1,  #  prevent rate-limiting by Cohere
    )


def main() -> None:
    cfg = get_settings()
    rag_cfg = cfg.rag
    eval_cfg = cfg.evaluation
    eval_rag_langsmith(rag_cfg=rag_cfg, eval_cfg=eval_cfg)


if __name__ == "__main__":
    main()
