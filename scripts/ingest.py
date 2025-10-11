from langchain_unstructured import UnstructuredLoader
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import json
import os

# local fallback
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ART_DIR = BASE_DIR / "artifacts" / "faiss" / "lancet_eat_2025"
file_path = DATA_DIR / "lancet_eat_2025.pdf"  # TODO: pull from query/other endpoint

loader = UnstructuredLoader(
    file_path=file_path,
    strategy="hi_res",
    infer_table_structure=True,
)

docs = []

for doc in loader.lazy_load():
    docs.append(doc)

# TODO: get from config
chunk_size = 1000
chunk_overlap = 100
embedding_model = "text-embedding-3-large"

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=chunk_size,
    chunk_overlap=chunk_overlap,
    length_function=len,
    separators=["\n\n", "\n", ".", "!", "?", " ", ""],
)

chunks = text_splitter.split_documents(docs)
embeddings = OpenAIEmbeddings(model=embedding_model)
vector_store = FAISS.from_documents(chunks, embeddings)
vector_store.save_local(ART_DIR)

# manifest
manifest = {
    "embedding_model": embedding_model,
    "chunk_size": chunk_size,
    "chunk_overlap": chunk_overlap,
    "source_files": [
        file_path.name,
    ],
}
with open(ART_DIR / "manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)

print(f"Saved FAISS index to {ART_DIR}")
