from fastapi import FastAPI
from pydantic import BaseModel
from app.rag_pipeline import answer_question

app = FastAPI(title="RAG API", version="0.1")


class QueryRequest(BaseModel):
    question: str


@app.post("/ask")
async def ask_question(req: QueryRequest):
    result = answer_question(req.question)
    return result
