from fastapi import APIRouter
from pydantic import BaseModel
from apps.prod_api.grok_client import call_grok_prompt

router = APIRouter(prefix="/reason", tags=["Reason"])

class ReasonReq(BaseModel):
    symbol: str
    price: float
    context: str | None = None

@router.post("/explain")
def explain(req: ReasonReq):
    prompt = f"Explain concisely why the model assigned sentiment for {req.symbol} at price {req.price}. Context: {req.context or ''}\\nReturn JSON {{'explanation':'short','risks':'short'}}"
    res = call_grok_prompt(prompt)
    return {"raw": res}
