from langsmith import Client
from langsmith.utils import LangSmithError
from app.rag_pipeline import build_graph
from app.config import load_config
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone
import json
from langchain.smith import RunEvalConfig, run_on_dataset
from ragas.integrations.langchain import EvaluatorChain
from ragas.metrics import (
    AnswerCorrectness,
    AnswerRelevancy,
    Faithfulness,
    ResponseGroundedness,
    LLMContextPrecisionWithoutReference,
)

load_dotenv()
LANGSMITH_PROJECT = "rag_learning_ragas"
EVAL_DIR = Path(__file__).resolve().parent

metrics = [
    AnswerCorrectness(),
    AnswerRelevancy(),
    Faithfulness(),
    LLMContextPrecisionWithoutReference(),
    ResponseGroundedness(),
    LLMContextPrecisionWithoutReference(),
]

client = Client()
dataset_name = "Sustainability dataset v1"
dataset_filename = "dataset_2025-11-09_20-51-15.jsonl"
dataset_manifest_filename = "manifest_2025-11-09_20-51-15.json"
with open(EVAL_DIR / "datasets" / dataset_manifest_filename, "r") as f:
    ds_manifest = json.load(f)
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

dataset = []
with open(EVAL_DIR / "datasets" / dataset_filename, "r") as f:
    for line in f:
        dataset.append(json.loads(line))

try:
    ls_dataset = client.read_dataset(dataset_name=dataset_name)
    print("using existing dataset: ", dataset_name)
except LangSmithError:
    ls_dataset = client.create_dataset(
        dataset_name=dataset_name, description="sustainability test dataset"
    )
    for sample in dataset:
        client.create_example(
            inputs={"question": sample["question"]},
            outputs={"ground_truth": sample["ground_truth"]},
            dataset_id=ls_dataset.id,
        )
    print("Created a new dataset: ", ls_dataset.name)

eval_chains = [EvaluatorChain(metric=m) for m in metrics]

evaluation_config = RunEvalConfig(
    custom_evaluators=eval_chains,
    prediction_key="response",
)

graph_cfg = load_config()

result = run_on_dataset(
    client,
    dataset_name,
    build_graph(graph_cfg, eval_mode=True),
    evaluation=evaluation_config,
    project_metadata=ds_manifest,
    concurrency_level=1,  #  prevent rate-limiting from Cohere
)

manifest = {
    "langsmith_dataset_name": dataset_name,
    "evaluated_at": str(datetime.now(timezone.utc)),
    "eval_script": Path(__file__).resolve().name,
}
manifest.update(ds_manifest)

with open(EVAL_DIR / "runs" / f"manifest_{timestamp}", "w") as f:
    json.dump(manifest, f)
