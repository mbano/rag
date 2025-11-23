from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from app.rag_pipeline import build_graph
from app.config import get_settings, RagConfig
from app.utils.artifacts import ensure_corpus_assets
from dotenv import load_dotenv
import os

load_dotenv()


class QueryRequest(BaseModel):
    question: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg: RagConfig = get_settings().rag
    vs_key = cfg.nodes.retrieve.dense_vector_store_key
    vs_dir, doc_dir = ensure_corpus_assets(
        config=cfg.vector_stores[vs_key],
        repo_id=os.getenv("HF_DATASET_REPO"),
        revision=os.getenv("HF_DATASET_REVISION", "main"),
        want_sources=True,
    )
    index_name = cfg.vector_stores[vs_key].kwargs.get("index_name", "rag-index")
    graph = build_graph(
        cfg,
        vs_dir=vs_dir,
        doc_dir=doc_dir,
        index_name=index_name,
    )
    app.state.graph = graph
    yield


app = FastAPI(title="RAG API", version="0.1", lifespan=lifespan)


@app.post("/ask")
async def ask_question(req: QueryRequest):
    graph = app.state.graph
    result = graph.invoke({"question": req.question})
    return result


@app.get("/")
async def report_status():
    return {"message": "status OK"}
