from fastapi import APIRouter


router = APIRouter(tags=["health"])


@router.get("/")
async def report_status():
    return {"message": "status OK"}
