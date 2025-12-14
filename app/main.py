from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.rag_pipeline import build_graph
from app.config import get_settings
from app.utils.vector_stores import VectorStoreType
from app.utils.artifacts import ensure_corpus_assets
from app.utils.paths import DOC_DIR, ART_DIR
from dotenv import load_dotenv
import os


load_dotenv()


class QueryRequest(BaseModel):
    question: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = get_settings()
    rag_cfg = cfg.rag
    vs_key = rag_cfg.nodes.retrieve.dense_vector_store_key
    vs_config = rag_cfg.vector_stores[vs_key]
    vs_dir = ART_DIR / vs_config.type
    doc_dir = DOC_DIR
    if vs_config.type == VectorStoreType.FAISS:
        vs_dir, doc_dir = ensure_corpus_assets(
            config=vs_config,
            repo_id=os.getenv("HF_DATASET_REPO"),
            revision=os.getenv("HF_DATASET_REVISION", "main"),
            want_sources=True,
        )
    graph = build_graph(
        rag_cfg,
        vs_dir=vs_dir,
        doc_dir=doc_dir,
    )
    app.state.graph = graph
    yield


app = FastAPI(title="RAG API", version="0.1", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/ask")
async def ask_question(req: QueryRequest):
    graph = app.state.graph
    result = graph.invoke({"question": req.question})
    return result


@app.get("/")
async def report_status():
    return {"message": "status OK"}
