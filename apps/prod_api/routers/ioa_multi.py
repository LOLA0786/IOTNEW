from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from apps.prod_api.routers.ioa import run_pipeline, RunRequest

router = APIRouter()

class MultiRunRequest(BaseModel):
    symbols: List[str]
    session_id: str | None = None

@router.post("/run-multi")
def run_multi(req: MultiRunRequest):
    results = []

    for symbol in req.symbols:
        single = run_pipeline(
            RunRequest(
                symbol=symbol,
                session_id=req.session_id
            )
        )
        results.append(single)

    return {
        "status": "ok",
        "results": results,
        "count": len(results)
    }
