from pathlib import Path
import json


EVAL_DIR = Path(__file__).resolve().parent

dataset_name = "Sustainability dataset v1"
dataset_filename = "dataset_2025-11-09_20-51-15.jsonl"
dataset_manifest_filename = "manifest_2025-11-09_20-51-15.json"


manifest = {
    "langsmith_dataset_name": dataset_name,
    "created_at": "now",
    "eval_script": Path(__file__).resolve().name,
}

with open(EVAL_DIR / "datasets" / dataset_manifest_filename, "r") as f:
    ds_manifest = json.load(f)
manifest.update(ds_manifest)


print(ds_manifest)
print("\n\n\n")
print(manifest)
