from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from app.rag_pipeline import build_graph
from app.config import settings, RagConfig


class QueryRequest(BaseModel):
    question: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg: RagConfig = settings.rag
    graph = build_graph(cfg)
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
