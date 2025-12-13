from pathlib import Path
from datetime import datetime, timezone
import json
import yaml
import time
from dotenv import load_dotenv
from app.rag_pipeline import build_graph
from app.config import RagConfig, EvalConfig, get_settings
from app.utils.paths import BASE_DIR, EVAL_DATASETS_DIR, REF_DATASETS_DIR, DOC_DIR


load_dotenv()


def populate_dataset(
    rag_cfg: RagConfig,
    eval_cfg: EvalConfig,
    **kwargs,
) -> None:
    """
    Call RAG pipeline to populate a reference dataset with answers and contexts,
    and create a populated dataset file for use in evaluation.

    Use argument ref_dataset='dataset_name.json' to populate dataset_name.json.
    Otherwise populates the ref_dataset defined in config.yaml.

    Use argument vs_dir=Path/to/local/vectorstore/index to use only that index to answer.
    Otherwise uses merged vectorstore defined in config.yaml (local).
    """

    ref_dataset_name = kwargs.get("ref_dataset", None) or eval_cfg.ref_dataset
    ref_dataset_path = REF_DATASETS_DIR / ref_dataset_name
    ref_dataset_name = Path(ref_dataset_name).stem

    graph = build_graph(
        rag_cfg,
        eval_mode=True,
        doc_dir=DOC_DIR,
        **kwargs,
    )

    with open(ref_dataset_path, "r") as f:
        dataset = json.load(f)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    dataset_name = eval_cfg.eval_dataset
    if dataset_name == "none":
        dataset_name = f"{ref_dataset_name}_{timestamp}"
    dataset_dir = EVAL_DATASETS_DIR / dataset_name
    dataset_dir.mkdir(parents=True, exist_ok=True)

    with open(dataset_dir / f"{dataset_name}.jsonl", "w", encoding="utf-8") as f:
        for sample in dataset:
            question = sample["question"]
            response = graph.invoke({"question": question})
            time.sleep(8)  #  rate-limited to 10 API calls/min to Cohere reranker
            sample["contexts"] = [doc.page_content for doc in response["contexts"]]
            sample["answer"] = response["answer"]
            json.dump(sample, f)
            f.write("\n")

    metadata = {
        "dataset_name": dataset_name,
        "created_at": str(datetime.now(timezone.utc)),
        "generator_script": Path(__file__).resolve().name,
    }

    with open(BASE_DIR / "config.yaml", "r") as f:
        config = yaml.safe_load(f)

    metadata.update({"parameters": config})

    with open(dataset_dir / f"manifest_{timestamp}.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"[populate_dataset] Wrote populated dataset {dataset_name} to {dataset_dir}")


def main() -> None:
    cfg = get_settings()
    rag_cfg = cfg.rag
    eval_cfg = cfg.evaluation
    populate_dataset(rag_cfg=rag_cfg, eval_cfg=eval_cfg)


if __name__ == "__main__":
    main()
