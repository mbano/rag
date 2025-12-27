from pydantic import BaseModel
from fastapi import APIRouter, Request, Depends
from app.security.dependencies import get_current_principal, require_group
from app.security.principal import Principal


router = APIRouter(tags=["rag"])


class QueryRequest(BaseModel):
    question: str


@router.post("/ask")
async def ask_question(
    req: QueryRequest,
    request: Request,
    principal: Principal = Depends(get_current_principal),
    _authz=Depends(require_group("demo_user")),
):
    graph = request.app.state.graph
    result = graph.invoke({"question": req.question})
    return result
