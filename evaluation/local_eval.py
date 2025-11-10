# https://docs.ragas.io/en/latest/howtos/integrations/langchain/#evaluate
# https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/
# https://blog.langchain.com/evaluating-rag-pipelines-with-ragas-langsmith/
# https://langchain-tutorials.com/lessons/rag-applications/lesson-15


from ragas import EvaluationDataset
from ragas import evaluate
from ragas.metrics import (
    AnswerCorrectness,
    AnswerSimilarity,
    AnswerAccuracy,
    AnswerRelevancy,
    Faithfulness,
    FactualCorrectness,
    LLMContextRecall,
    LLMContextPrecisionWithoutReference,
    ResponseGroundedness,
)
from ragas.llms import LangchainLLMWrapper
from langchain.chat_models import init_chat_model
from app.config import EVAL_MODEL
from pathlib import Path
from datetime import datetime, timezone
import json
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EVAL_DIR = Path(__file__).resolve().parent


model = init_chat_model(EVAL_MODEL)
evaluator_llm = LangchainLLMWrapper(model, bypass_n=True)
metrics = [
    AnswerCorrectness(),
    AnswerSimilarity(),
    AnswerAccuracy(),
    AnswerRelevancy(),
    Faithfulness(),
    FactualCorrectness(),
    LLMContextRecall(),
    LLMContextPrecisionWithoutReference(),
    ResponseGroundedness(),
]

dataset_name = "pop_eval_dataset.jsonl"

dataset = []
with open(EVAL_DIR / dataset_name, "r") as f:
    for line in f:
        dataset.append(json.loads(line))

# join all retrieved contexts into single str
for sample in dataset:
    sample["retrieved_contexts"] = [ctx["text"] for ctx in sample["retrieved_contexts"]]

dataset = EvaluationDataset.from_list(dataset)

result = evaluate(
    dataset=dataset,
    metrics=metrics,
    llm=evaluator_llm,
)

result_df = result.to_pandas()
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
result_df.to_csv(EVAL_DIR / "results" / f"local_results_{timestamp}.csv")

with open(EVAL_DIR / "datasets" / dataset_name, "r") as f:
    ds_manifest = json.load(f)

manifest = {
    "dataset_name": dataset_name,
    "evaluated_at": str(datetime.now(timezone.utc)),
    "eval_script": Path(__file__).resolve().name,
}
manifest.update({"rag_conf": ds_manifest})

with open(EVAL_DIR / "results" / f"manifest_{timestamp}") as f:
    json.dump(manifest, f, indent=2)
