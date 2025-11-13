from pathlib import Path
from datetime import datetime, timezone
import json
import os
import yaml
import time
from dotenv import load_dotenv
from app.rag_pipeline import build_graph
from app.config import load_config
from app.utils.prompts import get_chat_prompt_template

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = PROJECT_ROOT / "evaluation"
cfg = load_config()
graph = build_graph(cfg)
gen_prompt = get_chat_prompt_template(cfg.nodes.generate.prompt)

with open(EVAL_DIR / "datasets" / "eval_dataset.json", "r") as f:
    dataset = json.load(f)

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
dataset_name = f"dataset_{timestamp}"

with open(EVAL_DIR / "datasets" / f"{dataset_name}.jsonl", "w", encoding="utf-8") as f:
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
    "generation_prompt": str(gen_prompt),
}

with open(PROJECT_ROOT / "config.yaml", "r") as f:
    config = yaml.safe_load(f)

metadata.update({"parameters": config})

with open(EVAL_DIR / "datasets" / f"manifest_{timestamp}.json", "w") as f:
    json.dump(metadata, f, indent=2)
